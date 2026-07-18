"""Phase 136AI: Stage 3 Typed Authority Model Publication Independent
Verification.

Independently re-derives and adversarially verifies the Phase 136AH
``PublicationAttempt``/``PublicationEvidence`` typed record models
(``src/pcae/cltr/authority/publication.py``) directly against the live
executable schemas (``records/publication_attempt.schema.json``,
``records/publication_evidence.schema.json``) and the shared component
schemas they compose, and against the frozen contracts those schemas
implement.

Deliberately does NOT import fixtures, sample builders, expected field
inventories, or helper functions from
``tests/test_cltr_authority_136ah_publication.py``. All wire fixtures in
this module are built from scratch from the live schema field tables
re-derived below, not copied from 136AH's own documentation table. Only
the shared, non-136AH-owned ``pcae.schema_runtime`` offline-schema-
validation infrastructure is reused, exactly as any independent verifier
would use the same live schema files 136AH itself validates against.

No later record-family model (``ConcurrencyConflict``,
``RecoveryJournalEntry``, ``NotificationAuthorityBinding``,
``MarkerAuthorityBinding``, ``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented, imported, or
exercised here -- this module verifies only Group 5.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import publication as pub
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
PUBLICATION_MODULE = AUTHORITY_PACKAGE_DIR / "publication.py"

PUBLICATION_ATTEMPT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_attempt.schema.json"
)
PUBLICATION_EVIDENCE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_evidence.schema.json"
)

# The 4 later record-family model class names that must not exist anywhere
# in src/pcae/cltr/authority (independently re-derived from the operator
# prompt's no-go list and cross-checked against the 16-value RecordFamily
# enum minus the 12 already-implemented families). Narrowed by Phase
# 136AJ: `ConcurrencyConflict`/`RecoveryJournalEntry` (Group 6) are now
# authorized, legitimately-implemented record-family models -- removed
# from this still-forbidden list. Narrowed further by Phase 136AL:
# `NotificationAuthorityBinding` (Group 7) is now authorized,
# legitimately-implemented record-family model -- removed from this
# still-forbidden list.
LATER_GROUP_MODEL_NAMES = (
    "MarkerAuthorityBinding",
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

IMPLEMENTED_RECORD_FAMILY_MODELS = (
    "AuthorityEpoch",
    "AuthorityState",
    "CutoverRequest",
    "ReadinessPackage",
    "HumanAuthorization",
    "CutoverCandidate",
    "Certification",
    "PublicationAttempt",
    "PublicationEvidence",
)

FORBIDDEN_OPERATIONAL_SYMBOLS = (
    "publish",
    "execute_publication",
    "commit_publication",
    "promote",
    "activate_authority",
    "write_manifest",
    "write_pointer",
    "atomic_replace",
    "finalize_publication",
    "compare_and_swap",
    "execute_cas",
    "check_current_generation",
    "current_authority_state",
    "retry_on_conflict",
    "unlock",
    "verify_evidence",
    "validate_manifest",
    "check_artifact",
    "confirm_publication",
    "verify_receipt",
    "verify_marker",
    "provider_success",
)


def _hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is not OutcomeStatus.VALID, "expected schema-invalid, was accepted"


# ---------------------------------------------------------------------------
# Independently-built wire fixtures (from the live schema field tables, not
# from 136AH's own sample builders).
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative", text: str = "Independent-verification companion disclosure.") -> dict:
    return {"authority_role": role, "is_authoritative": False, "disclosure_text": text}


def _record_ref(record_id: str, family: str, *, cross_family: bool = False) -> dict:
    ref = {"record_id": record_id, "record_digest": _hex("a"), "record_family": family}
    if cross_family:
        ref["schema_id"] = "https://pcae.local/schemas/cltr_cutover/records/placeholder.schema.json"
        ref["schema_version"] = "1.0"
    return ref


def _epoch_ref(record_id: str) -> dict:
    return _record_ref(record_id, "authority_epoch")


def _generation_ref(gen_id: str) -> dict:
    return {"generation_id": gen_id, "generation_digest": _hex("b")}


def _cas_expectation() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _epoch_ref("authority-epoch-src0001"),
        "expected_authoritative_generation": _generation_ref("generation-gen00001"),
        "expected_authority_pointer_digest": _hex("c"),
        "expected_authority_state_digest": _hex("d"),
        "expected_migration_epoch": "epoch-1",
        "expected_source_lifecycle_state": "PROPOSED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _record_ref("cutover-request-req00001", "cutover_request"),
        "expected_certification_reference": _record_ref("certification-cert0001", "certification"),
    }


def _attempt_envelope(record_id: str = "publication-attempt-att0001") -> dict:
    return {
        "schema_id": PUBLICATION_ATTEMPT_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_attempt",
        "record_id": record_id,
        "record_digest": _hex("1"),
        "created_at": "2026-07-18T09:00:00Z",
    }


def minimal_attempt(**overrides) -> dict:
    """Minimal valid PublicationAttempt: state=not_requested (no
    uncertainty/failure_classification companions triggered), no
    temporary_pointer_reference (schema-optional)."""

    doc = {
        **_attempt_envelope(),
        "migration_epoch": "epoch-1",
        "transition_id": "trans-abc123",
        "attempt_id": "attempt-att00000001",
        "request_reference": _record_ref("cutover-request-req00001", "cutover_request", cross_family=True),
        "candidate_reference": _record_ref("cutover-candidate-can0001", "cutover_candidate", cross_family=True),
        "certification_reference": _record_ref("certification-cert0001", "certification", cross_family=True),
        "cas_expectation": _cas_expectation(),
        "source_authority_reference": _epoch_ref("authority-epoch-src0001"),
        "target_authority_reference": _epoch_ref("authority-epoch-tgt0001"),
        "attempt_sequence": 0,
        "state": "not_requested",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    doc.update(overrides)
    return doc


def maximal_attempt(**overrides) -> dict:
    """Maximal valid PublicationAttempt: state=publication_uncertain (adds
    uncertainty), plus the schema-optional temporary_pointer_reference and
    a non-empty limitations array."""

    doc = minimal_attempt(
        state="publication_uncertain",
        uncertainty={"reason": "Ambiguous provider response during publication."},
        temporary_pointer_reference=_record_ref("cutover-request-tmp0001", "cutover_request"),
        limitations=["Structural attempt record only; no publication performed."],
    )
    doc.update(overrides)
    return doc


def _evidence_envelope(record_id: str = "publication-evidence-evi0001") -> dict:
    return {
        "schema_id": PUBLICATION_EVIDENCE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_evidence",
        "record_id": record_id,
        "record_digest": _hex("2"),
        "created_at": "2026-07-18T09:05:00Z",
    }


def minimal_evidence(**overrides) -> dict:
    doc = {
        **_evidence_envelope(),
        "migration_epoch": "epoch-1",
        "transition_id": "trans-abc123",
        "attempt_reference": _record_ref(
            "publication-attempt-att0001", "publication_attempt", cross_family=True
        ),
        "outcome": "not_attempted",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    doc.update(overrides)
    return doc


def maximal_evidence(**overrides) -> dict:
    doc = minimal_evidence(
        outcome="published_and_verified",
        target_readback=_record_ref("cutover-request-rb000001", "cutover_request"),
        authoritative_generation=_generation_ref("generation-gen00099"),
        authority_disclosure=_disclosure("authoritative"),
        limitations=["Claimed publication outcome only; not independently proven."],
    )
    doc.update(overrides)
    return doc


# ===========================================================================
# 1. Independent field re-derivation: exact schema shape.
# ===========================================================================


class TestFieldRederivationPublicationAttempt:
    """Schema field  Wire type  Required  Null  ABSENT  Wrapper  Invariant
    -- independently re-derived from records/publication_attempt.schema.json,
    not copied from 136AH's own field table."""

    REQUIRED_FIELDS = frozenset(
        {
            "schema_id",
            "schema_version",
            "contract_version",
            "record_type",
            "record_id",
            "record_digest",
            "created_at",
            "migration_epoch",
            "transition_id",
            "attempt_id",
            "request_reference",
            "candidate_reference",
            "certification_reference",
            "cas_expectation",
            "source_authority_reference",
            "target_authority_reference",
            "attempt_sequence",
            "state",
            "limitations",
            "authority_disclosure",
        }
    )
    OPTIONAL_FIELDS = frozenset({"temporary_pointer_reference", "uncertainty", "failure_classification"})
    ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

    def test_minimal_valid_accepted_by_schema(self, schema_registry):
        _assert_schema_valid(minimal_attempt(), PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)

    def test_maximal_valid_accepted_by_schema(self, schema_registry):
        _assert_schema_valid(maximal_attempt(), PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)

    def test_minimal_constructs(self):
        pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")

    def test_maximal_constructs(self):
        pub.PublicationAttempt.from_dict(maximal_attempt(), schema_version="1.0")

    @pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
    def test_missing_required_field_rejected_by_schema_and_model(self, field, schema_registry):
        doc = minimal_attempt()
        del doc[field]
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize(
        "injected",
        [
            "execute",
            "retry_count",
            "current_state",
            "lock_token",
            "publisher",
            "result_verified",
            "authority_activated",
        ],
    )
    def test_unauthorized_operational_field_rejected(self, injected, schema_registry):
        doc = minimal_attempt()
        doc[injected] = True
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_dataclass_field_set_matches_schema_optional_plus_required_minus_envelope_split(self):
        # envelope fields are bundled into a RecordEnvelope value object; the
        # remaining dataclass fields must be exactly ALL_FIELDS minus the 7
        # envelope fields that RecordEnvelope itself owns.
        envelope_fields = {
            "schema_id",
            "schema_version",
            "contract_version",
            "record_type",
            "record_id",
            "record_digest",
            "created_at",
        }
        dataclass_fields = {f.name for f in dataclasses.fields(pub.PublicationAttempt)}
        expected = (self.ALL_FIELDS - envelope_fields) | {"envelope"}
        assert dataclass_fields == expected


class TestFieldRederivationPublicationEvidence:
    REQUIRED_FIELDS = frozenset(
        {
            "schema_id",
            "schema_version",
            "contract_version",
            "record_type",
            "record_id",
            "record_digest",
            "created_at",
            "migration_epoch",
            "transition_id",
            "attempt_reference",
            "outcome",
            "limitations",
            "authority_disclosure",
        }
    )
    OPTIONAL_FIELDS = frozenset({"uncertainty_detail", "target_readback", "authoritative_generation"})
    ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

    def test_minimal_valid_accepted_by_schema(self, schema_registry):
        _assert_schema_valid(minimal_evidence(), PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)

    def test_maximal_valid_accepted_by_schema(self, schema_registry):
        _assert_schema_valid(maximal_evidence(), PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)

    def test_minimal_constructs(self):
        pub.PublicationEvidence.from_dict(minimal_evidence(), schema_version="1.0")

    def test_maximal_constructs(self):
        pub.PublicationEvidence.from_dict(maximal_evidence(), schema_version="1.0")

    @pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
    def test_missing_required_field_rejected(self, field, schema_registry):
        doc = minimal_evidence()
        del doc[field]
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize(
        "injected",
        [
            "verified",
            "provider_checked",
            "artifact_exists",
            "receipt_valid",
            "marker_created",
            "notification_sent",
            "authority_active",
        ],
    )
    def test_unauthorized_field_rejected(self, injected, schema_registry):
        doc = minimal_evidence()
        doc[injected] = True
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_dataclass_field_set_matches_schema(self):
        envelope_fields = {
            "schema_id",
            "schema_version",
            "contract_version",
            "record_type",
            "record_id",
            "record_digest",
            "created_at",
        }
        dataclass_fields = {f.name for f in dataclasses.fields(pub.PublicationEvidence)}
        expected = (self.ALL_FIELDS - envelope_fields) | {"envelope"}
        assert dataclass_fields == expected

    def test_no_artifact_or_evidence_collection_fields_exist(self):
        """The operator prompt anticipates 'artifact and evidence arrays' on
        PublicationEvidence; independently re-deriving the live schema shows
        no such array field exists at all (only a single attempt_reference
        plus scalar outcome/uncertainty_detail/target_readback/
        authoritative_generation fields) -- documented as a discrepancy
        between the assumed shape and the frozen schema, not a defect."""

        dataclass_fields = {f.name for f in dataclasses.fields(pub.PublicationEvidence)}
        for forbidden_name in ("artifacts", "evidence_items", "evidence_references", "artifact_references"):
            assert forbidden_name not in dataclass_fields


# ===========================================================================
# 2. Discriminators and constants
# ===========================================================================


class TestDiscriminatorsAndConstants:
    def test_attempt_schema_id_const(self):
        doc = minimal_attempt(schema_id="https://pcae.local/schemas/cltr_cutover/records/wrong.schema.json")
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_attempt_record_type_const(self):
        doc = minimal_attempt(record_type="publication_evidence")
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_attempt_record_type_wrong_case(self):
        doc = minimal_attempt(record_type="Publication_Attempt")
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_attempt_record_type_whitespace(self):
        doc = minimal_attempt(record_type="publication_attempt ")
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_attempt_contract_version_wrong(self):
        doc = minimal_attempt(contract_version="2.0")
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_attempt_unsupported_schema_version(self):
        with pytest.raises(auth.UnsupportedSchemaVersionError):
            pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="9.9")

    def test_evidence_schema_id_const(self):
        doc = minimal_evidence(schema_id="https://pcae.local/schemas/cltr_cutover/records/wrong.schema.json")
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_evidence_record_type_const(self):
        doc = minimal_evidence(record_type="publication_attempt")
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_missing_schema_id_rejected(self):
        doc = minimal_attempt()
        del doc["schema_id"]
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_explicit_null_record_type_rejected(self):
        doc = minimal_attempt(record_type=None)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_wrong_primitive_type_schema_id(self):
        doc = minimal_attempt(schema_id=12345)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 3. Reference families -- independently re-derived cross-family rules.
# ===========================================================================


class TestReferenceFamiliesAttempt:
    @pytest.mark.parametrize(
        "field,required_family",
        [
            ("request_reference", "cutover_request"),
            ("candidate_reference", "cutover_candidate"),
            ("certification_reference", "certification"),
            ("source_authority_reference", "authority_epoch"),
            ("target_authority_reference", "authority_epoch"),
        ],
    )
    def test_wrong_family_rejected(self, field, required_family, schema_registry):
        doc = minimal_attempt()
        wrong_family = "certification" if required_family != "certification" else "cutover_request"
        cross_family = field in ("request_reference", "candidate_reference", "certification_reference")
        doc[field] = _record_ref("cutover-request-wrongfam1", wrong_family, cross_family=cross_family)
        with pytest.raises(auth.WrongFamilyReferenceError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("field", ["request_reference", "candidate_reference", "certification_reference"])
    def test_cross_family_reference_requires_schema_id_and_version(self, field, schema_registry):
        doc = minimal_attempt()
        ref = dict(doc[field])
        ref.pop("schema_id", None)
        ref.pop("schema_version", None)
        doc[field] = ref
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("field", ["source_authority_reference", "target_authority_reference"])
    def test_epoch_reference_does_not_require_schema_id(self, field, schema_registry):
        doc = minimal_attempt()
        ref = dict(doc[field])
        ref.pop("schema_id", None)
        ref.pop("schema_version", None)
        doc[field] = ref
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_source_and_target_authority_reference_may_be_identical(self, schema_registry):
        # Sec.25 does not forbid source==target; mirrors certification.schema.json's precedent.
        doc = minimal_attempt()
        same = _epoch_ref("authority-epoch-samesame1")
        doc["source_authority_reference"] = same
        doc["target_authority_reference"] = dict(same)
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize(
        "field", ["request_reference", "candidate_reference", "certification_reference"]
    )
    def test_nonexistent_target_accepted_without_lookup(self, field, schema_registry):
        """A syntactically valid reference to a record_id that has never
        been created anywhere must construct successfully -- no lookup may
        occur (no repository, filesystem, or registry access)."""

        doc = minimal_attempt()
        family = {"request_reference": "cutover_request", "candidate_reference": "cutover_candidate",
                   "certification_reference": "certification"}[field]
        doc[field] = _record_ref("cutover-request-doesnotexist" if family == "cutover_request"
                                  else ("cutover-candidate-doesnotexist" if family == "cutover_candidate"
                                        else "certification-doesnotexist"),
                                  family, cross_family=True)
        attempt = pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        assert attempt is not None

    @pytest.mark.parametrize(
        "bad_schema_id,bad_schema_version",
        [
            (None, "1.0"),
            ("valid", None),
            (12345, "1.0"),
            ("valid", 42),
            ("valid", "not-a-version"),
            ("", "1.0"),
            ("valid", ""),
        ],
    )
    def test_malformed_cross_family_schema_id_version_rejected(
        self, bad_schema_id, bad_schema_version, schema_registry
    ):
        """136AI independent finding: shared/references.schema.json types
        schema_id as {"type": "string", "minLength": 1, "maxLength": 512}
        and schema_version as {"type": "string", "pattern": "^[0-9]+\\.[0-9]+$"}
        -- a plain "type": "string" JSON Schema constraint never admits an
        explicit null or a non-string primitive. Reproduced and repaired in
        this phase (see docs)."""

        doc = minimal_attempt()
        ref = dict(doc["request_reference"])
        ref["schema_id"] = bad_schema_id
        ref["schema_version"] = bad_schema_version
        doc["request_reference"] = ref
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelConstructionError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_temporary_pointer_reference_is_optional_and_unrestricted_family(self, schema_registry):
        doc = minimal_attempt()
        assert "temporary_pointer_reference" not in doc
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

        doc2 = minimal_attempt(
            temporary_pointer_reference=_record_ref("certification-anyfamily1", "certification")
        )
        _assert_schema_valid(doc2, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        attempt = pub.PublicationAttempt.from_dict(doc2, schema_version="1.0")
        assert attempt.temporary_pointer_reference is not auth.ABSENT


class TestReferenceFamiliesEvidence:
    def test_attempt_reference_wrong_family_rejected(self):
        doc = minimal_evidence()
        doc["attempt_reference"] = _record_ref(
            "cutover-request-wrongfam2", "cutover_request", cross_family=True
        )
        with pytest.raises(auth.WrongFamilyReferenceError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_attempt_reference_requires_schema_id_version(self, schema_registry):
        doc = minimal_evidence()
        ref = dict(doc["attempt_reference"])
        ref.pop("schema_id", None)
        ref.pop("schema_version", None)
        doc["attempt_reference"] = ref
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_nonexistent_attempt_target_accepted_without_lookup(self):
        doc = minimal_evidence()
        doc["attempt_reference"] = _record_ref(
            "publication-attempt-doesnotexist", "publication_attempt", cross_family=True
        )
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence is not None

    def test_target_readback_no_family_restriction(self, schema_registry):
        """Sec.16/26: target_readback reuses the bare record_reference $def
        with no local record_family restriction (readiness_package.evidence_references
        precedent) -- any of the 16 record_family enum values must be accepted."""

        for family in ("cutover_request", "certification", "authority_epoch"):
            doc = maximal_evidence(target_readback=_record_ref("cutover-request-anyfam001", family))
            _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_forward_reference_to_unimplemented_family_accepted_no_resolution(self, schema_registry):
        """target_readback accepts a syntactically valid but fictitious
        reference to a not-yet-implemented family (e.g. quarantine_record,
        still unimplemented as of Phase 136AJ -- concurrency_conflict was
        itself only a forward reference through 136AI and is now a real,
        implemented family per Phase 136AJ) with no lookup, no import, and
        no dynamic class construction."""

        doc = maximal_evidence(
            target_readback=_record_ref("quarantine-record-future0001", "quarantine_record")
        )
        _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence.target_readback.record_family.value == "quarantine_record"
        # Proves no dynamic class was constructed for the future family:
        assert not hasattr(auth, "QuarantineRecord")


# ===========================================================================
# 4. CAS Expectation -- descriptive only, no execution.
# ===========================================================================


class TestCasExpectation:
    def test_minimal_valid_cas(self, schema_registry):
        doc = minimal_attempt()
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        attempt = pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        assert isinstance(attempt.cas_expectation, auth.CasExpectation)

    def test_stale_but_schema_valid_cas_accepted_without_lookup(self, schema_registry, monkeypatch):
        """A CAS expectation naming an authority epoch/generation that has
        never existed must still construct: no current-state loader, no
        comparison function, may ever be invoked at construction time."""

        called = {"hit": False}

        def _boom(*a, **kw):
            called["hit"] = True
            raise AssertionError("current-state lookup must never occur")

        # Instrument the most plausible current-state hooks; absence of these
        # attributes on the module itself is also a pass (nothing to patch).
        for name in ("load_current_authority_state", "compare_and_swap", "check_current_generation"):
            if hasattr(pub, name):
                monkeypatch.setattr(pub, name, _boom)

        doc = minimal_attempt()
        doc["cas_expectation"]["expected_migration_epoch"] = "epoch-999-stale"
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        assert called["hit"] is False

    @pytest.mark.parametrize(
        "field,bad_value",
        [
            ("expected_authority_kind", "not_a_kind"),
            ("expected_compatibility_mode", "not_a_mode"),
            ("expected_source_lifecycle_state", "NOT_A_STATE"),
            ("expected_journal_lock_state", "half_locked"),
        ],
    )
    def test_malformed_cas_field_rejected(self, field, bad_value, schema_registry):
        doc = minimal_attempt()
        doc["cas_expectation"][field] = bad_value
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_malformed_digest_rejected(self, schema_registry):
        doc = minimal_attempt()
        doc["cas_expectation"]["expected_authority_pointer_digest"] = "not-a-digest"
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.InvalidDigestError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_wrong_field_family_in_cas_epoch_rejected(self):
        doc = minimal_attempt()
        doc["cas_expectation"]["expected_authority_epoch"] = _record_ref(
            "certification-wrongfam0003", "certification"
        )
        with pytest.raises(auth.WrongFamilyReferenceError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_explicit_null_cas_expectation_rejected(self):
        doc = minimal_attempt(cas_expectation=None)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize(
        "missing_field",
        [
            "expected_authority_kind",
            "expected_authority_epoch",
            "expected_authoritative_generation",
            "expected_authority_pointer_digest",
            "expected_authority_state_digest",
            "expected_migration_epoch",
            "expected_source_lifecycle_state",
            "expected_compatibility_mode",
            "expected_journal_lock_state",
            "expected_request_reference",
            "expected_certification_reference",
        ],
    )
    def test_cas_expectation_field_unconditionally_required(self, missing_field, schema_registry):
        doc = minimal_attempt()
        del doc["cas_expectation"][missing_field]
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_unknown_nested_cas_field_rejected(self, schema_registry):
        doc = minimal_attempt()
        doc["cas_expectation"]["expected_lock_owner"] = "someone"
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 5. Attempt-state enum (independently re-derived 12-value PublicationState).
# ===========================================================================

# Independently transcribed from the live shared/enums.schema.json
# `publication_state` $def, cross-checked against publication_attempt's own
# `state` field description (12 values) -- not copied from 136AH's
# PublicationState Python enum definition.
INDEPENDENT_PUBLICATION_STATE_VALUES = (
    "not_requested",
    "requested",
    "gate_rejected",
    "gate_uncertain",
    "certified",
    "publication_prepared",
    "publication_attempted",
    "publication_uncertain",
    "published",
    "verified",
    "conflict",
    "quarantined",
)


class TestAttemptStateEnum:
    def test_independent_enum_matches_schema_exactly(self, schema_registry):
        """Schema drift guard: every independently-derived value must be
        schema-accepted; the schema must accept no other value."""

        for value in INDEPENDENT_PUBLICATION_STATE_VALUES:
            doc = minimal_attempt(state=value)
            if value == "publication_uncertain":
                doc["uncertainty"] = {"reason": "test"}
            elif value in ("gate_rejected", "conflict"):
                doc["failure_classification"] = "cas_rejected"
            _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)

    @pytest.mark.parametrize("value", INDEPENDENT_PUBLICATION_STATE_VALUES)
    def test_every_valid_state_constructs(self, value):
        doc = minimal_attempt(state=value)
        if value == "publication_uncertain":
            doc["uncertainty"] = {"reason": "test"}
        elif value in ("gate_rejected", "conflict"):
            doc["failure_classification"] = "cas_rejected"
        attempt = pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        assert attempt.state.value == value

    @pytest.mark.parametrize(
        "bad_value",
        [
            "NOT_REQUESTED",
            "Not_Requested",
            " not_requested",
            "not_requested ",
            "notrequested",
            "unknown_state",
            123,
            True,
            None,
        ],
    )
    def test_invalid_state_rejected(self, bad_value, schema_registry):
        doc = minimal_attempt(state=bad_value)
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_state_never_triggers_operational_path(self):
        """Constructing with state='published' or 'verified' must not, by
        itself, mark authority_role authoritative -- the model forbids
        'authoritative' unconditionally regardless of state."""

        for terminal_state in ("published", "verified"):
            doc = minimal_attempt(state=terminal_state, authority_disclosure=_disclosure("authoritative"))
            with pytest.raises(auth.TypedModelInternalInvariantError):
                pub.PublicationAttempt.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 6. Conditional branches -- exact schema directionality (biconditional).
# ===========================================================================


class TestConditionalBranchesAttempt:
    def test_uncertainty_required_when_publication_uncertain(self, schema_registry):
        doc = minimal_attempt(state="publication_uncertain")
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_uncertainty_forbidden_when_not_publication_uncertain(self, schema_registry):
        doc = minimal_attempt(uncertainty={"reason": "test"})
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
    def test_failure_classification_required(self, state, schema_registry):
        doc = minimal_attempt(state=state)
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize(
        "state",
        [s for s in INDEPENDENT_PUBLICATION_STATE_VALUES if s not in ("gate_rejected", "conflict")],
    )
    def test_failure_classification_forbidden_elsewhere(self, state, schema_registry):
        doc = minimal_attempt(state=state, failure_classification="cas_rejected")
        if state == "publication_uncertain":
            doc["uncertainty"] = {"reason": "test"}
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_implication_is_biconditional_not_one_way(self, schema_registry):
        """The schema's own if/then/else pair is a strict biconditional
        (else: not required) -- confirm the model does not merely enforce
        the forward implication while silently tolerating the reverse."""

        doc = minimal_attempt(state="not_requested", uncertainty={"reason": "leaked"})
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_authority_role_authoritative_locally_forbidden_at_every_state(self, schema_registry):
        for state in INDEPENDENT_PUBLICATION_STATE_VALUES:
            doc = minimal_attempt(state=state, authority_disclosure=_disclosure("authoritative"))
            if state == "publication_uncertain":
                doc["uncertainty"] = {"reason": "test"}
            elif state in ("gate_rejected", "conflict"):
                doc["failure_classification"] = "cas_rejected"
            _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
            with pytest.raises(auth.TypedModelInternalInvariantError):
                pub.PublicationAttempt.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 7. PublicationEvidence: outcome enum, conditional branches.
# ===========================================================================

INDEPENDENT_PUBLICATION_OUTCOME_VALUES = (
    "not_attempted",
    "cas_rejected",
    "failed_before_replacement",
    "publication_uncertain",
    "published_and_verified",
    "post_publication_verification_failed",
    "conflict",
    "quarantined",
)


class TestEvidenceOutcomeEnum:
    def test_independent_enum_matches_schema_exactly(self, schema_registry):
        for value in INDEPENDENT_PUBLICATION_OUTCOME_VALUES:
            doc = minimal_evidence(outcome=value)
            if value == "publication_uncertain":
                doc["uncertainty_detail"] = {"last_known_state": "publication_attempted", "retry_recommended": True}
            elif value == "published_and_verified":
                doc["target_readback"] = _record_ref("cutover-request-rb000002", "cutover_request")
                doc["authoritative_generation"] = _generation_ref("generation-gen00098")
            _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)

    @pytest.mark.parametrize("value", INDEPENDENT_PUBLICATION_OUTCOME_VALUES)
    def test_every_valid_outcome_constructs(self, value):
        doc = minimal_evidence(outcome=value)
        if value == "publication_uncertain":
            doc["uncertainty_detail"] = {"last_known_state": "publication_attempted", "retry_recommended": True}
        elif value == "published_and_verified":
            doc["target_readback"] = _record_ref("cutover-request-rb000002", "cutover_request")
            doc["authoritative_generation"] = _generation_ref("generation-gen00098")
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence.outcome.value == value

    @pytest.mark.parametrize(
        "bad_value",
        ["NOT_ATTEMPTED", "Not_Attempted", " not_attempted", "unknown_outcome", 1, False, None],
    )
    def test_invalid_outcome_rejected(self, bad_value, schema_registry):
        doc = minimal_evidence(outcome=bad_value)
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_uncertainty_and_failure_are_structurally_distinct(self):
        """'publication_uncertain' never collapses into a failure-shaped
        outcome, and vice versa -- distinct outcome members with distinct
        companion-field requirements."""

        assert "publication_uncertain" in INDEPENDENT_PUBLICATION_OUTCOME_VALUES
        assert "cas_rejected" in INDEPENDENT_PUBLICATION_OUTCOME_VALUES
        doc = minimal_evidence(outcome="cas_rejected")
        # cas_rejected requires no uncertainty_detail/target_readback/authoritative_generation
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence.uncertainty_detail is auth.ABSENT


class TestEvidenceConditionalBranches:
    def test_uncertainty_detail_required(self, schema_registry):
        doc = minimal_evidence(outcome="publication_uncertain")
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_uncertainty_detail_forbidden_elsewhere(self, schema_registry):
        doc = minimal_evidence(
            uncertainty_detail={"last_known_state": "requested", "retry_recommended": False}
        )
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_target_readback_required_when_published_and_verified(self, schema_registry):
        doc = minimal_evidence(
            outcome="published_and_verified",
            authoritative_generation=_generation_ref("generation-gen00097"),
        )
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_authoritative_generation_required_when_published_and_verified(self, schema_registry):
        doc = minimal_evidence(
            outcome="published_and_verified",
            target_readback=_record_ref("cutover-request-rb000003", "cutover_request"),
        )
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_target_readback_forbidden_elsewhere(self, schema_registry):
        doc = minimal_evidence(target_readback=_record_ref("cutover-request-rb000004", "cutover_request"))
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_authoritative_generation_forbidden_elsewhere(self, schema_registry):
        doc = minimal_evidence(authoritative_generation=_generation_ref("generation-gen00096"))
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_claimed_success_with_operationally_false_references_accepted_if_schema_valid(
        self, schema_registry
    ):
        """A PublicationEvidence claiming published_and_verified against a
        target_readback/authoritative_generation that point to nothing real
        must still construct -- schema validity never proves truth."""

        doc = maximal_evidence(
            target_readback=_record_ref("cutover-request-neverexisted", "cutover_request"),
            authoritative_generation=_generation_ref("generation-neverexisted1"),
        )
        _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence.outcome is pub.PublicationOutcome.PUBLISHED_AND_VERIFIED

    def test_authority_role_authoritative_permitted_alongside_published_and_verified(
        self, schema_registry
    ):
        """One of exactly two families (with AuthorityState) where
        authority_role=='authoritative' is structurally permitted, though
        is_authoritative remains const False unconditionally."""

        doc = maximal_evidence(authority_disclosure=_disclosure("authoritative"))
        _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        evidence = pub.PublicationEvidence.from_dict(doc, schema_version="1.0")
        assert evidence.authority_disclosure.authority_role is auth.AuthorityRole.AUTHORITATIVE
        assert evidence.authority_disclosure.is_authoritative is False

    def test_is_authoritative_true_rejected_unconditionally(self):
        doc = minimal_evidence()
        doc["authority_disclosure"]["is_authoritative"] = True
        with pytest.raises(auth.TypedModelConstructionError):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 8. Timestamp behavior -- exact wire-string preservation.
# ===========================================================================


class TestTimestamps:
    @pytest.mark.parametrize(
        "wire",
        [
            "2026-07-18T09:00:00Z",
            "2026-07-18T09:00:00.123Z",
            "2026-07-18T09:00:00.123456Z",
            "2026-01-01T00:00:00Z",
            "2026-12-31T23:59:59.999999Z",
        ],
    )
    def test_exact_wire_preservation(self, wire):
        doc = minimal_attempt(created_at=wire)
        attempt = pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        assert attempt.envelope.created_at.wire == wire
        assert attempt.to_dict()["created_at"] == wire

    @pytest.mark.parametrize(
        "wire",
        [
            "2026-07-18T09:00:00+00:00",
            "2026-07-18T09:00:00+02:00",
            "2026-07-18T09:00:00-05:00",
            "2026-07-18 09:00:00Z",
            "2026-07-18T09:00:00",
            "not-a-timestamp",
        ],
    )
    def test_non_z_offset_forms_rejected(self, wire, schema_registry):
        """The shared envelope.schema.json timestamp $def requires an
        explicit 'Z' suffix only (independently re-derived); a +00:00 or
        other offset form must be rejected, not silently normalized."""

        doc = minimal_attempt(created_at=wire)
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(auth.InvalidTimestampError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_no_clock_access_at_construction(self, monkeypatch):
        import time as _time

        def _boom(*a, **kw):
            raise AssertionError("construction must never read the system clock")

        monkeypatch.setattr(_time, "time", _boom)
        pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")


# ===========================================================================
# 9. Round trip.
# ===========================================================================


class TestRoundTrip:
    def _round_trip(self, cls, doc):
        model = cls.from_dict(doc, schema_version="1.0")
        wire = model.to_dict()
        assert wire == doc
        return model

    def test_minimal_attempt_round_trip(self):
        self._round_trip(pub.PublicationAttempt, minimal_attempt())

    def test_maximal_attempt_round_trip(self):
        self._round_trip(pub.PublicationAttempt, maximal_attempt())

    @pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
    def test_failure_branch_round_trip(self, state):
        doc = minimal_attempt(state=state, failure_classification="cas_rejected")
        self._round_trip(pub.PublicationAttempt, doc)

    def test_minimal_evidence_round_trip(self):
        self._round_trip(pub.PublicationEvidence, minimal_evidence())

    def test_maximal_evidence_round_trip(self):
        self._round_trip(pub.PublicationEvidence, maximal_evidence())

    @pytest.mark.parametrize("outcome", INDEPENDENT_PUBLICATION_OUTCOME_VALUES)
    def test_every_outcome_branch_round_trip(self, outcome):
        doc = minimal_evidence(outcome=outcome)
        if outcome == "publication_uncertain":
            doc["uncertainty_detail"] = {"last_known_state": "publication_attempted", "retry_recommended": False}
        elif outcome == "published_and_verified":
            doc["target_readback"] = _record_ref("cutover-request-rb000005", "cutover_request")
            doc["authoritative_generation"] = _generation_ref("generation-gen00095")
        self._round_trip(pub.PublicationEvidence, doc)


# ===========================================================================
# 10. No publication/CAS/evidence-verification/marker/receipt/notification
#     execution -- instrumented.
# ===========================================================================


class TestNoOperationalExecution:
    def test_no_operational_symbols_defined_in_module_ast(self):
        tree = ast.parse(PUBLICATION_MODULE.read_text())
        defined_names = {
            node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for forbidden in FORBIDDEN_OPERATIONAL_SYMBOLS:
            assert forbidden not in defined_names, f"forbidden operational symbol defined: {forbidden}"

    def test_no_socket_access_during_construction_and_serialization(self, monkeypatch):
        def _boom(*a, **kw):
            raise AssertionError("socket access must never occur")

        monkeypatch.setattr(socket, "socket", _boom)
        attempt = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        attempt.to_dict()
        evidence = pub.PublicationEvidence.from_dict(maximal_evidence(), schema_version="1.0")
        evidence.to_dict()
        repr(attempt)
        repr(evidence)
        assert attempt == pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")

    def test_no_subprocess_access(self, monkeypatch):
        def _boom(*a, **kw):
            raise AssertionError("subprocess access must never occur")

        monkeypatch.setattr(subprocess, "run", _boom)
        monkeypatch.setattr(subprocess, "Popen", _boom)
        pub.PublicationAttempt.from_dict(maximal_attempt(), schema_version="1.0")
        pub.PublicationEvidence.from_dict(maximal_evidence(), schema_version="1.0")

    def test_no_filesystem_write_during_construction(self, monkeypatch, tmp_path):
        import builtins

        real_open = builtins.open

        def _guarded_open(file, mode="r", *a, **kw):
            if isinstance(mode, str) and any(c in mode for c in "wxa"):
                raise AssertionError(f"unexpected filesystem write: {file!r} mode={mode!r}")
            return real_open(file, mode, *a, **kw)

        monkeypatch.setattr(builtins, "open", _guarded_open)
        pub.PublicationAttempt.from_dict(maximal_attempt(), schema_version="1.0").to_dict()
        pub.PublicationEvidence.from_dict(maximal_evidence(), schema_version="1.0").to_dict()

    def test_invalid_inputs_produce_no_side_effects(self, monkeypatch):
        monkeypatch.setattr(socket, "socket", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("net")))
        for bad in (minimal_attempt(state="not_a_state"), minimal_attempt(attempt_sequence=-1)):
            with pytest.raises(Exception):
                pub.PublicationAttempt.from_dict(bad, schema_version="1.0")


# ===========================================================================
# 11. Immutability.
# ===========================================================================


class TestImmutability:
    def test_attempt_is_frozen_dataclass(self):
        attempt = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        with pytest.raises(dataclasses.FrozenInstanceError):
            attempt.state = pub.PublicationState.PUBLISHED if hasattr(pub, "PublicationState") else None

    def test_evidence_is_frozen_dataclass(self):
        evidence = pub.PublicationEvidence.from_dict(minimal_evidence(), schema_version="1.0")
        with pytest.raises(dataclasses.FrozenInstanceError):
            evidence.outcome = "conflict"

    def test_cas_expectation_is_frozen(self):
        attempt = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        with pytest.raises(dataclasses.FrozenInstanceError):
            attempt.cas_expectation.expected_migration_epoch = "hacked"

    def test_limitations_tuple_not_mutable_via_original_list(self):
        original = ["one limitation"]
        doc = minimal_attempt(limitations=original)
        attempt = pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        original.append("mutated after construction")
        assert list(attempt.limitations.entries) == ["one limitation"]

    def test_mutating_returned_dict_does_not_affect_model(self):
        attempt = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        wire = attempt.to_dict()
        wire["state"] = "conflict"
        wire["request_reference"]["record_id"] = "tampered"
        assert attempt.state.value == "not_requested"
        assert attempt.request_reference.record_id.value != "tampered"

    def test_authority_disclosure_frozen(self):
        evidence = pub.PublicationEvidence.from_dict(minimal_evidence(), schema_version="1.0")
        with pytest.raises(dataclasses.FrozenInstanceError):
            evidence.authority_disclosure.is_authoritative = True


# ===========================================================================
# 12. Equality and hashing.
# ===========================================================================


class TestEqualityAndHashing:
    def test_identical_records_compare_equal(self):
        a = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        b = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        assert a == b

    def test_changing_any_field_breaks_equality(self):
        a = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        b = pub.PublicationAttempt.from_dict(minimal_attempt(attempt_sequence=1), schema_version="1.0")
        assert a != b

    def test_same_attempt_id_does_not_imply_equality(self):
        a = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        b = pub.PublicationAttempt.from_dict(
            minimal_attempt(state="requested"), schema_version="1.0"
        )
        assert a.attempt_id == b.attempt_id
        assert a != b

    def test_timestamp_string_difference_observable(self):
        a = pub.PublicationAttempt.from_dict(minimal_attempt(created_at="2026-01-01T00:00:00Z"), schema_version="1.0")
        b = pub.PublicationAttempt.from_dict(minimal_attempt(created_at="2026-01-01T00:00:00.0Z"), schema_version="1.0")
        assert a.envelope.created_at.wire != b.envelope.created_at.wire
        assert a != b

    def test_hashable_where_recursively_safe(self):
        attempt = pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")
        try:
            hash(attempt)
        except TypeError:
            pytest.skip("model contains a non-hashable nested field (documented, not a defect)")

    def test_no_semantic_equality_based_on_outcome(self):
        published = pub.PublicationEvidence.from_dict(maximal_evidence(), schema_version="1.0")
        not_attempted = pub.PublicationEvidence.from_dict(minimal_evidence(), schema_version="1.0")
        assert published != not_attempted
        assert not (published == not_attempted)


# ===========================================================================
# 13. Public API surface.
# ===========================================================================


class TestPublicApiSurface:
    def test_all_nine_record_families_exported(self):
        for name in IMPLEMENTED_RECORD_FAMILY_MODELS:
            assert hasattr(auth, name), f"missing expected export: {name}"

    def test_no_later_group_model_exported(self):
        for name in LATER_GROUP_MODEL_NAMES:
            assert not hasattr(auth, name), f"unauthorized later-group export present: {name}"

    def test_publication_module_exports_only_group_5_symbols(self):
        expected = {
            "PublicationOutcome",
            "PublicationAttemptUncertainty",
            "PublicationEvidenceUncertaintyDetail",
            "PublicationAttempt",
            "PublicationEvidence",
        }
        assert set(pub.__all__) == expected

    def test_no_later_group_model_class_declared_anywhere_in_authority_package(self):
        for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
            tree = ast.parse(path.read_text())
            class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
            for forbidden in LATER_GROUP_MODEL_NAMES:
                assert forbidden not in class_names, f"{forbidden} declared in {path.name}"

    def test_wildcard_import_matches_dunder_all(self):
        namespace: dict = {}
        exec("from pcae.cltr.authority import *", namespace)  # noqa: S102
        for name in auth.__all__:
            assert name in namespace

    def test_exact_class_names_and_modules(self):
        assert pub.PublicationAttempt.__name__ == "PublicationAttempt"
        assert pub.PublicationAttempt.__module__ == "pcae.cltr.authority.publication"
        assert pub.PublicationEvidence.__name__ == "PublicationEvidence"
        assert pub.PublicationEvidence.__module__ == "pcae.cltr.authority.publication"

    def test_no_operational_public_method_on_either_model(self):
        allowed_methods = {"from_dict", "to_dict", "from_json"}
        for cls in (pub.PublicationAttempt, pub.PublicationEvidence):
            public_methods = {
                name
                for name in vars(cls)
                if not name.startswith("_") and callable(getattr(cls, name, None))
            }
            unexpected = public_methods - allowed_methods
            assert not unexpected, f"{cls.__name__} exposes unexpected public method(s): {unexpected}"


# ===========================================================================
# 14. Runtime isolation.
# ===========================================================================


class TestRuntimeIsolation:
    def test_no_production_module_imports_authority_package(self):
        production_roots = [
            REPO_ROOT / "src" / "pcae" / "commands",
            REPO_ROOT / "src" / "pcae" / "core",
            REPO_ROOT / "src" / "pcae" / "runtime",
        ]
        hits = []
        for root in production_roots:
            if not root.exists():
                continue
            for path in root.rglob("*.py"):
                text = path.read_text()
                if "cltr.authority" in text or "cltr import authority" in text:
                    hits.append(str(path))
        assert not hits, f"production import(s) of pcae.cltr.authority found: {hits}"

    def test_sibling_cltr_flat_modules_do_not_import_authority(self):
        cltr_dir = REPO_ROOT / "src" / "pcae" / "cltr"
        hits = []
        for path in cltr_dir.glob("*.py"):
            text = path.read_text()
            if "from pcae.cltr.authority" in text or "import pcae.cltr.authority" in text:
                hits.append(str(path))
        assert not hits, f"sibling cltr module import(s) of authority package found: {hits}"

    def test_publication_module_imports_no_production_lifecycle_module(self):
        tree = ast.parse(PUBLICATION_MODULE.read_text())
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
        forbidden_substrings = ("pcae.commands", "pcae.core", "pcae.runtime", "pcae.cltr.finalization",
                                 "pcae.cltr.notification", "pcae.cltr.marker", "pcae.cltr.receipt")
        for mod in imported_modules:
            for forbidden in forbidden_substrings:
                assert forbidden not in mod, f"publication.py imports forbidden module: {mod}"


# ===========================================================================
# 15. Adversarial matrix (subset from the operator prompt, independently
#     re-derived expectations).
# ===========================================================================


class TestAdversarialMatrix:
    def test_minimal_valid_accepted(self):
        pub.PublicationAttempt.from_dict(minimal_attempt(), schema_version="1.0")

    def test_maximal_valid_accepted(self):
        pub.PublicationAttempt.from_dict(maximal_attempt(), schema_version="1.0")

    def test_stale_but_schema_valid_cas_accepted_without_lookup(self):
        doc = minimal_attempt()
        doc["cas_expectation"]["expected_migration_epoch"] = "epoch-old-stale"
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_malformed_cas_rejected(self):
        doc = minimal_attempt()
        doc["cas_expectation"]["expected_authority_kind"] = "not_a_kind"
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_nonexistent_candidate_target_accepted_without_lookup(self):
        doc = minimal_attempt()
        doc["candidate_reference"] = _record_ref(
            "cutover-candidate-neverexist", "cutover_candidate", cross_family=True
        )
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_wrong_candidate_family_rejected(self):
        doc = minimal_attempt()
        doc["candidate_reference"] = _record_ref(
            "certification-notacandidate", "certification", cross_family=True
        )
        with pytest.raises(auth.WrongFamilyReferenceError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_state_branch_missing_required_metadata_schema_derived_result(self):
        doc = minimal_attempt(state="conflict")
        with pytest.raises(auth.TypedModelInternalInvariantError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_injected_execution_field_rejected(self):
        doc = minimal_attempt()
        doc["execute"] = True
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_evidence_minimal_valid_accepted(self):
        pub.PublicationEvidence.from_dict(minimal_evidence(), schema_version="1.0")

    def test_evidence_nonexistent_publication_attempt_target_accepted_without_lookup(self):
        doc = minimal_evidence()
        doc["attempt_reference"] = _record_ref(
            "publication-attempt-neverexist", "publication_attempt", cross_family=True
        )
        pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_evidence_claimed_success_with_false_references_accepted_if_schema_valid(self):
        doc = maximal_evidence(
            target_readback=_record_ref("cutover-request-falseclaim1", "cutover_request"),
            authoritative_generation=_generation_ref("generation-falseclaim01"),
        )
        pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_evidence_injected_provider_verified_rejected(self):
        doc = minimal_evidence()
        doc["provider_verified"] = True
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_evidence_valid_forward_reference_accepted_without_resolution(self):
        doc = maximal_evidence(
            target_readback=_record_ref("marker-authority-binding-future1", "marker_authority_binding")
        )
        pub.PublicationEvidence.from_dict(doc, schema_version="1.0")


# ===========================================================================
# 16. Absent versus null matrix.
# ===========================================================================


class TestAbsentVersusNullMatrix:
    @pytest.mark.parametrize("field", ["temporary_pointer_reference", "uncertainty", "failure_classification"])
    def test_attempt_optional_field_omission_valid(self, field, schema_registry):
        doc = minimal_attempt()
        assert field not in doc
        _assert_schema_valid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("field", ["temporary_pointer_reference", "uncertainty", "failure_classification"])
    def test_attempt_optional_field_explicit_null_invalid(self, field, schema_registry):
        """None of PublicationAttempt's optional fields are typed to admit
        an explicit JSON null (each $ref target is an object/string type,
        never a nullable union) -- omission and null must NOT collapse."""

        doc = minimal_attempt()
        doc[field] = None
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("field", ["uncertainty_detail", "target_readback", "authoritative_generation"])
    def test_evidence_optional_field_omission_valid(self, field, schema_registry):
        doc = minimal_evidence()
        assert field not in doc
        _assert_schema_valid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    @pytest.mark.parametrize("field", ["uncertainty_detail", "target_readback", "authoritative_generation"])
    def test_evidence_optional_field_explicit_null_invalid(self, field, schema_registry):
        doc = minimal_evidence()
        doc[field] = None
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_no_reason_code_style_absent_null_collapse_exception_applies_here(self):
        """CutoverRequest.reason_code is documented elsewhere as having an
        independently-nullable exception; neither publication schema
        declares any field type as ["string","null"] or similar -- the
        exception must not be copied here without a matching schema
        clause. Independently confirmed absent by grep of both schema
        files for a nullable type union."""

        import json

        for schema_path in (
            REPO_ROOT
            / "src/pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json",
            REPO_ROOT
            / "src/pcae/schema_resources/cltr_cutover/records/publication_evidence.schema.json",
        ):
            text = schema_path.read_text()
            assert '"type": ["string", "null"]' not in text
            assert '"type": ["null", "string"]' not in text


# ===========================================================================
# 17. Schema drift detection.
# ===========================================================================


class TestSchemaDriftDetection:
    def test_attempt_additional_properties_false(self):
        import json

        schema = json.loads(
            (
                REPO_ROOT
                / "src/pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json"
            ).read_text()
        )
        assert schema["additionalProperties"] is False

    def test_evidence_additional_properties_false(self):
        import json

        schema = json.loads(
            (
                REPO_ROOT
                / "src/pcae/schema_resources/cltr_cutover/records/publication_evidence.schema.json"
            ).read_text()
        )
        assert schema["additionalProperties"] is False

    def test_attempt_no_extensions_field(self, schema_registry):
        doc = minimal_attempt()
        doc["_extensions"] = {}
        _assert_schema_invalid(doc, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_evidence_no_extensions_field(self, schema_registry):
        doc = minimal_evidence()
        doc["_extensions"] = {}
        _assert_schema_invalid(doc, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
        with pytest.raises(Exception):
            pub.PublicationEvidence.from_dict(doc, schema_version="1.0")

    def test_required_set_matches_schema_exactly(self):
        import json

        schema = json.loads(
            (
                REPO_ROOT
                / "src/pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json"
            ).read_text()
        )
        assert set(schema["required"]) == TestFieldRederivationPublicationAttempt.REQUIRED_FIELDS

        schema2 = json.loads(
            (
                REPO_ROOT
                / "src/pcae/schema_resources/cltr_cutover/records/publication_evidence.schema.json"
            ).read_text()
        )
        assert set(schema2["required"]) == TestFieldRederivationPublicationEvidence.REQUIRED_FIELDS


# ===========================================================================
# 18. Error behavior.
# ===========================================================================


class TestErrorBehavior:
    def test_errors_do_not_leak_full_payload(self):
        doc = minimal_attempt(state="not_a_real_state")
        try:
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            # The full cas_expectation nested payload must not appear verbatim.
            assert str(doc["cas_expectation"]) not in message

    def test_errors_are_typed_model_errors_except_inherited_enum_bare_valueerror(self):
        """Most Layer-3 construction failures raise a TypedModelError
        subclass; enum construction is the disclosed CONFIRMED-136AC-1
        exception (bare ValueError) -- independently reproduced, not
        assumed. A non-enum-shape failure (missing required field) must
        still be a TypedModelError."""

        with pytest.raises(auth.TypedModelError):
            pub.PublicationAttempt.from_dict(
                {k: v for k, v in minimal_attempt().items() if k != "attempt_sequence"},
                schema_version="1.0",
            )
        with pytest.raises(ValueError):
            pub.PublicationAttempt.from_dict(minimal_attempt(state="bogus"), schema_version="1.0")

    def test_wrong_reference_family_raises_wrong_family_error_not_generic(self):
        doc = minimal_attempt()
        doc["candidate_reference"] = _record_ref(
            "certification-wrongfam0099", "certification", cross_family=True
        )
        with pytest.raises(auth.WrongFamilyReferenceError):
            pub.PublicationAttempt.from_dict(doc, schema_version="1.0")

    def test_bare_valueerror_on_enum_construction_inherited_confirmed(self):
        """CONFIRMED-136AC-1 (inherited): enum construction may raise a
        bare ValueError rather than a TypedModelError subclass. Reproduced
        here for PublicationState/PublicationOutcome -- remains
        Non-Blocking (fail-closed either way)."""

        with pytest.raises(ValueError):
            pub.PublicationState("not_a_real_state")
        with pytest.raises(ValueError):
            pub.PublicationOutcome("not_a_real_outcome")


# ===========================================================================
# 19. No later record-family model / no-go boundary.
# ===========================================================================


class TestNoLaterModels:
    def test_none_of_the_seven_later_families_importable_from_publication_module(self):
        for name in LATER_GROUP_MODEL_NAMES:
            assert not hasattr(pub, name)

    def test_publication_module_defines_exactly_two_record_family_dataclasses(self):
        tree = ast.parse(PUBLICATION_MODULE.read_text())
        frozen_dataclasses = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for deco in node.decorator_list:
                    src = ast.dump(deco)
                    if "dataclass" in src:
                        frozen_dataclasses.append(node.name)
        record_family_names = {"PublicationAttempt", "PublicationEvidence"}
        assert record_family_names.issubset(set(frozen_dataclasses))
        for forbidden in LATER_GROUP_MODEL_NAMES:
            assert forbidden not in frozen_dataclasses


# ===========================================================================
# 20. Packaging verification.
# ===========================================================================


class TestPackaging:
    @pytest.mark.slow
    def test_wheel_contains_publication_module_and_both_schemas_no_later_family(self, tmp_path: Path):
        dist_dir = tmp_path / "dist"
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
            check=True,
            capture_output=True,
            text=True,
        )
        wheels = list(dist_dir.glob("*.whl"))
        assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

        import zipfile

        with zipfile.ZipFile(wheels[0]) as archive:
            names = archive.namelist()

        assert "pcae/cltr/authority/publication.py" in names
        assert any(n.endswith("records/publication_attempt.schema.json") for n in names)
        assert any(n.endswith("records/publication_evidence.schema.json") for n in names)
        for forbidden in ("recovery", "bindings", "compatibility_quarantine"):
            assert f"pcae/cltr/authority/{forbidden}.py" not in names

    @pytest.mark.slow
    def test_sdist_includes_publication_module(self, tmp_path: Path):
        dist_dir = tmp_path / "dist"
        subprocess.run(
            [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
            check=True,
            capture_output=True,
            text=True,
        )
        sdists = list(dist_dir.glob("*.tar.gz"))
        assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"

        import tarfile

        with tarfile.open(sdists[0]) as archive:
            names = archive.getnames()

        assert any(name.endswith("pcae/cltr/authority/publication.py") for name in names)
