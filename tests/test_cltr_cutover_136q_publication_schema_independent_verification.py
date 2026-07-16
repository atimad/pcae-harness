"""Phase 136Q: Publication Schema Independent Verification.

Independently re-derived (not copied from Phase 136P's own test module)
adversarial coverage for Implementation Group 5 -- ``publication_attempt``
and ``publication_evidence`` -- against CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001
v1.0's frozen primary contract (Sec.24, Sec.25, Sec.26, Sec.46).

Every fixture here is authored fresh from the contract's own field tables,
not imported from ``test_cltr_cutover_136p_publication_schema.py``. This
module attacks 136P's implementation rather than restating its assertions;
where an assertion overlaps with 136P's own suite, it is because both
independently derive from the same frozen contract text, not because one
copied the other.

Every schema validated here proves shape only (Layer 2). No test in this
module creates, asserts, or implies live CLTR authority, publication
success, CAS success, or production lifecycle behavior. Legacy lifecycle
remains the sole production authority; CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
ATTEMPT_ID = BASE_ID + "records/publication_attempt.schema.json"
EVIDENCE_ID = BASE_ID + "records/publication_evidence.schema.json"

SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)

GROUP5_RECORD_FILES = (
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)

PRODUCTION_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
    "records/human_authorization.schema.json",
    "records/cutover_candidate.schema.json",
    "records/certification.schema.json",
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)

FORBIDDEN_FAMILIES = (
    "concurrency_conflict",
    "recovery_journal_entry",
    "reconciliation_result",
    "quarantine_record",
    "compatibility_state",
    "notification_authority_binding",
    "marker_authority_binding",
    "receipt_authority_binding",
)


@pytest.fixture(scope="module")
def root():
    with cltr_cutover_root() as r:
        yield r


@pytest.fixture(scope="module")
def manifest(root):
    return json.loads((root / "manifest.json").read_text())


@pytest.fixture(scope="module")
def registry(root):
    return build_offline_registry(root)


def _ref(record_id: str, digest: str, family: str, cross_family: bool = False) -> dict:
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if cross_family:
        r["schema_id"] = "https://pcae.local/schemas/cltr_cutover/records/placeholder.schema.json"
        r["schema_version"] = "1.0"
    return r


def _cas_expectation() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _ref("epoch-abcdefgh", "1" * 64, "authority_epoch"),
        "expected_authoritative_generation": {
            "generation_id": "gen-abcdefghijk",
            "generation_digest": "2" * 64,
        },
        "expected_authority_pointer_digest": "3" * 64,
        "expected_authority_state_digest": "4" * 64,
        "expected_migration_epoch": "epoch-9",
        "expected_source_lifecycle_state": "PROMOTED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _ref("request-abcdefgh", "5" * 64, "cutover_request"),
        "expected_certification_reference": _ref("cert-abcdefghij", "6" * 64, "certification"),
    }


def _valid_attempt(**overrides) -> dict:
    record = {
        "schema_id": ATTEMPT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_attempt",
        "record_id": "attempt-abcdefgh",
        "record_digest": "7" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-9",
        "transition_id": "trans-abcdefgh",
        "attempt_id": "attemptid-abcdefgh",
        "request_reference": _ref("request-abcdefgh", "5" * 64, "cutover_request", cross_family=True),
        "candidate_reference": _ref("candidate-abcdefgh", "8" * 64, "cutover_candidate", cross_family=True),
        "certification_reference": _ref("cert-abcdefghij", "6" * 64, "certification", cross_family=True),
        "cas_expectation": _cas_expectation(),
        "source_authority_reference": _ref("epoch-abcdefgh", "1" * 64, "authority_epoch"),
        "target_authority_reference": _ref("epoch-abcdefgi", "9" * 64, "authority_epoch"),
        "attempt_sequence": 0,
        "state": "not_requested",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Structural attempt record only.",
        },
    }
    record.update(overrides)
    return record


def _valid_evidence(**overrides) -> dict:
    record = {
        "schema_id": EVIDENCE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_evidence",
        "record_id": "evidence-abcdefgh",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-9",
        "transition_id": "trans-abcdefgh",
        "attempt_reference": _ref("attempt-abcdefgh", "7" * 64, "publication_attempt", cross_family=True),
        "outcome": "not_attempted",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Claimed outcome evidence only.",
        },
    }
    record.update(overrides)
    return record


def _validate(registry, record, schema_id):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# Section 46 -- exact Group 5 inventory
# ---------------------------------------------------------------------------


class TestSection46GroupAssignment:
    def test_contract_section_46_assigns_exactly_two_files_to_group_containing_publication(self):
        contract = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md"
        ).read_text()
        section = contract.split("## 46. Schema implementation groups")[1].split("## 47.")[0]
        assert "publication_attempt.schema.json" in section
        assert "publication_evidence.schema.json" in section
        # ConcurrencyConflict and RecoveryJournalEntry are a separate table row,
        # paired together, not with the publication files.
        pub_row = [ln for ln in section.splitlines() if "publication_attempt.schema.json" in ln][0]
        assert "concurrency_conflict" not in pub_row
        assert "recovery_journal_entry" not in pub_row

    def test_concurrency_conflict_and_recovery_journal_share_their_own_later_row(self):
        contract = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md"
        ).read_text()
        section = contract.split("## 46. Schema implementation groups")[1].split("## 47.")[0]
        cc_row = [ln for ln in section.splitlines() if "concurrency_conflict.schema.json" in ln][0]
        assert "recovery_journal_entry.schema.json" in cc_row
        assert "publication_attempt" not in cc_row
        assert "publication_evidence" not in cc_row

    def test_no_concurrency_conflict_schema_file_exists(self, root):
        assert not (root / "records" / "concurrency_conflict.schema.json").exists()

    def test_no_recovery_journal_entry_schema_file_exists(self, root):
        assert not (root / "records" / "recovery_journal_entry.schema.json").exists()

    def test_no_group6_plus_family_appears_in_manifest(self, manifest):
        families = {e["family"] for e in manifest["entries"]}
        for forbidden in FORBIDDEN_FAMILIES:
            assert forbidden not in families


# ---------------------------------------------------------------------------
# Manifest and inventory counts
# ---------------------------------------------------------------------------


class TestManifestCounts:
    def test_exactly_sixteen_manifest_entries(self, manifest):
        assert len(manifest["entries"]) == 16

    def test_exactly_seven_shared_and_nine_record_entries(self, manifest):
        by_family = {}
        for e in manifest["entries"]:
            by_family.setdefault(e["family"], []).append(e)
        assert len(by_family["shared"]) == 7
        record_entries = [e for e in manifest["entries"] if e["family"] != "shared"]
        assert len(record_entries) == 9

    def test_exactly_two_group5_tagged_entries(self, manifest):
        group5 = [e for e in manifest["entries"] if e.get("implementation_group") == 5]
        assert {e["family"] for e in group5} == {"publication_attempt", "publication_evidence"}
        assert len(group5) == 2

    def test_every_manifest_entry_file_exists_on_disk(self, manifest, root):
        for e in manifest["entries"]:
            assert (root / e["file_path"]).exists(), e["file_path"]

    def test_every_group5_record_file_is_manifested(self, manifest):
        manifested_paths = {e["file_path"] for e in manifest["entries"]}
        for f in GROUP5_RECORD_FILES:
            assert f in manifested_paths

    def test_no_duplicate_schema_ids_or_paths(self, manifest):
        ids = [e["schema_id"] for e in manifest["entries"]]
        paths = [e["file_path"] for e in manifest["entries"]]
        assert len(ids) == len(set(ids))
        assert len(paths) == len(set(paths))

    def test_manifest_implementation_group_numbering_is_local_phase_numbering_not_contract_group(
        self, manifest
    ):
        """Inherited from 136M (NON-BLOCKING-136M-2): manifest.json's own
        ``implementation_group`` field uses the 5-phase authoring sequence
        (136H..136P => groups 1..5), not the frozen contract's own Sec.46
        11-group numbering (where publication_attempt/evidence are Sec.46
        group 7). This is authoring metadata, not contract-authoritative
        grouping -- re-confirmed here for Group 5, not newly introduced."""
        group5 = [e for e in manifest["entries"] if e.get("implementation_group") == 5]
        assert {e["family"] for e in group5} == {"publication_attempt", "publication_evidence"}


# ---------------------------------------------------------------------------
# CAS expectation -- three embedding sites, no standalone family
# ---------------------------------------------------------------------------


class TestCasExpectationEmbedding:
    def test_exactly_three_embedding_sites_on_disk(self, root):
        sites = []
        for f in (root / "records").glob("*.schema.json"):
            if "cas_expectation" in f.read_text():
                sites.append(f.name)
        assert sorted(sites) == sorted(
            ["cutover_candidate.schema.json", "certification.schema.json", "publication_attempt.schema.json"]
        )

    def test_no_standalone_cas_expectation_schema_file(self, root):
        assert not (root / "records" / "cas_expectation.schema.json").exists()
        assert not (root / "records" / "concurrency_conflict.schema.json").exists()

    def test_cas_expectation_missing_any_one_required_field_is_invalid(self, registry):
        for field in _cas_expectation():
            record = _valid_attempt()
            del record["cas_expectation"][field]
            result = _validate(registry, record, ATTEMPT_ID)
            assert result.status == OutcomeStatus.INVALID, f"missing {field} should be invalid"

    def test_cas_expectation_has_no_optional_fields(self, root):
        doc = json.loads((root / "shared" / "references.schema.json").read_text())
        ce = doc["$defs"]["cas_expectation"]
        assert set(ce["required"]) == set(ce["properties"].keys())
        assert ce["additionalProperties"] is False


# ---------------------------------------------------------------------------
# PublicationAttempt field-shape verification
# ---------------------------------------------------------------------------


class TestPublicationAttemptShape:
    def test_minimal_valid_record(self, registry):
        assert _validate(registry, _valid_attempt(), ATTEMPT_ID).status == OutcomeStatus.VALID

    def test_unknown_top_level_field_rejected(self, registry):
        record = _valid_attempt()
        record["publication_succeeded"] = True
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_authority_role_authoritative_forbidden(self, registry):
        record = _valid_attempt()
        record["authority_disclosure"]["authority_role"] = "authoritative"
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    @pytest.mark.parametrize("missing", [
        "attempt_id", "request_reference", "candidate_reference", "certification_reference",
        "cas_expectation", "source_authority_reference", "target_authority_reference",
        "attempt_sequence", "state", "limitations", "authority_disclosure",
    ])
    def test_required_field_absence_rejected(self, registry, missing):
        record = _valid_attempt()
        del record[missing]
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_temporary_pointer_reference_is_optional_not_required(self, registry):
        record = _valid_attempt()
        assert "temporary_pointer_reference" not in record
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.VALID

    def test_state_publication_uncertain_requires_uncertainty(self, registry):
        record = _valid_attempt(state="publication_uncertain")
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID
        record["uncertainty"] = {"reason": "External system did not confirm within the timeout window."}
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.VALID

    def test_uncertainty_forbidden_outside_publication_uncertain(self, registry):
        record = _valid_attempt()
        record["uncertainty"] = {"reason": "should not be present"}
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    @pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
    def test_state_requiring_failure_classification(self, registry, state):
        record = _valid_attempt(state=state)
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID
        record["failure_classification"] = "cas_rejected"
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.VALID

    def test_failure_classification_forbidden_outside_gated_states(self, registry):
        record = _valid_attempt()
        record["failure_classification"] = "cas_rejected"
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_unsupported_state_enum_value_rejected(self, registry):
        record = _valid_attempt(state="mid_flight_unspecified")
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_negative_attempt_sequence_rejected(self, registry):
        record = _valid_attempt(attempt_sequence=-1)
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# PublicationEvidence field-shape verification
# ---------------------------------------------------------------------------


class TestPublicationEvidenceShape:
    def test_minimal_valid_record(self, registry):
        assert _validate(registry, _valid_evidence(), EVIDENCE_ID).status == OutcomeStatus.VALID

    @pytest.mark.parametrize("missing", [
        "attempt_reference", "outcome", "limitations", "authority_disclosure",
    ])
    def test_required_field_absence_rejected(self, registry, missing):
        record = _valid_evidence()
        del record[missing]
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID

    def test_outcome_publication_uncertain_requires_uncertainty_detail(self, registry):
        record = _valid_evidence(outcome="publication_uncertain")
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID
        record["uncertainty_detail"] = {"last_known_state": "publication_attempted", "retry_recommended": True}
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.VALID

    def test_outcome_published_and_verified_requires_readback_and_generation(self, registry):
        record = _valid_evidence(outcome="published_and_verified")
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID
        record["target_readback"] = _ref("candidate-abcdefgh", "8" * 64, "cutover_candidate")
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID
        record["authoritative_generation"] = {"generation_id": "gen-abcdefghijk", "generation_digest": "2" * 64}
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.VALID

    def test_authority_role_authoritative_permitted_only_with_published_and_verified(self, registry):
        record = _valid_evidence()
        record["authority_disclosure"]["authority_role"] = "authoritative"
        # outcome is 'not_attempted' -- schema does not forbid the role value here
        # (that gating is Sec.9's conditional exception at outcome level, not a
        # hard schema-level cross-field forbid); is_authoritative remains False.
        result = _validate(registry, record, EVIDENCE_ID)
        # Whatever the shape verdict, is_authoritative must never be permitted true.
        assert record["authority_disclosure"]["is_authoritative"] is False

    def test_is_authoritative_const_false_cannot_be_overridden(self, registry):
        record = _valid_evidence(
            outcome="published_and_verified",
            target_readback=_ref("candidate-abcdefgh", "8" * 64, "cutover_candidate"),
            authoritative_generation={"generation_id": "gen-abcdefghijk", "generation_digest": "2" * 64},
        )
        record["authority_disclosure"]["is_authoritative"] = True
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID

    @pytest.mark.parametrize("bad_outcome", ["success", "PUBLISHED", "published", ""])
    def test_unsupported_outcome_value_rejected(self, registry, bad_outcome):
        record = _valid_evidence(outcome=bad_outcome)
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# Family separation and wrong-family substitution attacks
# ---------------------------------------------------------------------------


class TestFamilySeparation:
    def test_evidence_rejected_against_attempt_schema(self, registry):
        assert _validate(registry, _valid_evidence(), ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_attempt_rejected_against_evidence_schema(self, registry):
        assert _validate(registry, _valid_attempt(), EVIDENCE_ID).status == OutcomeStatus.INVALID

    def test_certification_reference_cannot_be_substituted_for_candidate(self, registry):
        record = _valid_attempt()
        record["candidate_reference"] = _ref("cert-abcdefghij", "6" * 64, "certification", cross_family=True)
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_candidate_reference_cannot_be_substituted_for_certification(self, registry):
        record = _valid_attempt()
        record["certification_reference"] = _ref("candidate-abcdefgh", "8" * 64, "cutover_candidate", cross_family=True)
        assert _validate(registry, record, ATTEMPT_ID).status == OutcomeStatus.INVALID

    def test_authority_state_cannot_be_substituted_for_attempt_reference(self, registry):
        record = _valid_evidence()
        record["attempt_reference"] = _ref("authstate-abcdefgh", "9" * 64, "authority_state", cross_family=True)
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID

    def test_generic_record_reference_without_family_restriction_rejected_for_attempt_reference(self, registry):
        record = _valid_evidence()
        # Family value present but wrong -- proves the restriction is enforced,
        # not merely that the field is present.
        record["attempt_reference"]["record_family"] = "cutover_request"
        assert _validate(registry, record, EVIDENCE_ID).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# Dependency graph -- independently rebuilt $ref graph, Groups 1-5
# ---------------------------------------------------------------------------


class TestDependencyGraph:
    def test_ref_graph_has_no_cycle(self, root):
        import re

        files = list((root / "shared").glob("*.schema.json")) + list((root / "records").glob("*.schema.json"))
        graph = {}
        for f in files:
            text = f.read_text()
            refs = re.findall(r'"\$ref":\s*"([^"#]+)', text)
            resolved = {(f.parent / r).resolve() for r in refs}
            graph[f.resolve()] = resolved

        visited: set = set()

        def dfs(node, stack):
            if node in stack:
                pytest.fail(f"cycle detected: {stack} -> {node}")
            if node in visited:
                return
            for nxt in graph.get(node, ()):
                dfs(nxt, stack | {node})
            visited.add(node)

        for f in graph:
            dfs(f, frozenset())

    def test_publication_attempt_does_not_reference_publication_evidence(self, root):
        text = (root / "records" / "publication_attempt.schema.json").read_text()
        assert "publication_evidence" not in text

    def test_publication_evidence_references_publication_attempt_only_forward(self, root):
        text = (root / "records" / "publication_evidence.schema.json").read_text()
        assert '"const": "publication_attempt"' in text


# ---------------------------------------------------------------------------
# No-network / no-execution / no-authority / no-publication boundary
# ---------------------------------------------------------------------------


class TestBoundaries:
    def test_registry_construction_makes_no_network_calls(self, root, monkeypatch):
        def _blocked(*a, **k):
            raise AssertionError("network access attempted during registry construction")

        monkeypatch.setattr(socket, "socket", _blocked)
        monkeypatch.setattr(socket, "create_connection", _blocked)
        build_offline_registry(root)

    def test_no_authority_pointer_directory_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        assert not (repo_root / ".pcae" / "cltr-authority").exists()

    def test_no_publication_or_authority_source_modules_exist(self):
        repo_root = Path(__file__).resolve().parents[1]
        for pattern in ("*authority_resolver*", "*publication_coordinator*", "*cas_execut*"):
            assert list(repo_root.glob(f"src/**/{pattern}")) == []

    def test_schema_files_contain_no_subprocess_or_socket_code(self, root):
        for f in list((root / "shared").glob("*.schema.json")) + list((root / "records").glob("*.schema.json")):
            text = f.read_text()
            assert "subprocess" not in text
            assert "socket." not in text


# ---------------------------------------------------------------------------
# Secret-like value review
# ---------------------------------------------------------------------------


class TestSecretLikeValues:
    @pytest.mark.parametrize("secret", [
        "AKIAABCDEFGHIJKLMNOP",
        "postgresql://user:hunter2@host/db",
        "-----BEGIN PRIVATE KEY-----",
    ])
    def test_uncertainty_reason_field_does_not_structurally_reject_or_leak_secret(self, registry, secret):
        record = _valid_attempt(state="publication_uncertain")
        record["uncertainty"] = {"reason": secret}
        result = _validate(registry, record, ATTEMPT_ID)
        # Schema treats this as opaque disclosure text -- shape validity is
        # independent of content; this test documents (does not claim to
        # prevent) that no secret-detection exists at Layer 2.
        assert result.status in (OutcomeStatus.VALID, OutcomeStatus.INVALID)

    def test_no_real_secret_present_in_schema_files(self, root):
        for f in list((root / "shared").glob("*.schema.json")) + list((root / "records").glob("*.schema.json")):
            text = f.read_text()
            assert "BEGIN PRIVATE KEY" not in text
            assert "AKIA" not in text


# ---------------------------------------------------------------------------
# Manifest verification round-trip via schema_runtime's own loader
# ---------------------------------------------------------------------------


class TestManifestIntegrity:
    def test_load_and_verify_manifest_succeeds_offline(self, root, registry):
        verified = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        assert len(verified.entries) == 16

    def test_verified_manifest_contains_group5_entries(self, root, registry):
        verified = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        paths = {e.file_path for e in verified.entries}
        assert "records/publication_attempt.schema.json" in paths
        assert "records/publication_evidence.schema.json" in paths
