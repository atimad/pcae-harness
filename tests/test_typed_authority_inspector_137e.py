"""Phase 137E evidence for the TAMP-001 explicit-artifact inspector.

Requirement references point to TAMC-001; this module does not restate or
replace that contract.  The fixtures cover all sixteen frozen Stage 3 record
families through the one prototype consumer operation.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from pcae.cltr.authority.errors import TypedModelConstructionError
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import ManifestIntegrityError, SchemaRegistryError
from prototypes.typed_authority_inspector import (
    ExplicitArtifactContext,
    InspectionFailure,
    InspectionSuccess,
    REPRESENTATION_ONLY_DISCLOSURE,
    inspect_explicit_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = REPO_ROOT / "prototypes/typed_authority_inspector.py"
SID = "https://pcae.local/schemas/cltr_cutover/records/{}.schema.json"


def _sha(fill: str) -> str:
    return (fill * 64)[:64]


def _rref(family: str, rid: str = "ref-0000001", *, with_schema: bool = False) -> dict:
    value = {"record_id": rid, "record_digest": _sha("1"), "record_family": family}
    if with_schema:
        value.update(schema_id=SID.format(family), schema_version="1.0")
    return value


def _gref() -> dict:
    return {"generation_id": "gen-0000001", "generation_digest": _sha("2")}


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "fixture claim only",
    }


def _cas() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _rref("authority_epoch"),
        "expected_authoritative_generation": _gref(),
        "expected_authority_pointer_digest": _sha("3"),
        "expected_authority_state_digest": _sha("4"),
        "expected_migration_epoch": "epoch-001",
        "expected_source_lifecycle_state": "PROPOSED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _rref("cutover_request"),
        "expected_certification_reference": _rref("certification"),
    }


def _envelope(family: str, record_id: str) -> dict:
    return {
        "schema_id": SID.format(family),
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": family,
        "record_id": record_id,
        "record_digest": _sha("0"),
        "created_at": "2026-07-19T12:00:00Z",
        "migration_epoch": "epoch-001",
    }


def _authority_epoch() -> dict:
    value = _envelope("authority_epoch", "authepoch-0000001")
    value.update(authority_kind="legacy", activation_state="proposed", predecessor_epoch=None,
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _authority_state() -> dict:
    value = _envelope("authority_state", "authstate-0000001")
    value.update(transition_id="trans-0000001", active_authority_epoch=_rref("authority_epoch"),
                 authority_kind="legacy", publication_evidence_reference=_rref("publication_evidence"),
                 pointer_digest=_sha("5"), verification_state="verified",
                 compatibility_mode="legacy_authoritative", limitations=[], authority_disclosure=_disclosure())
    return value


def _cutover_request() -> dict:
    value = _envelope("cutover_request", "cutreq-00000001")
    value.update(phase_id="137E", target="cltr", source_authority="legacy",
                 source_epoch=_rref("authority_epoch"), target_epoch=_rref("authority_epoch"),
                 evidence_requirements=[], readiness_package_reference=_rref("readiness_package", with_schema=True),
                 authorization_requirement=True, final_revision="1", state="pending",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _readiness_package() -> dict:
    value = _envelope("readiness_package", "readypkg-0000001")
    value.update(phase_id="137E", transition_id="trans-0000002", evidence_references=[],
                 prerequisite_status="unknown", findings=[], state="unknown",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _human_authorization() -> dict:
    value = _envelope("human_authorization", "humanauth-0000001")
    value.update(phase_id="137E", principal="operator@example.com", method="manual_review",
                 request_reference=_rref("cutover_request", with_schema=True),
                 readiness_reference=_rref("readiness_package", with_schema=True),
                 target_reference=_rref("authority_epoch", with_schema=True),
                 issued_at="2026-07-19T12:00:00Z", expires_at="2027-07-19T12:00:00Z",
                 state="issued", replay_binding="bind-1", risk_acknowledgement=True,
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _cutover_candidate() -> dict:
    value = _envelope("cutover_candidate", "cutcand-00000001")
    value.update(stage2_generation_reference=_rref("cutover_candidate"), cas_expectation=_cas(),
                 state="proposed", limitations=[], authority_disclosure=_disclosure())
    return value


def _certification() -> dict:
    value = _envelope("certification", "certif-00000001")
    value.update(phase_id="137E", candidate_reference=_rref("cutover_candidate", with_schema=True),
                 request_reference=_rref("cutover_request", with_schema=True),
                 readiness_reference=_rref("readiness_package", with_schema=True),
                 authorization_reference=_rref("human_authorization", with_schema=True),
                 source_authority_reference=_rref("authority_epoch"),
                 target_epoch_reference=_rref("authority_epoch"), cas_expectation=_cas(),
                 verifier_evidence=[], state="pending", limitations=[], authority_disclosure=_disclosure())
    return value


def _publication_attempt() -> dict:
    value = _envelope("publication_attempt", "pubattempt-0000001")
    value.update(transition_id="trans-0000003", attempt_id="pubattempt-0000002",
                 request_reference=_rref("cutover_request", with_schema=True),
                 candidate_reference=_rref("cutover_candidate", with_schema=True),
                 certification_reference=_rref("certification", with_schema=True), cas_expectation=_cas(),
                 source_authority_reference=_rref("authority_epoch"),
                 target_authority_reference=_rref("authority_epoch"), attempt_sequence=1,
                 state="not_requested", limitations=[], authority_disclosure=_disclosure())
    return value


def _publication_evidence() -> dict:
    value = _envelope("publication_evidence", "pubevid-00000001")
    value.update(transition_id="trans-0000004",
                 attempt_reference=_rref("publication_attempt", with_schema=True),
                 outcome="not_attempted", limitations=[], authority_disclosure=_disclosure())
    return value


def _concurrency_conflict() -> dict:
    value = _envelope("concurrency_conflict", "concconf-0000001")
    value.update(actors=["writer-a", "writer-b"],
                 requests=[_rref("cutover_request", with_schema=True)], type="dual_writer",
                 winner=None, recovery_requirement="none_required",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _recovery_journal_entry() -> dict:
    value = _envelope("recovery_journal_entry", "recjournal-0000001")
    value.update(transition_id="trans-0000005", sequence=0, prior_entry_digest=None,
                 operation_reference=_rref("recovery_journal_entry"),
                 prior_state_reference=_rref("authority_state"), new_state_reference=_rref("authority_state"),
                 authority_state_reference=_rref("authority_state"), generation_reference=_gref(),
                 external_effect_state="none", retry_replay_classification="original", state="recorded",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _notification_binding() -> dict:
    value = _envelope("notification_authority_binding", "notifbind-0000001")
    value.update(authoritative_generation_reference=_gref(), authority_epoch_reference=_rref("authority_epoch"),
                 payload_digest=_sha("6"), attempt_identity="notifattempt-0000001",
                 pfn001_classification="cutover-notification", delivery_state="not_dispatched",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _marker_binding() -> dict:
    value = _envelope("marker_authority_binding", "markerbind-0000001")
    value.update(generation_reference=_gref(), state="absent", compatibility_fallback_forbidden=True,
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _receipt_binding() -> dict:
    value = _envelope("receipt_authority_binding", "receiptbind-0000001")
    value.update(generation_reference=_gref(), receipt_state="absent",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _compatibility_state() -> dict:
    value = _envelope("compatibility_state", "compatst-0000001")
    value.update(component="legacy-lifecycle", role="compatibility", allowed_reads=[],
                 forbidden_authority_use=True, fallback_disabled=False, mode="legacy_adapter",
                 limitations=[], authority_disclosure=_disclosure())
    return value


def _quarantine_record() -> dict:
    value = _envelope("quarantine_record", "quarrec-0000001")
    value.update(object_type="generation", object_reference=_rref("cutover_candidate"),
                 reason_code="quarantine_required", state="quarantined",
                 limitations=[], authority_disclosure=_disclosure("quarantined"))
    return value


WIRE_BUILDERS = {
    "authority_epoch": _authority_epoch,
    "authority_state": _authority_state,
    "certification": _certification,
    "compatibility_state": _compatibility_state,
    "concurrency_conflict": _concurrency_conflict,
    "cutover_candidate": _cutover_candidate,
    "cutover_request": _cutover_request,
    "human_authorization": _human_authorization,
    "marker_authority_binding": _marker_binding,
    "notification_authority_binding": _notification_binding,
    "publication_attempt": _publication_attempt,
    "publication_evidence": _publication_evidence,
    "quarantine_record": _quarantine_record,
    "readiness_package": _readiness_package,
    "receipt_authority_binding": _receipt_binding,
    "recovery_journal_entry": _recovery_journal_entry,
}


def _wire_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@pytest.fixture
def explicit_context():
    with cltr_cutover_root() as root:
        yield ExplicitArtifactContext(
            source_artifact_identity="fixture:explicit-stage3-record",
            source_location="memory://phase-137e-fixture",
            schema_package_identity="cltr_cutover/CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001/1.0",
            package_root=root,
            manifest_path=root / "manifest.json",
        )


# TAMC-REQ-001–034, 039–045, 056–067, 070–073.
@pytest.mark.parametrize("family", sorted(WIRE_BUILDERS))
def test_137e_all_sixteen_families_inspect_losslessly(family, explicit_context):
    wire = WIRE_BUILDERS[family]()
    result = inspect_explicit_artifact(_wire_bytes(wire), context=explicit_context)
    assert isinstance(result, InspectionSuccess), result
    rendered = result.to_dict()
    assert rendered["outcome"] == "inspected"
    assert rendered["record_family"] == family
    assert rendered["record_claims"] == wire
    assert rendered["provenance"]["complete_typed_record_claims"] == wire
    assert rendered["validation"]["schema"]["status"] == "shape_conformant"
    assert rendered["validation"]["model"]["status"] == "constructed_and_losslessly_serialized"
    assert rendered["validation"]["semantic"] == "not_performed"
    assert rendered["validation"]["lifecycle"] == "not_performed"
    assert rendered["validation"]["governance"] == "not_performed"


# TAMC-REQ-022–032, 042–045, 052–055, 060–064.
def test_137e_replay_is_byte_deterministic_idempotent_and_non_mutating(explicit_context):
    wire = _certification()
    original = copy.deepcopy(wire)
    raw = _wire_bytes(wire)
    package_hashes_before = {
        p.relative_to(explicit_context.package_root): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in explicit_context.package_root.rglob("*") if p.is_file()
    }
    first = inspect_explicit_artifact(raw, context=explicit_context)
    second = inspect_explicit_artifact(raw, context=explicit_context)
    package_hashes_after = {
        p.relative_to(explicit_context.package_root): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in explicit_context.package_root.rglob("*") if p.is_file()
    }
    assert first == second
    assert first.to_canonical_bytes() == second.to_canonical_bytes()
    assert wire == original
    assert raw == _wire_bytes(original)
    assert package_hashes_before == package_hashes_after


# TAMC-REQ-035–038, 046–051, 068–069.
def test_137e_authority_and_lifecycle_looking_claims_never_become_operative(explicit_context):
    wire = _human_authorization()
    result = inspect_explicit_artifact(_wire_bytes(wire), context=explicit_context)
    assert isinstance(result, InspectionSuccess)
    output = result.to_dict()
    assert output["record_claims"]["state"] == "issued"
    assert output["disclosure"] == REPRESENTATION_ONLY_DISCLOSURE
    assert output["provenance"]["authority_neutrality"] == REPRESENTATION_ONLY_DISCLOSURE
    forbidden_top_level = {"approved", "authoritative", "ready", "active", "executable", "complete"}
    assert forbidden_top_level.isdisjoint(output)


@pytest.mark.parametrize("raw", [b"{", b'{"x":1,"x":2}', b"[]", b"not-json"])
def test_137e_malformed_artifacts_fail_closed_and_repeatably(raw, explicit_context):
    first = inspect_explicit_artifact(raw, context=explicit_context)
    second = inspect_explicit_artifact(raw, context=explicit_context)
    assert isinstance(first, InspectionFailure)
    assert first.outcome == "malformed_artifact"
    assert first == second


def test_137e_unknown_family_has_no_fallback(explicit_context):
    wire = _authority_epoch()
    wire["record_type"] = "future_family"
    wire["schema_id"] = SID.format("future_family")
    result = inspect_explicit_artifact(_wire_bytes(wire), context=explicit_context)
    assert isinstance(result, InspectionFailure)
    assert result.outcome == "unknown_record_family"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [("schema_version", "2.0", "unsupported_schema_version"),
     ("contract_version", "2.0", "unsupported_model_version")],
)
def test_137e_unsupported_versions_are_not_coerced(field, value, expected, explicit_context):
    wire = _authority_epoch()
    wire[field] = value
    result = inspect_explicit_artifact(_wire_bytes(wire), context=explicit_context)
    assert isinstance(result, InspectionFailure)
    assert result.outcome == expected


def test_137e_invalid_explicit_provenance_fails_before_consumption(explicit_context):
    bad_context = dataclasses.replace(explicit_context, source_artifact_identity="")
    result = inspect_explicit_artifact(_wire_bytes(_authority_epoch()), context=bad_context)
    assert isinstance(result, InspectionFailure)
    assert result.outcome == "required_provenance_failed"


def test_137e_schema_validation_failure_is_distinct(explicit_context):
    wire = _authority_epoch()
    wire["activation_state"] = "invented-state"
    result = inspect_explicit_artifact(_wire_bytes(wire), context=explicit_context)
    assert isinstance(result, InspectionFailure)
    assert result.outcome == "schema_validation_failed"


def test_137e_model_validation_failure_is_distinct(monkeypatch, explicit_context):
    import prototypes.typed_authority_inspector as prototype

    class RejectingModel:
        @classmethod
        def from_dict(cls, payload, *, schema_version):
            raise TypedModelConstructionError("fixture rejection")

    monkeypatch.setitem(prototype._MODEL_BY_FAMILY, "authority_epoch", RejectingModel)
    result = inspect_explicit_artifact(_wire_bytes(_authority_epoch()), context=explicit_context)
    assert isinstance(result, InspectionFailure)
    assert result.outcome == "model_validation_failed"
    assert "fixture rejection" not in result.message


def test_137e_registry_failure_is_sanitized(monkeypatch, explicit_context):
    import prototypes.typed_authority_inspector as prototype

    def fail_registry(*args, **kwargs):
        raise SchemaRegistryError("/ambient/secret/path")

    monkeypatch.setattr(prototype, "build_offline_registry", fail_registry)
    result = inspect_explicit_artifact(_wire_bytes(_authority_epoch()), context=explicit_context)
    assert result.outcome == "registry_failure"
    assert "/ambient/secret/path" not in result.message


def test_137e_manifest_failure_is_sanitized(monkeypatch, explicit_context):
    import prototypes.typed_authority_inspector as prototype

    def fail_manifest(*args, **kwargs):
        raise ManifestIntegrityError("/ambient/secret/path")

    monkeypatch.setattr(prototype, "load_and_verify_manifest", fail_manifest)
    result = inspect_explicit_artifact(_wire_bytes(_authority_epoch()), context=explicit_context)
    assert result.outcome == "manifest_failure"
    assert "/ambient/secret/path" not in result.message


def test_137e_source_digest_and_all_structural_provenance_are_preserved(explicit_context):
    wire = _certification()
    raw = _wire_bytes(wire)
    result = inspect_explicit_artifact(raw, context=explicit_context)
    output = result.to_dict()
    assert output["input_digest"] == hashlib.sha256(raw).hexdigest()
    assert output["declared_record_digest"] == wire["record_digest"]
    assert output["record_identity"] == wire["record_id"]
    assert output["schema_version"] == wire["schema_version"]
    assert output["model_version"] == wire["contract_version"]
    copied = output["provenance"]["copied_provenance_values"]
    paths = {item["instance_path"] for item in copied}
    assert "/candidate_reference" in paths
    assert "/limitations" in paths
    assert "/authority_disclosure" in paths


def test_137e_result_nested_content_is_defensively_copied(explicit_context):
    result = inspect_explicit_artifact(_wire_bytes(_authority_epoch()), context=explicit_context)
    first = result.to_dict()
    first["record_claims"]["record_id"] = "mutated"
    second = result.to_dict()
    assert second["record_claims"]["record_id"] == "authepoch-0000001"


# TAMC-REQ-046–051 and 068–073: static reachability/import isolation evidence.
def test_137e_prototype_has_no_runtime_lifecycle_execution_or_side_effect_imports():
    tree = ast.parse(PROTOTYPE_PATH.read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_fragments = {
        "pcae.commands", "pcae.core.runtime", "pcae.runtime", "lifecycle",
        "phase_reports", "pcae.core.tasks", "pcae.core.session", "subprocess",
        "socket", "urllib", "requests", "http",
    }
    assert not {name for name in imported if any(fragment in name for fragment in forbidden_fragments)}


def test_137e_no_production_module_imports_or_registers_the_prototype():
    offenders = []
    for path in (REPO_ROOT / "src/pcae").rglob("*.py"):
        if path == PROTOTYPE_PATH:
            continue
        text = path.read_text()
        if "typed_authority_inspector" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


def test_137e_dispatch_is_exactly_the_frozen_sixteen_family_inventory():
    import prototypes.typed_authority_inspector as prototype

    assert set(prototype._MODEL_BY_FAMILY) == set(WIRE_BUILDERS)
    assert len(prototype._MODEL_BY_FAMILY) == 16
