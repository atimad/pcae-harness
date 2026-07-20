"""Phase 137K evidence for the TAMPC-001 production Typed Authority Model consumer.

Requirement references point to TAMPC-001
(`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`)
and the Phase 137J implementation plan
(`docs/IMPLEMENTATION_PLAN_TYPED_AUTHORITY_MODEL_CONSUMER.md`). Every
fixture in this module is freshly authored for 137K (TAMPC-REQ-168): none
is copied from `tests/test_typed_authority_inspector_137e.py`, though both
necessarily encode the same frozen Stage 3 schema field shapes.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

import pcae.cltr.authority_inspection as authority_inspection
import pcae.commands.authority_inspect as authority_inspect
from pcae.cltr.authority_inspection import (
    CONSUMER_ID,
    InspectionFailure,
    InspectionObservation,
    REPRESENTATION_ONLY_DISCLOSURE,
    TAMPC_CONTRACT_VERSION,
    inspect_artifact_at_path,
)
from pcae.commands.authority_inspect import run_authority_inspect
from pcae.schema_runtime import DEFAULT_MAX_INPUT_BYTES

REPO_ROOT = Path(__file__).resolve().parents[1]
SID = "https://pcae.local/schemas/cltr_cutover/records/{}.schema.json"


def _sha(fill: str) -> str:
    return (fill * 64)[:64]


def _rref(family: str, rid: str = "ref-0000001") -> dict:
    return {"record_id": rid, "record_digest": _sha("a"), "record_family": family}


def _rref_s(family: str, rid: str = "ref-0000001") -> dict:
    value = _rref(family, rid)
    value.update(schema_id=SID.format(family), schema_version="1.0")
    return value


def _gref() -> dict:
    return {"generation_id": "gen-0000001", "generation_digest": _sha("b")}


def _disclosure(role: str = "derivative") -> dict:
    return {"authority_role": role, "is_authoritative": False, "disclosure_text": "137k fixture"}


def _cas() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _rref("authority_epoch"),
        "expected_authoritative_generation": _gref(),
        "expected_authority_pointer_digest": _sha("c"),
        "expected_authority_state_digest": _sha("d"),
        "expected_migration_epoch": "epoch-137k",
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
        "created_at": "2026-07-20T09:00:00Z",
        "migration_epoch": "epoch-137k",
    }


def _authority_epoch() -> dict:
    v = _envelope("authority_epoch", "k-authepoch-0000001")
    v.update(authority_kind="legacy", activation_state="proposed", predecessor_epoch=None,
              limitations=[], authority_disclosure=_disclosure())
    return v


def _authority_state() -> dict:
    v = _envelope("authority_state", "k-authstate-0000001")
    v.update(transition_id="trans-k-0000001", active_authority_epoch=_rref("authority_epoch"),
              authority_kind="legacy", publication_evidence_reference=_rref("publication_evidence"),
              pointer_digest=_sha("e"), verification_state="verified",
              compatibility_mode="legacy_authoritative", limitations=[], authority_disclosure=_disclosure())
    return v


def _cutover_request() -> dict:
    v = _envelope("cutover_request", "k-cutreq-00000001")
    v.update(phase_id="137K", target="cltr", source_authority="legacy",
              source_epoch=_rref("authority_epoch"), target_epoch=_rref("authority_epoch"),
              evidence_requirements=[], readiness_package_reference=_rref_s("readiness_package"),
              authorization_requirement=True, final_revision="1", state="pending",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _readiness_package() -> dict:
    v = _envelope("readiness_package", "k-readypkg-0000001")
    v.update(phase_id="137K", transition_id="trans-k-0000002", evidence_references=[],
              prerequisite_status="unknown", findings=[], state="unknown",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _human_authorization() -> dict:
    v = _envelope("human_authorization", "k-humanauth-0000001")
    v.update(phase_id="137K", principal="operator@example.com", method="manual_review",
              request_reference=_rref_s("cutover_request"), readiness_reference=_rref_s("readiness_package"),
              target_reference=_rref_s("authority_epoch"), issued_at="2026-07-20T09:00:00Z",
              expires_at="2027-07-20T09:00:00Z", state="issued", replay_binding="bind-137k",
              risk_acknowledgement=True, limitations=[], authority_disclosure=_disclosure())
    return v


def _cutover_candidate() -> dict:
    v = _envelope("cutover_candidate", "k-cutcand-00000001")
    v.update(stage2_generation_reference=_rref("cutover_candidate"), cas_expectation=_cas(),
              state="proposed", limitations=[], authority_disclosure=_disclosure())
    return v


def _certification() -> dict:
    v = _envelope("certification", "k-certif-00000001")
    v.update(phase_id="137K", candidate_reference=_rref_s("cutover_candidate"),
              request_reference=_rref_s("cutover_request"), readiness_reference=_rref_s("readiness_package"),
              authorization_reference=_rref_s("human_authorization"),
              source_authority_reference=_rref("authority_epoch"),
              target_epoch_reference=_rref("authority_epoch"), cas_expectation=_cas(),
              verifier_evidence=[], state="pending", limitations=[], authority_disclosure=_disclosure())
    return v


def _publication_attempt() -> dict:
    v = _envelope("publication_attempt", "k-pubattempt-0000001")
    v.update(transition_id="trans-k-0000003", attempt_id="k-pubattempt-0000002",
              request_reference=_rref_s("cutover_request"), candidate_reference=_rref_s("cutover_candidate"),
              certification_reference=_rref_s("certification"), cas_expectation=_cas(),
              source_authority_reference=_rref("authority_epoch"),
              target_authority_reference=_rref("authority_epoch"), attempt_sequence=1,
              state="not_requested", limitations=[], authority_disclosure=_disclosure())
    return v


def _publication_evidence() -> dict:
    v = _envelope("publication_evidence", "k-pubevid-00000001")
    v.update(transition_id="trans-k-0000004", attempt_reference=_rref_s("publication_attempt"),
              outcome="not_attempted", limitations=[], authority_disclosure=_disclosure())
    return v


def _concurrency_conflict() -> dict:
    v = _envelope("concurrency_conflict", "k-concconf-0000001")
    v.update(actors=["writer-k1", "writer-k2"], requests=[_rref_s("cutover_request")],
              type="dual_writer", winner=None, recovery_requirement="none_required",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _recovery_journal_entry() -> dict:
    v = _envelope("recovery_journal_entry", "k-recjournal-0000001")
    v.update(transition_id="trans-k-0000005", sequence=0, prior_entry_digest=None,
              operation_reference=_rref("recovery_journal_entry"),
              prior_state_reference=_rref("authority_state"), new_state_reference=_rref("authority_state"),
              authority_state_reference=_rref("authority_state"), generation_reference=_gref(),
              external_effect_state="none", retry_replay_classification="original", state="recorded",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _notification_binding() -> dict:
    v = _envelope("notification_authority_binding", "k-notifbind-0000001")
    v.update(authoritative_generation_reference=_gref(), authority_epoch_reference=_rref("authority_epoch"),
              payload_digest=_sha("f"), attempt_identity="k-notifattempt-0000001",
              pfn001_classification="cutover-notification", delivery_state="not_dispatched",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _marker_binding() -> dict:
    v = _envelope("marker_authority_binding", "k-markerbind-0000001")
    v.update(generation_reference=_gref(), state="absent", compatibility_fallback_forbidden=True,
              limitations=[], authority_disclosure=_disclosure())
    return v


def _receipt_binding() -> dict:
    v = _envelope("receipt_authority_binding", "k-receiptbind-0000001")
    v.update(generation_reference=_gref(), receipt_state="absent",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _compatibility_state() -> dict:
    v = _envelope("compatibility_state", "k-compatst-0000001")
    v.update(component="legacy-lifecycle", role="compatibility", allowed_reads=[],
              forbidden_authority_use=True, fallback_disabled=False, mode="legacy_adapter",
              limitations=[], authority_disclosure=_disclosure())
    return v


def _quarantine_record() -> dict:
    v = _envelope("quarantine_record", "k-quarrec-0000001")
    v.update(object_type="generation", object_reference=_rref("cutover_candidate"),
              reason_code="quarantine_required", state="quarantined",
              limitations=[], authority_disclosure=_disclosure("quarantined"))
    return v


FAMILY_FIXTURES = {
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


def _write_fixture(tmp_path: Path, name: str, value: dict) -> Path:
    p = tmp_path / name
    p.write_bytes(_wire_bytes(value))
    return p


# ── TAMPC-REQ-006, 007, 055–057: all sixteen families ────────────────────


@pytest.mark.parametrize("family", sorted(FAMILY_FIXTURES))
def test_all_sixteen_families_inspect_successfully(tmp_path, family):
    wire = FAMILY_FIXTURES[family]()
    path = _write_fixture(tmp_path, f"{family}.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionObservation), outcome
    rendered = outcome.to_dict()
    assert rendered["outcome"] == "inspected"
    assert rendered["record_family"] == family
    assert rendered["record_claims"] == wire
    assert rendered["provenance"]["complete_typed_record_claims"] == wire
    assert rendered["validation"]["schema"]["status"] == "shape_conformant"
    assert rendered["validation"]["model"]["status"] == "constructed_and_losslessly_serialized"
    assert rendered["validation"]["semantic"] == "not_performed"
    assert rendered["validation"]["lifecycle"] == "not_performed"
    assert rendered["validation"]["governance"] == "not_performed"
    assert rendered["disclosure"] == REPRESENTATION_ONLY_DISCLOSURE
    assert rendered["consumer_identity"] == CONSUMER_ID
    assert rendered["tampc_contract_version"] == TAMPC_CONTRACT_VERSION


def test_dispatch_table_has_sixteen_families():
    assert len(authority_inspection._MODEL_BY_FAMILY) == 16
    assert set(authority_inspection._MODEL_BY_FAMILY) == set(FAMILY_FIXTURES)


# ── Malformed-artifact failure category (TAMPC-REQ-039–047) ──────────────


@pytest.mark.parametrize(
    "raw",
    [b"{", b'{"x":1,"x":2}', b"[]", b"not-json", b'"just a string"', b""],
)
def test_malformed_artifacts_fail_closed(tmp_path, raw):
    path = tmp_path / "malformed.json"
    path.write_bytes(raw)
    artifact_bytes = path.read_bytes()
    outcome = inspect_artifact_at_path(path, artifact_bytes=artifact_bytes)
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "malformed_artifact"


def test_duplicate_nested_key_rejected(tmp_path):
    raw = b'{"a": {"x": 1, "x": 2}, "record_type": "authority_epoch"}'
    path = tmp_path / "dup.json"
    path.write_bytes(raw)
    outcome = inspect_artifact_at_path(path, artifact_bytes=raw)
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "malformed_artifact"


# ── Family/version/identity failure categories ────────────────────────────


def test_unknown_record_family(tmp_path):
    wire = _authority_epoch()
    wire["record_type"] = "future_family_not_yet_authorized"
    path = _write_fixture(tmp_path, "unknown.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "unknown_record_family"


def test_missing_record_type(tmp_path):
    wire = _authority_epoch()
    del wire["record_type"]
    path = _write_fixture(tmp_path, "missing_type.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "unknown_record_family"


def test_non_string_record_type(tmp_path):
    wire = _authority_epoch()
    wire["record_type"] = 12345
    path = _write_fixture(tmp_path, "non_string_type.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "unknown_record_family"


def test_unsupported_schema_version(tmp_path):
    wire = _authority_epoch()
    wire["schema_version"] = "9.9"
    path = _write_fixture(tmp_path, "bad_schema_version.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "unsupported_schema_version"


def test_unsupported_model_version(tmp_path):
    wire = _authority_epoch()
    wire["contract_version"] = "9.9"
    path = _write_fixture(tmp_path, "bad_model_version.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "unsupported_model_version"


def test_family_identity_mismatch(tmp_path):
    wire = _authority_epoch()
    wire["schema_id"] = SID.format("authority_state")
    path = _write_fixture(tmp_path, "identity_mismatch.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "family_identity_mismatch"


def test_schema_validation_failed(tmp_path):
    wire = _authority_epoch()
    del wire["authority_kind"]  # required field per shared envelope + record schema
    path = _write_fixture(tmp_path, "schema_invalid.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "schema_validation_failed"


def test_model_validation_failed(tmp_path):
    wire = _authority_epoch()
    wire["activation_state"] = "not-a-real-activation-state-value"
    path = _write_fixture(tmp_path, "model_invalid.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome in {"schema_validation_failed", "model_validation_failed"}


# ── Failure injection (registry/manifest, TAMPC-REQ-048–053) ─────────────


def test_registry_failure_translated(tmp_path, monkeypatch):
    from pcae.schema_runtime import SchemaRegistryError

    def _raise(*a, **k):
        raise SchemaRegistryError("boom")

    monkeypatch.setattr(authority_inspection, "build_offline_registry", _raise)
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "registry_failure.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "registry_failure"
    assert "SchemaRegistryError" not in outcome.message
    assert "boom" not in outcome.message


def test_manifest_failure_translated(tmp_path, monkeypatch):
    from pcae.schema_runtime import ManifestIntegrityError

    def _raise(*a, **k):
        raise ManifestIntegrityError("boom")

    monkeypatch.setattr(authority_inspection, "load_and_verify_manifest", _raise)
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "manifest_failure.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "manifest_failure"
    assert "boom" not in outcome.message


def test_manifest_one_entry_per_family_live():
    """TAMPC-REQ-059 — live manifest must have exactly one entry per family."""
    from pcae.schema_resources import cltr_cutover_root
    from pcae.schema_runtime import build_offline_registry, load_and_verify_manifest
    from pcae.cltr.authority_inspection import MANIFEST_SCHEMA_ID

    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    by_family: dict[str, int] = {}
    for entry in manifest.document["entries"]:
        if entry.get("file_path", "").startswith("records/"):
            by_family[entry["family"]] = by_family.get(entry["family"], 0) + 1
    assert set(by_family) == set(FAMILY_FIXTURES)
    assert all(count == 1 for count in by_family.values())


# ── Immutability (TAMPC-REQ-075–080) ──────────────────────────────────────


def test_observation_ordinary_assignment_blocked(tmp_path):
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "immutable.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionObservation)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.record_family = "tampered"


def test_observation_delattr_blocked(tmp_path):
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "immutable_del.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    with pytest.raises(dataclasses.FrozenInstanceError):
        del outcome.record_family


def test_failure_ordinary_assignment_blocked(tmp_path):
    path = tmp_path / "missing.json"
    outcome = inspect_artifact_at_path(path, artifact_bytes=b"not-json")
    assert isinstance(outcome, InspectionFailure)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.outcome = "tampered"


def test_returned_nested_values_are_defensive_copies(tmp_path):
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "defensive.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    first = outcome.to_dict()["record_claims"]
    first["record_family_injected"] = "tampered"
    second = outcome.to_dict()["record_claims"]
    assert "record_family_injected" not in second


# ── Authority-neutral disclosure (TAMPC-REQ-146–147) ──────────────────────


def test_forged_operative_claims_are_never_authority_signals(tmp_path):
    wire = _human_authorization()
    wire["state"] = "issued"  # already a plausible-sounding operative value
    path = _write_fixture(tmp_path, "forged.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionObservation)
    rendered = outcome.to_dict()
    assert rendered["disclosure"] == REPRESENTATION_ONLY_DISCLOSURE
    forbidden_top_level = {"approved", "authoritative", "ready", "active", "executable", "complete"}
    assert forbidden_top_level.isdisjoint(rendered)


# ── Determinism (TAMPC-REQ-117–120) ───────────────────────────────────────


def test_repeated_invocation_identical_output(tmp_path):
    wire = _certification()
    path = _write_fixture(tmp_path, "det.json", wire)
    data = path.read_bytes()
    first = inspect_artifact_at_path(path, artifact_bytes=data)
    second = inspect_artifact_at_path(path, artifact_bytes=data)
    assert first == second
    assert first.to_canonical_bytes() == second.to_canonical_bytes()


def test_two_paths_same_content_identical_except_identity(tmp_path):
    wire = _certification()
    path_a = _write_fixture(tmp_path, "det_a.json", wire)
    path_b = _write_fixture(tmp_path, "det_b.json", wire)
    a = inspect_artifact_at_path(path_a, artifact_bytes=path_a.read_bytes()).to_dict()
    b = inspect_artifact_at_path(path_b, artifact_bytes=path_b.read_bytes()).to_dict()
    a.pop("source_artifact_identity")
    b.pop("source_artifact_identity")
    a["provenance"].pop("origin")
    b["provenance"].pop("origin")
    assert a == b


# ── Provenance field presence (TAMPC-REQ-084–086) ─────────────────────────


def test_provenance_fields_present(tmp_path):
    wire = _readiness_package()
    path = _write_fixture(tmp_path, "prov.json", wire)
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    prov = outcome.to_dict()["provenance"]
    for field in (
        "origin",
        "record_identity",
        "record_family",
        "schema_identity",
        "schema_version",
        "model_version",
        "declared_record_digest",
        "derived_input_digest",
        "copied_provenance_values",
        "complete_typed_record_claims",
        "derivation",
        "authority_neutrality",
    ):
        assert field in prov, field


def test_input_digest_is_sha256_of_exact_bytes(tmp_path):
    import hashlib

    wire = _readiness_package()
    path = _write_fixture(tmp_path, "digest.json", wire)
    data = path.read_bytes()
    outcome = inspect_artifact_at_path(path, artifact_bytes=data)
    assert outcome.input_digest == hashlib.sha256(data).hexdigest()
    # declared_record_digest is a distinct, never-cross-checked field.
    assert outcome.declared_record_digest == wire["record_digest"]


# ── CLI layer: Stage 1 bounded read (TAMPC-REQ-029–038) ───────────────────


def test_cli_missing_path(tmp_path):
    args = _ns(path=str(tmp_path / "nope.json"), json=False)
    rc = run_authority_inspect(args)
    assert rc == 1


def test_cli_directory_path(tmp_path):
    args = _ns(path=str(tmp_path), json=False)
    rc = run_authority_inspect(args)
    assert rc == 1


def test_cli_empty_file(tmp_path):
    p = tmp_path / "empty.json"
    p.write_bytes(b"")
    args = _ns(path=str(p), json=False)
    rc = run_authority_inspect(args)
    assert rc == 1


def test_cli_oversized_file(tmp_path):
    p = tmp_path / "oversized.json"
    with open(p, "wb") as fh:
        fh.seek(DEFAULT_MAX_INPUT_BYTES + 1)
        fh.write(b"0")
    args = _ns(path=str(p), json=False)
    rc = run_authority_inspect(args)
    assert rc == 1


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions only")
def test_cli_unreadable_file(tmp_path):
    p = tmp_path / "unreadable.json"
    p.write_bytes(_wire_bytes(_authority_epoch()))
    p.chmod(0)
    try:
        if os.access(p, os.R_OK):
            pytest.skip("running as a user that bypasses file permissions")
        args = _ns(path=str(p), json=False)
        rc = run_authority_inspect(args)
        assert rc == 1
    finally:
        p.chmod(stat.S_IRUSR | stat.S_IWUSR)


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlinks only")
def test_cli_symlink_to_missing(tmp_path):
    link = tmp_path / "dangling.json"
    link.symlink_to(tmp_path / "does_not_exist.json")
    args = _ns(path=str(link), json=False)
    rc = run_authority_inspect(args)
    assert rc == 1


def test_cli_valid_artifact_exit_zero_and_toctou_no_reread(tmp_path):
    p = tmp_path / "valid.json"
    p.write_bytes(_wire_bytes(_authority_epoch()))
    args = _ns(path=str(p), json=True)
    rc = run_authority_inspect(args)
    assert rc == 0


def _ns(**kwargs):
    import argparse

    return argparse.Namespace(**kwargs)


# ── CLI: rendering / exit codes / registration ────────────────────────────


def test_cli_json_output_is_sorted_and_indented(tmp_path, capsys):
    p = tmp_path / "valid.json"
    p.write_bytes(_wire_bytes(_authority_epoch()))
    run_authority_inspect(_ns(path=str(p), json=True))
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["outcome"] == "inspected"
    reserialized = json.dumps(payload, indent=2, sort_keys=True, default=str)
    assert out.strip() == reserialized.strip()


def test_cli_human_output_has_disclosure_first_and_fixed_fields(tmp_path, capsys):
    p = tmp_path / "valid.json"
    p.write_bytes(_wire_bytes(_authority_epoch()))
    run_authority_inspect(_ns(path=str(p), json=False))
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0] == authority_inspect._DISCLOSURE_LINE
    assert any(line.strip().startswith("outcome:") for line in lines)


def test_cli_exit_1_on_failure(tmp_path, capsys):
    p = tmp_path / "malformed.json"
    p.write_bytes(b"not-json")
    rc = run_authority_inspect(_ns(path=str(p), json=False))
    assert rc == 1


def test_cli_registration_help(capsys):
    proc = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "--help"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0
    assert "inspect" in proc.stdout


def test_cli_registration_inspect_help():
    proc = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "inspect", "--help"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0
    assert "--json" in proc.stdout
    assert "path" in proc.stdout


def test_cli_missing_path_argument_is_argparse_usage_error():
    proc = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "inspect"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 2


def test_cli_unknown_authority_subcommand_rejected():
    proc = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "not-a-real-subcommand"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 2


def test_cli_full_invocation_success_and_failure(tmp_path):
    valid = tmp_path / "valid.json"
    valid.write_bytes(_wire_bytes(_authority_epoch()))
    proc_ok = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "inspect", str(valid)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc_ok.returncode == 0
    assert "inspected" in proc_ok.stdout

    missing = tmp_path / "missing.json"
    proc_fail = subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "inspect", str(missing)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert proc_fail.returncode == 1
    assert "input_not_found" in proc_fail.stdout


# ── Package/import boundary (TAMPC-REQ-009–012, 024–028, 140–145) ─────────

_FORBIDDEN_IMPORT_PREFIXES = (
    "pcae.core.tasks",
    "pcae.core.session",
    "pcae.commands.session",
    "pcae.commands.phase_reports",
    "pcae.commands.notify",
    "pcae.commands.phase",
    "pcae.runtime_introspection",
    "pcae.runtime_snapshot",
    "pcae.runtime_registry",
    "pcae.permission_broker",
)


def _imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize(
    "path",
    [
        REPO_ROOT / "src/pcae/cltr/authority_inspection.py",
        REPO_ROOT / "src/pcae/commands/authority_inspect.py",
    ],
)
def test_no_forbidden_imports(path):
    imported = _imported_module_names(path)
    for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
        for name in imported:
            assert not name.startswith(forbidden), f"{path.name} imports forbidden module {name}"


def test_public_api_surface_exact():
    assert set(authority_inspection.__all__) == {
        "CONSUMER_ID",
        "FAILURE_IDENTIFIERS",
        "InspectionFailure",
        "InspectionObservation",
        "InspectionOutcome",
        "MANIFEST_SCHEMA_ID",
        "REPRESENTATION_ONLY_DISCLOSURE",
        "SUPPORTED_MODEL_VERSION",
        "SUPPORTED_SCHEMA_VERSION",
        "TAMPC_CONTRACT_VERSION",
        "UNAVAILABLE",
        "inspect_artifact_at_path",
    }


# ── Lifecycle/runtime neutrality (TAMPC-REQ-140–145) ───────────────────────


def test_lifecycle_and_runtime_surfaces_unchanged_before_after():
    before_health = subprocess.run(
        [sys.executable, "-m", "pcae", "health"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    # Invoke the new command in between.
    subprocess.run(
        [sys.executable, "-m", "pcae", "authority", "inspect", "--help"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    after_health = subprocess.run(
        [sys.executable, "-m", "pcae", "health"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert before_health.returncode == after_health.returncode


# ── Side-effect boundary (TAMPC-REQ-123–124) ───────────────────────────────


def test_no_side_effect_files_written(tmp_path):
    wire = _authority_epoch()
    path = _write_fixture(tmp_path, "no_side_effect.json", wire)
    before = set(tmp_path.iterdir())
    inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    after = set(tmp_path.iterdir())
    assert before == after
