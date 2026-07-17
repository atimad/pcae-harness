"""Phase 136O: Authorization and Candidate Schema Independent Verification.

Independently authored adversarial tests attacking Phase 136N's Implementation
Group 4 (``HumanAuthorization``, ``CutoverCandidate``, ``Certification``) and
the embedded ``cas_expectation`` shared ``$def`` against the frozen primary
contract (``CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`` v1.0, Sec.21-24). This
module does not import or restate 136N's own test helpers/fixtures; every
fixture here is authored fresh, from the frozen contract text, in an attempt
to falsify 136N's claims rather than to repeat them.

Every test validates SHAPE only. No test in this module creates, reads, or
asserts anything about live CLTR authority, migration state, human
authorization truth, candidate eligibility, certification authenticity, or
production lifecycle behavior. Legacy lifecycle remains the sole production
authority; CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
HUMAN_AUTH_ID = BASE_ID + "records/human_authorization.schema.json"
CANDIDATE_ID = BASE_ID + "records/cutover_candidate.schema.json"
CERTIFICATION_ID = BASE_ID + "records/certification.schema.json"
MANIFEST_SCHEMA_ID = BASE_ID + "manifest.schema.json"

GROUP4_RECORD_FILES = {
    "records/certification.schema.json",
    "records/cutover_candidate.schema.json",
    "records/human_authorization.schema.json",
}

GROUP2_3_RECORD_FILES = {
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
}

LATER_GROUP_FAMILY_NAMES = (
    # publication_attempt and publication_evidence are no longer later-group:
    # Phase 136P legitimately implements them as Implementation Group 5.
    # concurrency_conflict and recovery_journal_entry are no longer
    # later-group: Phase 136R legitimately implements them as contract
    # Group 8. notification_authority_binding, marker_authority_binding,
    # and receipt_authority_binding are no longer later-group: Phase 136T
    # legitimately implements them as contract Group 10.
    "reconciliation_result",
    "quarantine_record",
    "compatibility_state",
    "historical_authority_reference",
)


@pytest.fixture(scope="module")
def root():
    with cltr_cutover_root() as path:
        yield path


@pytest.fixture(scope="module")
def registry(root):
    return build_offline_registry(root)


@pytest.fixture(scope="module")
def manifest(root, registry):
    return load_and_verify_manifest(
        root / "manifest.json",
        package_root=root,
        registry=registry,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )


def _ref(record_id: str, family: str, digest: str = "a" * 64, **extra) -> dict:
    ref = {"record_id": record_id, "record_digest": digest, "record_family": family}
    ref.update(extra)
    return ref


def _cas_expectation(**overrides) -> dict:
    base = {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _ref("epoch-0000000000000001", "authority_epoch"),
        "expected_authoritative_generation": {
            "generation_id": "gen-0000000000000001",
            "generation_digest": "b" * 64,
        },
        "expected_authority_pointer_digest": "c" * 64,
        "expected_authority_state_digest": "d" * 64,
        "expected_migration_epoch": "epoch-0001",
        "expected_source_lifecycle_state": "CERTIFIED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _ref("req-0000000000000001", "cutover_request"),
        "expected_certification_reference": _ref("cert-0000000000000001", "certification"),
    }
    base.update(overrides)
    return base


def _human_authorization(**overrides) -> dict:
    doc = {
        "schema_id": HUMAN_AUTH_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "human_authorization",
        "record_id": "ha-0000000000000001",
        "record_digest": "e" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "phase_id": "136O",
        "migration_epoch": "epoch-0001",
        "principal": "principal-verifier-136o",
        "method": "manual_review",
        "request_reference": _ref(
            "req-0000000000000001", "cutover_request",
            schema_id=BASE_ID + "records/cutover_request.schema.json", schema_version="1.0",
        ),
        "readiness_reference": _ref(
            "ready-0000000000000001", "readiness_package",
            schema_id=BASE_ID + "records/readiness_package.schema.json", schema_version="1.0",
        ),
        "target_reference": _ref(
            "epoch-0000000000000002", "authority_epoch",
            schema_id=BASE_ID + "records/authority_epoch.schema.json", schema_version="1.0",
        ),
        "issued_at": "2026-07-16T00:00:00Z",
        "expires_at": "2026-07-17T00:00:00Z",
        "state": "issued",
        "replay_binding": "replay-token-ref-0001",
        "risk_acknowledgement": True,
        "limitations": [],
        "authority_disclosure": {"authority_role": "derivative", "is_authoritative": False, "disclosure_text": "Local shape verification only; not proof of authority."},
    }
    doc.update(overrides)
    return doc


def _cutover_candidate(**overrides) -> dict:
    doc = {
        "schema_id": CANDIDATE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_candidate",
        "record_id": "cc-0000000000000001",
        "record_digest": "f" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "migration_epoch": "epoch-0001",
        "stage2_generation_reference": _ref("gen-0000000000000002", "readiness_package"),
        "cas_expectation": _cas_expectation(),
        "state": "proposed",
        "limitations": [],
        "authority_disclosure": {"authority_role": "derivative", "is_authoritative": False, "disclosure_text": "Local shape verification only; not proof of authority."},
    }
    doc.update(overrides)
    return doc


def _certification(**overrides) -> dict:
    doc = {
        "schema_id": CERTIFICATION_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "certification",
        "record_id": "cert-0000000000000001",
        "record_digest": "2" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "phase_id": "136O",
        "migration_epoch": "epoch-0001",
        "candidate_reference": _ref(
            "cc-0000000000000001", "cutover_candidate",
            schema_id=CANDIDATE_ID, schema_version="1.0",
        ),
        "request_reference": _ref(
            "req-0000000000000001", "cutover_request",
            schema_id=BASE_ID + "records/cutover_request.schema.json", schema_version="1.0",
        ),
        "readiness_reference": _ref(
            "ready-0000000000000001", "readiness_package",
            schema_id=BASE_ID + "records/readiness_package.schema.json", schema_version="1.0",
        ),
        "authorization_reference": _ref(
            "ha-0000000000000001", "human_authorization",
            schema_id=HUMAN_AUTH_ID, schema_version="1.0",
        ),
        "source_authority_reference": _ref("epoch-0000000000000001", "authority_epoch"),
        "target_epoch_reference": _ref("epoch-0000000000000002", "authority_epoch"),
        "cas_expectation": _cas_expectation(),
        "verifier_evidence": [],
        "state": "pending",
        "limitations": [],
        "authority_disclosure": {"authority_role": "derivative", "is_authoritative": False, "disclosure_text": "Local shape verification only; not proof of authority."},
    }
    doc.update(overrides)
    return doc


# ---------------------------------------------------------------------------
# 1. Exact inventory verification
# ---------------------------------------------------------------------------


def test_manifest_contains_exactly_seven_record_schemas(manifest):
    # Updated by Phase 136P (nine), Phase 136R (eleven), and Phase 136T:
    # fourteen record schemas now legitimately exist (the seven Group
    # 2+3+4 schemas plus the two Group 5 schemas plus the two Group 8
    # schemas plus the three new Group 10 schemas).
    record_entries = [e for e in manifest.entries if e.file_path.startswith("records/")]
    assert len(record_entries) == 14, sorted(e.file_path for e in record_entries)


def test_manifest_contains_exactly_three_group4_record_schemas(manifest):
    raw_by_path = {e["file_path"]: e for e in manifest.document["entries"]}
    group4 = [path for path, e in raw_by_path.items() if e["implementation_group"] == 4]
    assert set(group4) == GROUP4_RECORD_FILES


def test_no_standalone_cas_expectation_record_schema_exists(root):
    names = {p.name for p in (root / "records").glob("*.schema.json")}
    assert not any("cas_expectation" in n for n in names), names


def test_no_group5_or_later_record_schema_files_exist(root):
    names = {p.stem.replace(".schema", "") for p in (root / "records").glob("*.schema.json")}
    for later in LATER_GROUP_FAMILY_NAMES:
        assert later not in names, f"unexpected later-group family present on disk: {later}"


def test_no_bindings_or_views_directories_exist(root):
    assert not (root / "bindings").exists()
    assert not (root / "views").exists()


def test_cas_expectation_is_embedded_def_not_manifest_entry(manifest):
    ids = {e.schema_id for e in manifest.entries}
    assert not any(sid.endswith("cas_expectation.schema.json") for sid in ids)


def test_cas_expectation_embedded_in_exactly_candidate_and_certification(registry):
    candidate_doc = registry.document(CANDIDATE_ID)
    certification_doc = registry.document(CERTIFICATION_ID)
    assert candidate_doc["properties"]["cas_expectation"]["$ref"].endswith("cas_expectation")
    assert certification_doc["properties"]["cas_expectation"]["$ref"].endswith("cas_expectation")
    human_auth_doc = registry.document(HUMAN_AUTH_ID)
    assert "cas_expectation" not in human_auth_doc["properties"]


# ---------------------------------------------------------------------------
# 2. Valid baseline sanity (each fresh fixture must actually validate)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "schema_id,factory",
    [
        (HUMAN_AUTH_ID, _human_authorization),
        (CANDIDATE_ID, _cutover_candidate),
        (CERTIFICATION_ID, _certification),
    ],
)
def test_fresh_valid_fixture_validates(registry, schema_id, factory):
    result = validate_record_shape(factory(), schema_id=schema_id, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# 3. HumanAuthorization adversarial verification
# ---------------------------------------------------------------------------


def test_human_authorization_rejects_unknown_top_level_field(registry):
    doc = _human_authorization(scope="global-admin")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_has_no_general_purpose_scope_field(registry):
    doc = registry.document(HUMAN_AUTH_ID)
    assert "scope" not in doc["properties"]


def test_human_authorization_requires_expires_at(registry):
    doc = _human_authorization()
    del doc["expires_at"]
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_rejects_null_expires_at(registry):
    doc = _human_authorization(expires_at=None)
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_revoked_requires_revocation_metadata(registry):
    doc = _human_authorization(state="revoked")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_non_revoked_forbids_revocation_metadata(registry):
    doc = _human_authorization(
        revocation_metadata={
            "revoked_at": "2026-07-16T00:00:00Z",
            "revoked_by": "principal-x",
            "reason_code": "manual_review_failed",
        }
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_used_requires_use_binding(registry):
    doc = _human_authorization(state="used")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_used_with_use_binding_validates(registry):
    doc = _human_authorization(
        state="used",
        use_binding=_ref("pub-attempt-0000000000000001", "publication_attempt"),
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


def test_human_authorization_signed_attestation_requires_proof_reference(registry):
    doc = _human_authorization(method="signed_attestation")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_manual_review_forbids_proof_reference(registry):
    doc = _human_authorization(
        method="manual_review",
        proof_reference=_ref("proof-0000000000000001", "human_authorization"),
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_risk_acknowledgement_must_be_true(registry):
    doc = _human_authorization(risk_acknowledgement=False)
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_rejects_unknown_state(registry):
    doc = _human_authorization(state="approved")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_rejects_unknown_method(registry):
    doc = _human_authorization(method="verbal_agreement")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


# family-substitution attacks
def test_human_authorization_rejects_readiness_reference_in_request_slot(registry):
    doc = _human_authorization()
    doc["request_reference"] = _ref(
        "ready-0000000000000001", "readiness_package",
        schema_id=BASE_ID + "records/readiness_package.schema.json", schema_version="1.0",
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_rejects_authority_epoch_in_readiness_slot(registry):
    doc = _human_authorization()
    doc["readiness_reference"] = _ref(
        "epoch-0000000000000001", "authority_epoch",
        schema_id=BASE_ID + "records/authority_epoch.schema.json", schema_version="1.0",
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_human_authorization_rejects_cutover_request_in_target_slot(registry):
    doc = _human_authorization()
    doc["target_reference"] = _ref(
        "req-0000000000000001", "cutover_request",
        schema_id=BASE_ID + "records/cutover_request.schema.json", schema_version="1.0",
    )
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


# secret-handling probes
SECRET_LIKE_VALUES = [
    "password123!",
    "sk-ant-api03-fake-0123456789abcdef",
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "8271633376:AAF-fake-telegram-bot-token-value",
    "-----BEGIN PRIVATE KEY-----\nMIIfake\n-----END PRIVATE KEY-----",
    "API_KEY=sk_live_fake_0000000000000000",
    "https://user:hunter2@example.test/resource",
    "ya29.fake-oauth-access-token-value",
]


@pytest.mark.parametrize("secret", SECRET_LIKE_VALUES)
def test_human_authorization_replay_binding_pattern_rejects_secret_shaped_values(registry, secret):
    doc = _human_authorization(replay_binding=secret)
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    # replay_binding is pattern-restricted ([A-Za-z0-9._-]{1,256}); most
    # secret-shaped strings (spaces, ':', '=', '@', newlines) violate that
    # pattern incidentally. This is NOT comprehensive secret detection --
    # only a structural side effect of the opaque-token pattern.
    looks_pattern_valid = bool(__import__("re").fullmatch(r"[A-Za-z0-9._-]{1,256}", secret))
    if looks_pattern_valid:
        assert result.status == OutcomeStatus.VALID
    else:
        assert result.status == OutcomeStatus.INVALID


def test_human_authorization_replay_binding_accepts_opaque_token_that_happens_to_look_key_shaped(registry):
    # A pattern-conforming opaque string is accepted regardless of whether it
    # superficially resembles a key -- proving the schema does NOT perform
    # semantic secret detection, only opaque-shape structural validation.
    doc = _human_authorization(replay_binding="skantapi03fakekeylookingtoken0001")
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. CutoverCandidate adversarial verification
# ---------------------------------------------------------------------------


def test_cutover_candidate_has_no_direct_readiness_or_authorization_binding_fields(registry):
    doc = registry.document(CANDIDATE_ID)
    assert "readiness_reference" not in doc["properties"]
    assert "authorization_reference" not in doc["properties"]
    assert set(doc["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type",
        "record_id", "record_digest", "created_at", "migration_epoch",
        "stage2_generation_reference", "cas_expectation", "state",
        "limitations", "authority_disclosure",
    }


def test_cutover_candidate_cas_expectation_does_not_reach_readiness_or_authorization(registry):
    # cas_expectation only carries expected_request_reference and
    # expected_certification_reference -- neither a readiness nor an
    # authorization binding is reachable indirectly through it either.
    doc = registry.document(BASE_ID + "shared/references.schema.json")
    cas_fields = set(doc["$defs"]["cas_expectation"]["required"])
    assert "expected_readiness_reference" not in cas_fields
    assert "expected_authorization_reference" not in cas_fields


def test_cutover_candidate_rejects_unknown_top_level_field(registry):
    doc = _cutover_candidate(readiness_reference=_ref("x", "readiness_package"))
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cutover_candidate_accepts_extensions_object(registry):
    doc = _cutover_candidate(_extensions={"note": "adversarial-probe"})
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


def test_cutover_candidate_rejects_non_string_extension_values(registry):
    doc = _cutover_candidate(_extensions={"note": 12345})
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cutover_candidate_rejects_unknown_state(registry):
    doc = _cutover_candidate(state="published")
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "state", ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"]
)
def test_cutover_candidate_accepts_every_contract_state(registry, state):
    doc = _cutover_candidate(state=state)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


def test_cutover_candidate_certified_state_alone_does_not_imply_authoritative(registry):
    doc = _cutover_candidate(state="certified")
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID
    assert doc["authority_disclosure"]["is_authoritative"] is False


def test_cutover_candidate_forbids_authoritative_role(registry):
    doc = _cutover_candidate(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "probe"}
    )
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cutover_candidate_rejects_missing_cas_expectation_field(registry):
    for field in [
        "expected_authority_kind", "expected_authority_epoch",
        "expected_authoritative_generation", "expected_authority_pointer_digest",
        "expected_authority_state_digest", "expected_migration_epoch",
        "expected_source_lifecycle_state", "expected_compatibility_mode",
        "expected_journal_lock_state", "expected_request_reference",
        "expected_certification_reference",
    ]:
        cas = _cas_expectation()
        del cas[field]
        doc = _cutover_candidate(cas_expectation=cas)
        result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
        assert result.status == OutcomeStatus.INVALID, f"missing {field} should be rejected"


def test_cutover_candidate_rejects_wrong_family_in_expected_authority_epoch(registry):
    cas = _cas_expectation(expected_authority_epoch=_ref("req-0001", "cutover_request"))
    doc = _cutover_candidate(cas_expectation=cas)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Certification adversarial verification
# ---------------------------------------------------------------------------


def test_certification_has_no_certifier_principal_field(registry):
    doc = registry.document(CERTIFICATION_ID)
    assert "principal" not in doc["properties"]
    assert "certifier_principal" not in doc["properties"]


def test_certification_carries_verifier_evidence_array_instead(registry):
    doc = registry.document(CERTIFICATION_ID)
    assert doc["properties"]["verifier_evidence"]["type"] == "array"


def test_certification_rejects_unknown_top_level_field(registry):
    doc = _certification(certifier_principal="principal-x")
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_certification_stale_requires_staleness_object(registry):
    doc = _certification(state="stale")
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_certification_stale_with_staleness_validates(registry):
    doc = _certification(
        state="stale",
        staleness={"detected_at": "2026-07-16T00:00:00Z", "reason_code": "stale_certification"},
    )
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


def test_certification_invalidated_requires_invalidation_object(registry):
    doc = _certification(state="invalidated")
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_certification_non_stale_forbids_staleness_object(registry):
    doc = _certification(
        state="pending",
        staleness={"detected_at": "2026-07-16T00:00:00Z", "reason_code": "stale_certification"},
    )
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_certification_forbids_authoritative_role(registry):
    doc = _certification(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "probe"}
    )
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


# family-substitution attacks across all five certification reference slots
CERTIFICATION_REFERENCE_SLOTS = [
    ("candidate_reference", "cutover_candidate"),
    ("request_reference", "cutover_request"),
    ("readiness_reference", "readiness_package"),
    ("authorization_reference", "human_authorization"),
]


@pytest.mark.parametrize("slot,correct_family", CERTIFICATION_REFERENCE_SLOTS)
def test_certification_rejects_wrong_family_substitution(registry, slot, correct_family):
    wrong_family = next(f for _, f in CERTIFICATION_REFERENCE_SLOTS if f != correct_family)
    doc = _certification()
    doc[slot] = _ref(
        "sub-0000000000000001", wrong_family,
        schema_id=BASE_ID + f"records/{wrong_family}.schema.json", schema_version="1.0",
    )
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID, f"{slot} should reject {wrong_family}"


def test_certification_allows_identical_source_and_target_epoch(registry):
    # Sec.23 does not forbid source_authority_reference == target_epoch_reference.
    doc = _certification(
        source_authority_reference=_ref("epoch-same", "authority_epoch"),
        target_epoch_reference=_ref("epoch-same", "authority_epoch"),
    )
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# 6. Embedded CAS expectation adversarial verification
# ---------------------------------------------------------------------------


def test_cas_expectation_rejects_unknown_field(registry):
    cas = _cas_expectation(unexpected_field="x")
    doc = _cutover_candidate(cas_expectation=cas)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cas_expectation_rejects_null_for_required_field(registry):
    cas = _cas_expectation(expected_migration_epoch=None)
    doc = _cutover_candidate(cas_expectation=cas)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cas_expectation_rejects_unknown_compatibility_mode(registry):
    cas = _cas_expectation(expected_compatibility_mode="turbo")
    doc = _cutover_candidate(cas_expectation=cas)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cas_expectation_rejects_unknown_journal_lock_state(registry):
    cas = _cas_expectation(expected_journal_lock_state="half-locked")
    doc = _cutover_candidate(cas_expectation=cas)
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cas_expectation_schema_valid_record_does_not_imply_cas_success(root):
    # Structural assertion only: no runtime CAS/publication concept exists
    # anywhere in schema_runtime or schema_resources.
    for path in root.rglob("*.schema.json"):
        text = path.read_text()
        assert "cas_succeeded" not in text
        assert "publication_succeeded" not in text


# ---------------------------------------------------------------------------
# 7. Dependency graph verification (Groups 1-4)
# ---------------------------------------------------------------------------


def _collect_refs(node) -> set[str]:
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and "#" in value:
                file_part = value.split("#", 1)[0]
                if file_part:
                    found.add(file_part)
            found |= _collect_refs(value)
    elif isinstance(node, list):
        for item in node:
            found |= _collect_refs(item)
    return found


def test_dependency_graph_has_no_cycle_among_group1_4_files(root):
    files = list(root.glob("shared/*.schema.json")) + list(root.glob("records/*.schema.json"))
    graph: dict[str, set[str]] = {}
    for path in files:
        doc = json.loads(path.read_text())
        refs = _collect_refs(doc)
        graph[path.name] = {r for r in refs}

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]):
        if node in visited:
            return
        if node in visiting:
            raise AssertionError(f"cycle detected: {' -> '.join(stack + [node])}")
        visiting.add(node)
        for dep in graph.get(node, ()):
            visit(dep, stack + [node])
        visiting.discard(node)
        visited.add(node)

    for node in graph:
        visit(node, [])


def test_record_reference_graph_creation_order_is_derivable(manifest):
    # Independently derive a valid topological creation order from the
    # manifest's own dependency edges (a DFS-based toposort, not merely
    # implementation_group + id sorting, since Group 1 shared files
    # themselves depend on each other).
    raw_entries = manifest.document["entries"]
    by_id = {e["schema_id"]: e for e in raw_entries}

    visiting: set[str] = set()
    created: set[str] = set()

    def visit(schema_id: str, stack: list[str]):
        if schema_id in created:
            return
        if schema_id in visiting:
            raise AssertionError(f"dependency cycle: {' -> '.join(stack + [schema_id])}")
        visiting.add(schema_id)
        for dep in by_id[schema_id]["dependencies"]:
            visit(dep, stack + [schema_id])
        visiting.discard(schema_id)
        created.add(schema_id)

    for schema_id in by_id:
        visit(schema_id, [])
    assert len(created) == len(by_id)


# ---------------------------------------------------------------------------
# 8. Manifest / registry verification
# ---------------------------------------------------------------------------


def test_manifest_two_way_completeness_with_files_on_disk(root, manifest):
    manifest_paths = {e.file_path for e in manifest.entries}
    on_disk = {
        str(p.relative_to(root))
        for p in list(root.glob("records/*.schema.json")) + list(root.glob("shared/*.schema.json"))
    }
    assert manifest_paths == on_disk


def test_manifest_has_no_duplicate_schema_id_or_path(manifest):
    ids = [e.schema_id for e in manifest.entries]
    paths = [e.file_path for e in manifest.entries]
    assert len(ids) == len(set(ids))
    assert len(paths) == len(set(paths))


def test_registry_schema_ids_deterministically_ordered(root):
    r1 = build_offline_registry(root)
    r2 = build_offline_registry(root)
    assert r1.schema_ids == r2.schema_ids
    assert list(r1.schema_ids) == sorted(r1.schema_ids)


def test_group4_entries_declare_frozen_status(manifest):
    for entry in manifest.document["entries"]:
        if entry["file_path"] in GROUP4_RECORD_FILES:
            assert entry["status"] == "frozen"


# ---------------------------------------------------------------------------
# 9. No-authority / no-execution / no-network structural verification
# ---------------------------------------------------------------------------


def test_no_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


def test_schema_runtime_source_contains_no_subprocess_or_socket_calls():
    schema_runtime_dir = Path(__file__).resolve().parents[1] / "src" / "pcae" / "schema_runtime"
    for path in schema_runtime_dir.glob("*.py"):
        tree_source = path.read_text()
        # Only flag actual call sites, not docstring prose mentioning the words.
        import ast as _ast

        tree = _ast.parse(tree_source, filename=str(path))
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Call):
                func = node.func
                dotted = None
                if isinstance(func, _ast.Attribute):
                    dotted = func.attr
                elif isinstance(func, _ast.Name):
                    dotted = func.id
                assert dotted not in {"run", "Popen", "call", "check_call", "check_output", "socket", "create_connection"}, (
                    f"{path.name} calls {dotted}(...)"
                )


def test_validate_record_shape_does_not_touch_network(monkeypatch, registry):
    def _boom(*_args, **_kwargs):
        raise AssertionError("network access attempted during validation")

    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    for schema_id, factory in (
        (HUMAN_AUTH_ID, _human_authorization),
        (CANDIDATE_ID, _cutover_candidate),
        (CERTIFICATION_ID, _certification),
    ):
        result = validate_record_shape(factory(), schema_id=schema_id, registry=registry)
        assert result.status == OutcomeStatus.VALID


def test_no_subprocess_invoked_during_registry_build(monkeypatch, root):
    def _boom(*_args, **_kwargs):
        raise AssertionError("subprocess invoked while building registry")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    build_offline_registry(root)


# ---------------------------------------------------------------------------
# 10. Absent-vs-null contract verification
# ---------------------------------------------------------------------------


def test_human_authorization_conditional_fields_forbid_null_when_absent(registry):
    doc = _human_authorization()
    doc["revocation_metadata"] = None
    result = validate_record_shape(doc, schema_id=HUMAN_AUTH_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_certification_conditional_fields_forbid_null_when_absent(registry):
    doc = _certification()
    doc["staleness"] = None
    result = validate_record_shape(doc, schema_id=CERTIFICATION_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID


def test_cutover_candidate_limitations_array_may_be_empty_but_not_absent(registry):
    doc = _cutover_candidate()
    del doc["limitations"]
    result = validate_record_shape(doc, schema_id=CANDIDATE_ID, registry=registry)
    assert result.status == OutcomeStatus.INVALID
    doc2 = _cutover_candidate(limitations=[])
    result2 = validate_record_shape(doc2, schema_id=CANDIDATE_ID, registry=registry)
    assert result2.status == OutcomeStatus.VALID
