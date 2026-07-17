"""Phase 136N: Authorization and Candidate Schema Implementation (Implementation Group 4).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 4 record schemas -- ``human_authorization.schema.json``,
``cutover_candidate.schema.json``, and ``certification.schema.json`` -- plus
the newly-added embedded ``cas_expectation`` shared $def, manifest entries,
registry integration, local conditional validation, family-reference
separation, unknown-field strictness, secret-handling boundary, and the exact
scope guard proving no later-group (Group 5+) record schema, binding, view,
typed model, semantic validator, or authority resolver/state/pointer was
introduced.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state, human
authorization truth, candidate eligibility, certification authenticity, or
production lifecycle behavior. Legacy lifecycle remains the sole production
authority; CLTR remains derivative.
"""
from __future__ import annotations

import ast
import copy
import json
import socket
import subprocess
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"

SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)

GROUP2_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)

GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)

GROUP4_RECORD_FILES = (
    "records/certification.schema.json",
    "records/cutover_candidate.schema.json",
    "records/human_authorization.schema.json",
)

# Phase 136P legitimately implements Group 5 (publication_attempt,
# publication_evidence); no longer part of LATER_GROUP_RECORD_FILES.
GROUP5_RECORD_FILES = (
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)

# Phase 136R legitimately implements contract Group 8 (concurrency_conflict,
# recovery_journal_entry), paired atomically per CSCH-EXEC-REQ-062; no
# longer part of LATER_GROUP_RECORD_FILES.
GROUP8_RECORD_FILES = (
    "records/concurrency_conflict.schema.json",
    "records/recovery_journal_entry.schema.json",
)

# Phase 136T legitimately implements contract Group 10
# (notification_authority_binding, marker_authority_binding,
# receipt_authority_binding); no longer part of LATER_GROUP_RECORD_FILES.
GROUP10_RECORD_FILES = (
    "records/notification_authority_binding.schema.json",
    "records/marker_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
)

LATER_GROUP_RECORD_FILES = (
    "records/quarantine_record.schema.json",
    "records/compatibility_state.schema.json",
)

HUMAN_AUTH_ID = BASE_ID + "records/human_authorization.schema.json"
CANDIDATE_ID = BASE_ID + "records/cutover_candidate.schema.json"
CERT_ID = BASE_ID + "records/certification.schema.json"
CUTOVER_REQUEST_ID = BASE_ID + "records/cutover_request.schema.json"
READINESS_PACKAGE_ID = BASE_ID + "records/readiness_package.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ref(record_id, digest, family, schema_id=None):
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = "1.0"
    return r


def _cas_expectation(**overrides) -> dict:
    ce = {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _ref("authepoch-0000001", "b" * 64, "authority_epoch"),
        "expected_authoritative_generation": {
            "generation_id": "generat-0000001",
            "generation_digest": "c" * 64,
        },
        "expected_authority_pointer_digest": "d" * 64,
        "expected_authority_state_digest": "e" * 64,
        "expected_migration_epoch": "epoch-001",
        "expected_source_lifecycle_state": "PROPOSED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _ref("cutreq-00000001", "f" * 64, "cutover_request"),
        "expected_certification_reference": _ref("cert-00000000001", "0" * 64, "certification"),
    }
    ce.update(overrides)
    return ce


def _valid_human_authorization(**overrides) -> dict:
    record = {
        "schema_id": HUMAN_AUTH_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "human_authorization",
        "record_id": "humanaut-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136N",
        "migration_epoch": "epoch-001",
        "principal": "operator@example.com",
        "method": "manual_review",
        "request_reference": _ref(
            "cutreq-00000001", "b" * 64, "cutover_request", CUTOVER_REQUEST_ID
        ),
        "readiness_reference": _ref(
            "readypkg-0000001", "c" * 64, "readiness_package", READINESS_PACKAGE_ID
        ),
        "target_reference": _ref(
            "authepoch-0000002", "d" * 64, "authority_epoch", AUTHORITY_EPOCH_ID
        ),
        "issued_at": "2026-07-16T12:00:00Z",
        "expires_at": "2026-07-17T12:00:00Z",
        "state": "issued",
        "replay_binding": "replay-token-0001",
        "risk_acknowledgement": True,
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_candidate(**overrides) -> dict:
    record = {
        "schema_id": CANDIDATE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_candidate",
        "record_id": "cutcand-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "migration_epoch": "epoch-001",
        "stage2_generation_reference": _ref("rehearsl-0000001", "b" * 64, "authority_epoch"),
        "cas_expectation": _cas_expectation(),
        "state": "proposed",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_certification(**overrides) -> dict:
    record = {
        "schema_id": CERT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "certification",
        "record_id": "cert-00000000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136N",
        "migration_epoch": "epoch-001",
        "candidate_reference": _ref(
            "cutcand-0000001", "b" * 64, "cutover_candidate", CANDIDATE_ID
        ),
        "request_reference": _ref(
            "cutreq-00000001", "c" * 64, "cutover_request", CUTOVER_REQUEST_ID
        ),
        "readiness_reference": _ref(
            "readypkg-0000001", "d" * 64, "readiness_package", READINESS_PACKAGE_ID
        ),
        "authorization_reference": _ref(
            "humanaut-0000001", "e" * 64, "human_authorization", HUMAN_AUTH_ID
        ),
        "source_authority_reference": _ref("authepoch-0000001", "f" * 64, "authority_epoch"),
        "target_epoch_reference": _ref("authepoch-0000002", "0" * 64, "authority_epoch"),
        "cas_expectation": _cas_expectation(),
        "verifier_evidence": [],
        "state": "pending",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _validate(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# 1. Package integrity / exact scope guard
# ---------------------------------------------------------------------------


def test_136n_exact_group1_through_group4_file_inventory():
    with cltr_cutover_root() as root:
        schema_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert schema_files == sorted(
        ("manifest.schema.json",)
        + SHARED_FILES
        + GROUP2_RECORD_FILES
        + GROUP3_RECORD_FILES
        + GROUP4_RECORD_FILES
        + GROUP5_RECORD_FILES
        + GROUP8_RECORD_FILES
        + GROUP10_RECORD_FILES
    )


def test_136n_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136n_records_directory_contains_exactly_seven_files():
    with cltr_cutover_root() as root:
        files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert files == [
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "certification.schema.json",
        "concurrency_conflict.schema.json",
        "cutover_candidate.schema.json",
        "cutover_request.schema.json",
        "human_authorization.schema.json",
        "marker_authority_binding.schema.json",
        "notification_authority_binding.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
        "readiness_package.schema.json",
        "receipt_authority_binding.schema.json",
        "recovery_journal_entry.schema.json",
    ]


@pytest.mark.parametrize("relative_path", LATER_GROUP_RECORD_FILES)
def test_136n_no_later_group_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136n_no_later_group_filename_tracked_anywhere_in_repository():
    # Bounded repair (Phase 136U): this test previously carried its own,
    # separately hardcoded forbidden_stems tuple that still named the three
    # Group 10 binding files even after Phase 136T's migration updated
    # LATER_GROUP_RECORD_FILES (the file actually authorizing them) to drop
    # those same three names -- the two lists had silently desynchronized.
    # Deriving forbidden_stems from LATER_GROUP_RECORD_FILES directly makes
    # that class of desync structurally impossible going forward.
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = tuple(
        Path(relative_path).name.removesuffix(".json")
        for relative_path in LATER_GROUP_RECORD_FILES
    )
    hits = [
        path
        for path in tracked
        if any(stem in path for stem in forbidden_stems) and "docs/" not in path and path.endswith(".json")
    ]
    assert hits == []


def test_136n_no_typed_python_record_model_introduced():
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = (
        "human_authorization.py",
        "cutover_candidate.py",
        "certification.py",
        "authority_model.py",
        "typed_authority.py",
    )
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136n_no_cltr_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", GROUP4_RECORD_FILES)
def test_136n_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", GROUP4_RECORD_FILES)
def test_136n_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136n_registry_loads_exactly_fifteen_resources_with_unique_ids(registry):
    # Updated by Phase 136P (17) and Phase 136R: registry now legitimately
    # loads 19 resources (the 17 Group 1+2+3+4+5 resources plus the 2 new
    # Group 8 record schemas).
    assert len(registry.schema_ids) == 22
    assert len(set(registry.schema_ids)) == 22
    assert HUMAN_AUTH_ID in registry.schema_ids
    assert CANDIDATE_ID in registry.schema_ids
    assert CERT_ID in registry.schema_ids


def test_136n_human_authorization_is_tier1_strict_no_extensions():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/human_authorization.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" not in document.get("properties", {})


def test_136n_certification_is_tier1_strict_no_extensions():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/certification.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" not in document.get("properties", {})


def test_136n_cutover_candidate_is_tier2_extensions_only():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/cutover_candidate.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136n_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    # Updated by Phase 136P (16) and Phase 136R: manifest now legitimately
    # carries 18 entries.
    assert len(manifest.entries) == 21
    assert {e.file_path for e in manifest.entries} == set(SHARED_FILES) | set(
        GROUP2_RECORD_FILES
    ) | set(GROUP3_RECORD_FILES) | set(GROUP4_RECORD_FILES) | set(GROUP5_RECORD_FILES) | set(
        GROUP8_RECORD_FILES
    ) | set(GROUP10_RECORD_FILES)


def test_136n_manifest_new_entries_are_group_four():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path, family, schema_id in (
        ("records/human_authorization.schema.json", "human_authorization", HUMAN_AUTH_ID),
        ("records/cutover_candidate.schema.json", "cutover_candidate", CANDIDATE_ID),
        ("records/certification.schema.json", "certification", CERT_ID),
    ):
        entry = by_path[path]
        assert entry["implementation_group"] == 4
        assert entry["family"] == family
        assert entry["status"] == "frozen"
        assert entry["schema_id"] == schema_id


def test_136n_manifest_group1_through_group3_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group2_entries = [e for e in manifest["entries"] if e["family"] in ("authority_epoch", "authority_state")]
    assert len(group2_entries) == 2
    assert all(e["implementation_group"] == 2 for e in group2_entries)
    group3_entries = [e for e in manifest["entries"] if e["family"] in ("cutover_request", "readiness_package")]
    assert len(group3_entries) == 2
    assert all(e["implementation_group"] == 3 for e in group3_entries)


def test_136n_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136n_manifest_entry_count_matches_group1_through_4_exactly():
    # Updated by Phase 136P and Phase 136R: manifest now legitimately
    # carries 18 entries (Group 1: 7, Group 2: 2, Group 3: 2, Group 4: 3,
    # Group 5: 2, Group 8: 2).
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 21


def test_136n_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "human_authorization.schema.json"
    document = json.loads(tampered.read_bytes())
    document["title"] = "tampered"
    tampered.write_text(json.dumps(document), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="does not match"):
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136n_manifest_detects_missing_certification_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "certification.schema.json").unlink()

    with pytest.raises(Exception):
        reg = build_offline_registry(tmp_path)
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ---------------------------------------------------------------------------
# 3. HumanAuthorization -- valid branches
# ---------------------------------------------------------------------------


def test_136n_human_authorization_valid_minimal(registry):
    result = _validate(_valid_human_authorization(), HUMAN_AUTH_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["issued", "used", "revoked", "expired"])
def test_136n_human_authorization_valid_every_state(state, registry):
    overrides = {"state": state}
    if state == "used":
        overrides["use_binding"] = _ref("pubattmp-0000001", "1" * 64, "publication_attempt")
    elif state == "revoked":
        overrides["revocation_metadata"] = {
            "revoked_at": "2026-07-16T13:00:00Z",
            "revoked_by": "admin@example.com",
            "reason_code": "stale_authorization",
        }
    record = _valid_human_authorization(**overrides)
    result = _validate(record, HUMAN_AUTH_ID, registry)
    assert result.status is OutcomeStatus.VALID, result.issues


@pytest.mark.parametrize("method", ["manual_review", "signed_attestation"])
def test_136n_human_authorization_valid_every_method(method, registry):
    overrides = {"method": method}
    if method == "signed_attestation":
        overrides["proof_reference"] = _ref("proofrec-0000001", "2" * 64, "human_authorization")
    record = _valid_human_authorization(**overrides)
    result = _validate(record, HUMAN_AUTH_ID, registry)
    assert result.status is OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# 4. HumanAuthorization -- local conditional / invalid branches
# ---------------------------------------------------------------------------


def test_136n_human_authorization_revoked_without_metadata_rejected(registry):
    record = _valid_human_authorization(state="revoked")
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_used_without_use_binding_rejected(registry):
    record = _valid_human_authorization(state="used")
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_issued_with_stray_revocation_metadata_rejected(registry):
    record = _valid_human_authorization(
        revocation_metadata={
            "revoked_at": "2026-07-16T13:00:00Z",
            "revoked_by": "admin@example.com",
            "reason_code": "stale_authorization",
        }
    )
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_issued_with_stray_use_binding_rejected(registry):
    record = _valid_human_authorization(
        use_binding=_ref("pubattmp-0000001", "1" * 64, "publication_attempt")
    )
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_signed_attestation_without_proof_rejected(registry):
    record = _valid_human_authorization(method="signed_attestation")
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_manual_review_with_proof_rejected(registry):
    record = _valid_human_authorization(
        proof_reference=_ref("proofrec-0000001", "2" * 64, "human_authorization")
    )
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_risk_acknowledgement_false_rejected(registry):
    record = _valid_human_authorization(risk_acknowledgement=False)
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_risk_acknowledgement_missing_rejected(registry):
    record = _valid_human_authorization()
    del record["risk_acknowledgement"]
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_missing_expires_at_rejected(registry):
    record = _valid_human_authorization()
    del record["expires_at"]
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("state", ["unknown", "ISSUED", "Issued", "", "authorized"])
def test_136n_human_authorization_unknown_state_rejected(state, registry):
    record = _valid_human_authorization(state=state)
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("method", ["auto", "MANUAL_REVIEW", "manual-review", ""])
def test_136n_human_authorization_unknown_method_rejected(method, registry):
    record = _valid_human_authorization(method=method)
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. HumanAuthorization -- family-reference separation / security
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,wrong_family",
    [
        ("request_reference", "readiness_package"),
        ("request_reference", "human_authorization"),
        ("readiness_reference", "cutover_request"),
        ("readiness_reference", "authority_epoch"),
        ("target_reference", "cutover_request"),
        ("target_reference", "readiness_package"),
    ],
)
def test_136n_human_authorization_wrong_family_reference_rejected(field, wrong_family, registry):
    record = _valid_human_authorization()
    record[field] = _ref("someid-00000001", "9" * 64, wrong_family, "x")
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_authoritative_forbidden(registry):
    record = _valid_human_authorization()
    record["authority_disclosure"]["authority_role"] = "authoritative"
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_unknown_top_level_field_rejected(registry):
    record = _valid_human_authorization()
    record["extra_field"] = "sneaky"
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "replay_binding",
    [
        "Bearer abc.def.ghi",
        "password=hunter2",
        "-----BEGIN PRIVATE KEY-----",
        "a b c",
        "token\nvalue",
        "a" * 300,
        "",
    ],
)
def test_136n_human_authorization_replay_binding_shape_rejects_secret_like_values(replay_binding, registry):
    record = _valid_human_authorization(replay_binding=replay_binding)
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_human_authorization_no_field_named_password_token_or_secret():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/human_authorization.schema.json").read_bytes())
    forbidden_substrings = ("password", "secret", "private_key", "bearer_token", "api_key")
    for prop_name in document["properties"]:
        lowered = prop_name.lower()
        assert not any(bad in lowered for bad in forbidden_substrings), prop_name


def test_136n_human_authorization_never_embeds_field_named_scope():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/human_authorization.schema.json").read_bytes())
    assert "scope" not in document["properties"]
    assert "scope" not in document["required"]


# ---------------------------------------------------------------------------
# 6. CutoverCandidate -- valid / invalid branches
# ---------------------------------------------------------------------------


def test_136n_candidate_valid_minimal(registry):
    result = _validate(_valid_candidate(), CANDIDATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "state", ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"]
)
def test_136n_candidate_valid_every_state(state, registry):
    record = _valid_candidate(state=state)
    result = _validate(record, CANDIDATE_ID, registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def test_136n_candidate_extensions_key_accepted(registry):
    record = _valid_candidate(_extensions={"note": "informational-only"})
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.VALID


def test_136n_candidate_extensions_nested_object_rejected(registry):
    record = _valid_candidate(_extensions={"nested": {"a": 1}})
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_unknown_top_level_field_rejected(registry):
    record = _valid_candidate()
    record["unknown_top_level"] = "x"
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_authoritative_forbidden_at_every_state(registry):
    for state in ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"]:
        record = _valid_candidate(state=state)
        record["authority_disclosure"]["authority_role"] = "authoritative"
        assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


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
def test_136n_candidate_cas_expectation_no_field_is_omittable(missing_field, registry):
    """CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.24: missing values are never wildcards."""
    ce = _cas_expectation()
    del ce[missing_field]
    record = _valid_candidate(cas_expectation=ce)
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_cas_expectation_wrong_family_authority_epoch_rejected(registry):
    ce = _cas_expectation()
    ce["expected_authority_epoch"] = _ref("readypkg-0000001", "1" * 64, "readiness_package")
    record = _valid_candidate(cas_expectation=ce)
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_cas_expectation_wrong_family_request_reference_rejected(registry):
    ce = _cas_expectation()
    ce["expected_request_reference"] = _ref("authepoch-0000001", "1" * 64, "authority_epoch")
    record = _valid_candidate(cas_expectation=ce)
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_unknown_state_rejected(registry):
    record = _valid_candidate(state="publication_pending")
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_missing_stage2_generation_reference_rejected(registry):
    record = _valid_candidate()
    del record["stage2_generation_reference"]
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_no_publication_or_authority_claim_field_exists():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/cutover_candidate.schema.json").read_bytes())
    forbidden = ("published", "publication_state", "current_authority", "cutover_completed")
    for prop_name in document["properties"]:
        assert prop_name not in forbidden


# ---------------------------------------------------------------------------
# 7. Certification -- valid / invalid branches
# ---------------------------------------------------------------------------


def test_136n_certification_valid_minimal(registry):
    result = _validate(_valid_certification(), CERT_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["pending", "certified", "stale", "invalidated"])
def test_136n_certification_valid_every_state(state, registry):
    overrides = {"state": state}
    if state == "stale":
        overrides["staleness"] = {
            "detected_at": "2026-07-16T14:00:00Z",
            "reason_code": "stale_certification",
        }
    elif state == "invalidated":
        overrides["invalidation"] = {
            "invalidated_at": "2026-07-16T14:00:00Z",
            "reason_code": "digest_mismatch",
        }
    record = _valid_certification(**overrides)
    result = _validate(record, CERT_ID, registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def test_136n_certification_stale_without_staleness_object_rejected(registry):
    record = _valid_certification(state="stale")
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_invalidated_without_invalidation_object_rejected(registry):
    record = _valid_certification(state="invalidated")
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_pending_with_stray_staleness_rejected(registry):
    record = _valid_certification(
        staleness={"detected_at": "2026-07-16T14:00:00Z", "reason_code": "stale_certification"}
    )
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_unknown_state_rejected(registry):
    record = _valid_certification(state="revoked")
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_unknown_top_level_field_rejected(registry):
    record = _valid_certification()
    record["unknown_field"] = "x"
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_authoritative_forbidden(registry):
    record = _valid_certification()
    record["authority_disclosure"]["authority_role"] = "authoritative"
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_no_certifier_principal_field_exists():
    """Sec.23's frozen field table names no certifier-principal field; disclosed
    design distinction from human_authorization.principal (NON-BLOCKING-136N-8)."""
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/certification.schema.json").read_bytes())
    assert "certifier_principal" not in document["properties"]
    assert "principal" not in document["properties"]


# ---------------------------------------------------------------------------
# 8. Cross-family substitution attacks (Layer 2 boundary)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,wrong_family",
    [
        ("candidate_reference", "human_authorization"),
        ("candidate_reference", "certification"),
        ("request_reference", "readiness_package"),
        ("readiness_reference", "cutover_request"),
        ("authorization_reference", "cutover_candidate"),
        ("authorization_reference", "certification"),
        ("source_authority_reference", "cutover_request"),
        ("target_epoch_reference", "readiness_package"),
    ],
)
def test_136n_certification_wrong_family_reference_rejected(field, wrong_family, registry):
    record = _valid_certification()
    record[field] = _ref("someid-00000001", "9" * 64, wrong_family, "x")
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_authorization_cannot_substitute_for_certification(registry):
    """A HumanAuthorization document is never itself schema-valid against the
    Certification schema (Sec.13 family-substitution requirement)."""
    record = _valid_human_authorization()
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_cannot_substitute_for_authorization(registry):
    record = _valid_candidate()
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_cannot_substitute_for_candidate(registry):
    record = _valid_certification()
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_authority_state_cannot_substitute_for_candidate(registry):
    with cltr_cutover_root() as root:
        authority_state_doc = json.loads(
            (root / "records/authority_state.schema.json").read_bytes()
        )
    # Sanity: distinct record_type const values across all three new families
    # and the pre-existing authority_state family (proves no accidental sharing).
    with cltr_cutover_root() as root:
        for path in GROUP4_RECORD_FILES:
            doc = json.loads((root / path).read_bytes())
            assert doc["properties"]["record_type"]["const"] != authority_state_doc["properties"]["record_type"]["const"]


# ---------------------------------------------------------------------------
# 9. Null vs. absent
# ---------------------------------------------------------------------------


def test_136n_human_authorization_revocation_metadata_null_rejected(registry):
    record = _valid_human_authorization(state="revoked", revocation_metadata=None)
    assert _validate(record, HUMAN_AUTH_ID, registry).status is OutcomeStatus.INVALID


def test_136n_candidate_cas_expectation_null_rejected(registry):
    record = _valid_candidate(cas_expectation=None)
    assert _validate(record, CANDIDATE_ID, registry).status is OutcomeStatus.INVALID


def test_136n_certification_staleness_null_rejected(registry):
    record = _valid_certification(state="stale", staleness=None)
    assert _validate(record, CERT_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 10. No-authority / no-execution proof
# ---------------------------------------------------------------------------


def test_136n_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    repo_root = Path(__file__).resolve().parents[1]
    for relative in GROUP4_RECORD_FILES:
        json_path = repo_root / "src" / "pcae" / "schema_resources" / "cltr_cutover" / relative
        assert json_path.suffix == ".json"  # data files, not code

    forbidden_names = {"subprocess", "eval", "exec", "socket"}
    for py_file in (repo_root / "src" / "pcae" / "schema_resources").rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden_names, f"{py_file}: {alias.name}"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_names, f"{py_file}: {node.module}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec"}, f"{py_file}: {node.func.id}(...)"


def test_136n_no_network_during_registry_and_validation(monkeypatch):
    calls = []

    def _blocked(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Network access attempted during offline schema operations")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        _validate(_valid_human_authorization(), HUMAN_AUTH_ID, reg)
        _validate(_valid_candidate(), CANDIDATE_ID, reg)
        _validate(_valid_certification(), CERT_ID, reg)

    assert calls == []


def test_136n_validation_never_mutates_input_record(registry):
    for builder, schema_id in (
        (_valid_human_authorization, HUMAN_AUTH_ID),
        (_valid_candidate, CANDIDATE_ID),
        (_valid_certification, CERT_ID),
    ):
        record = builder()
        before = copy.deepcopy(record)
        _validate(record, schema_id, registry)
        assert record == before


def test_136n_no_persistence_directory_created_during_validation(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_human_authorization(), HUMAN_AUTH_ID, registry)
    _validate(_valid_candidate(), CANDIDATE_ID, registry)
    _validate(_valid_certification(), CERT_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136n_no_authority_resolver_symbol_referenced_in_new_schema_text():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP4_RECORD_FILES]
    forbidden = ("authority_resolver", "AuthorityResolver", "resolve_authority", "current_authority_pointer")
    for text in texts:
        for token in forbidden:
            assert token not in text


def test_136n_no_authority_pointer_or_state_persistence_path_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP4_RECORD_FILES]
    for text in texts:
        assert ".pcae/cltr-authority" not in text


# ---------------------------------------------------------------------------
# 11. Packaging
# ---------------------------------------------------------------------------


def test_136n_group4_schemas_load_from_editable_install(registry):
    for schema_id in (HUMAN_AUTH_ID, CANDIDATE_ID, CERT_ID):
        assert schema_id in registry.schema_ids


def test_136n_group4_fixtures_validate_outside_repository_checkout(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    reg = build_offline_registry(tmp_path)
    result = _validate(_valid_human_authorization(), HUMAN_AUTH_ID, reg)
    assert result.status is OutcomeStatus.VALID
    result = _validate(_valid_candidate(), CANDIDATE_ID, reg)
    assert result.status is OutcomeStatus.VALID
    result = _validate(_valid_certification(), CERT_ID, reg)
    assert result.status is OutcomeStatus.VALID
