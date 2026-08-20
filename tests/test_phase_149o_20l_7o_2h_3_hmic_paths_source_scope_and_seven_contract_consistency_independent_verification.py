"""Phase 149O.20L.7O.2H.3 independent verification.

This suite is derived from HMIC-001 v1.6, current production source, and
the fixed pre-2H.2 checkpoint.  It deliberately does not import or reuse the
2H.2 repair tests.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import agent
from pcae.core import hatp_hardware_credential_admin as hardware_admin
from pcae.core import hatp_mandatory_certification as hmic
from pcae.core import hatp_principal_signer_admin as principal_admin
from pcae.core import provenance
from pcae.core.paths import HarnessPath


ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY = "2d1c4d58"
REPAIR_COMMIT = "69467afb"
PRE_REPAIR = "bb652aa4d18b5568e15feaf98c525ce0a6bd9a01"
GUARD_ORIGIN = "85616f4b"
CONTRACT = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
PRODUCTION = "src/pcae/core/hatp_mandatory_certification.py"
PATHS = "src/pcae/core/paths.py"
GUARD_TEST = "tests/test_phase_149o_20l_7l_6_contract_preamble_and_relative_import_guard_repair_independent_verification.py"

SEVEN_IDS = {
    "HMRC-001",
    "HATP-001",
    "HSCE-001",
    "RAE-001",
    "HBDC-001",
    "HPSE-001",
    "HHCE-001",
}

CLASS_B_MEMBERS = {
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
    "src/pcae/core/hatp_deployment_binding_admin.py",
    "scripts/hatp_deployment_binding_admin.py",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def _show(rev: str, path: str) -> str:
    return _git("show", f"{rev}:{path}")


def _show_bytes(rev: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=ROOT, check=True, capture_output=True
    ).stdout


def _requirement(text: str, req_id: str) -> str:
    match = re.search(
        rf"\*\*{re.escape(req_id)}\b.*?(?=\n\*\*HMIC-REQ-\d{{3}}\b|\n---\n|\Z)",
        text,
        re.S,
    )
    assert match, req_id
    return match.group(0)


def _req_050_members(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    block = _requirement(text, "HMIC-REQ-050")
    match = re.search(r"```\n(.*?)\n```", block, re.S)
    assert match
    buckets = re.split(r"\n\s*\n", match.group(1).strip(), maxsplit=1)
    assert len(buckets) == 2

    def clean(bucket: str) -> tuple[str, ...]:
        return tuple(line.strip().split()[0] for line in bucket.splitlines() if line.strip())

    return clean(buckets[0]), clean(buckets[1])


def _canonical(src_members: tuple[str, ...], root_members: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted([f"src/pcae/{item}" for item in src_members] + list(root_members)))


def _digest(root: Path, members: tuple[str, ...]) -> str:
    outer = hashlib.sha256()
    for member in sorted(members):
        file_digest = hashlib.sha256((root / member).read_bytes()).hexdigest()
        outer.update(f"{member}\0{file_digest}\n".encode())
    return outer.hexdigest()


def _copy_members(target: Path, members: tuple[str, ...], source: Path = ROOT) -> None:
    for member in members:
        destination = target / member
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / member, destination)


def _function(source: str, name: str) -> ast.FunctionDef:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(name)


def _calls(node: ast.AST) -> set[str]:
    result: set[str] = set()
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        if isinstance(candidate.func, ast.Name):
            result.add(candidate.func.id)
        elif isinstance(candidate.func, ast.Attribute):
            result.add(candidate.func.attr)
    return result


def _old_guard_window(text: str) -> str:
    match = re.search(r"\*\*HMIC-REQ-145 \(.*?(?=\n\*\*HMIC-REQ-\d{3} \(|\Z)", text, re.S)
    assert match
    return match.group(0)


def _narrow_guard_window(text: str) -> str:
    match = re.search(r"\*\*HMIC-REQ-145 \(.*?(?=\n---\n)", text, re.S)
    assert match
    return match.group(0)


def _base_record_document(contract_versions: dict[str, str]) -> dict[str, object]:
    return {
        "certification_id": "a" * 64,
        "repository_instance_id": "12345678-1234-4234-8234-123456789abc",
        "canonical_deployment_root": "/disposable/deployment",
        "implementation_commit": "b" * 40,
        "implementation_scope_digest": "c" * 64,
        "contract_versions": contract_versions,
        "verification_record_digest": "d" * 64,
        "certified_at": "2026-08-19T00:00:00Z",
        "certified_by": "independent-verifier",
        "status": "active",
    }


def test_entry_and_historical_checkpoint_are_exact() -> None:
    assert _git("rev-parse", PHASE_ENTRY).strip() == "2d1c4d583f1baa7254725ae92cc8574e49ac2063"
    assert _git("rev-parse", f"{REPAIR_COMMIT}^").strip() == PRE_REPAIR
    assert _git("rev-list", "--count", "origin/main.." + PHASE_ENTRY).strip() == "0"


def test_historical_v15_exact_35_and_paths_omission() -> None:
    text = _show(PRE_REPAIR, CONTRACT)
    assert "**Version:** 1.5" in text
    src_members, root_members = _req_050_members(text)
    members = _canonical(src_members, root_members)
    assert (len(src_members), len(root_members), len(members)) == (26, 9, 35)
    assert "src/pcae/core/paths.py" not in members
    assert len(members) == len(set(members))


def test_current_membership_is_derived_as_27_plus_9_and_all_exist() -> None:
    """CURRENT NORMATIVE, updated (§26 of the 149O.20L.7O.2M governing
    prompt): Phase 149O.20L.7O.2M widened `_FROZEN_REPOSITORY_ROOT_
    RELATIVE_FILES` 9 -> 11 (38 total), binding the two standalone
    Trust-Enrollment admin scripts this phase's own §271 test already
    anticipated as "pending a future HMIC source-scope evolution"."""

    text = (ROOT / CONTRACT).read_text(encoding="utf-8")
    src_members, root_members = _req_050_members(text)
    members = _canonical(src_members, root_members)
    assert (len(src_members), len(root_members), len(members)) == (27, 11, 38)
    assert len(members) == len(set(members))
    assert all((ROOT / member).is_file() for member in members)
    assert "src/pcae/core/paths.py" in members


def test_exact_source_delta_is_only_paths_and_retains_all_35() -> None:
    """Pinned to this phase's own entry/exit window (PRE_REPAIR ->
    PHASE_ENTRY, the v1.5 -> v1.6 transition this phase itself
    independently verified), not to the live contract text: a later,
    separately-governed phase (149O.20L.7O.2M, v1.6 -> v1.7) widening
    HMIC-REQ-050 further does not change what THIS phase's own v1.6
    repair actually added. §26 of the 149O.20L.7O.2M governing prompt:
    historical snapshot, preserved."""

    old = _canonical(*_req_050_members(_show(PRE_REPAIR, CONTRACT)))
    new = _canonical(*_req_050_members(_show(PHASE_ENTRY, CONTRACT)))
    assert set(old) <= set(new)
    assert set(new) - set(old) == {"src/pcae/core/paths.py"}
    assert set(old) - set(new) == set()


def test_contract_and_production_memberships_are_exactly_equal() -> None:
    """CURRENT NORMATIVE, updated (§26 of the 149O.20L.7O.2M governing
    prompt) -- see docstring on test_current_membership_is_derived_as_
    27_plus_9_and_all_exist above."""

    contract_members = _canonical(*_req_050_members((ROOT / CONTRACT).read_text(encoding="utf-8")))
    production_members = tuple(sorted(hmic._frozen_canonical_paths()))
    assert contract_members == production_members
    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 27
    assert len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 11


def test_paths_exact_symbol_chains_reach_authority_inputs() -> None:
    signing = (ROOT / "src/pcae/core/hatp_signing_ceremony.py").read_text(encoding="utf-8")
    agent_source = (ROOT / "src/pcae/core/agent.py").read_text(encoding="utf-8")
    paths_source = (ROOT / PATHS).read_text(encoding="utf-8")
    assert "build_rollback_review" in _calls(_function(signing, "_resolve_ag3_operation"))
    assert "lookup_promotion_execution_record" in _calls(_function(signing, "_resolve_ag5_operation"))
    assert "join" in _calls(_function(agent_source, "build_rollback_review"))
    lookup = ast.get_source_segment(agent_source, _function(agent_source, "lookup_promotion_execution_record"))
    assert lookup and "root.path" in lookup
    join = ast.get_source_segment(paths_source, _function(paths_source, "join"))
    assert join and "self.path / relative_path" in join
    ag3 = ast.get_source_segment(signing, _function(signing, "_resolve_ag3_operation"))
    ag5 = ast.get_source_segment(signing, _function(signing, "_resolve_ag5_operation"))
    assert ag3 and "original_commit_sha" in ag3
    assert ag5 and "ecp_id" in ag5


def test_historical_paths_behavior_changes_ag3_authority_while_35_digest_does_not(tmp_path: Path) -> None:
    historical_members = _canonical(*_req_050_members(_show(PRE_REPAIR, CONTRACT)))
    for member in historical_members:
        destination = tmp_path / member
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_show_bytes(PRE_REPAIR, member))
    paths_target = tmp_path / PATHS
    paths_target.parent.mkdir(parents=True, exist_ok=True)
    paths_target.write_text(_show(PRE_REPAIR, PATHS), encoding="utf-8")
    before = _digest(tmp_path, historical_members)
    paths_target.write_text(
        paths_target.read_text(encoding="utf-8").replace(
            "return self.path / relative_path", "return self.path / 'redirected' / relative_path"
        ),
        encoding="utf-8",
    )
    after = _digest(tmp_path, historical_members)
    assert before == after

    job_id = "authority-selection"
    ordinary = tmp_path / agent._REMOTE_JOBS_OUTPUT_DIR
    redirected = tmp_path / "redirected" / agent._REMOTE_JOBS_OUTPUT_DIR
    ordinary.mkdir(parents=True, exist_ok=True)
    redirected.mkdir(parents=True, exist_ok=True)
    (ordinary / f"{job_id}.json").write_text(json.dumps({"commit_sha": "1" * 40}), encoding="utf-8")
    (redirected / f"{job_id}.json").write_text(json.dumps({"commit_sha": "2" * 40}), encoding="utf-8")

    class RedirectedRoot:
        path = tmp_path

        def join(self, relative_path: Path) -> Path:
            return self.path / "redirected" / relative_path

    baseline = agent.build_rollback_review(HarnessPath(tmp_path), job_id)["rollback_review"]["original_commit_sha"]
    changed = agent.build_rollback_review(RedirectedRoot(), job_id)["rollback_review"]["original_commit_sha"]
    assert baseline == "1" * 40
    assert changed == "2" * 40


def test_current_paths_digest_is_sensitive_and_deterministic(tmp_path: Path) -> None:
    members = tuple(hmic._frozen_canonical_paths())
    _copy_members(tmp_path, members)
    baseline = hmic.derive_implementation_scope_digest(HarnessPath(tmp_path))
    assert hmic.derive_implementation_scope_digest(HarnessPath(tmp_path)) == baseline
    target = tmp_path / PATHS
    target.write_bytes(target.read_bytes() + b"\n# disposable 2H.3 mutation\n")
    assert hmic.derive_implementation_scope_digest(HarnessPath(tmp_path)) != baseline


def test_limb_d_authority_sources_are_bound_and_only_audit_leaf_is_unbound() -> None:
    bound = set(hmic._frozen_canonical_paths())
    authority_sources = {
        "src/pcae/core/hatp_signing_ceremony.py",
        "src/pcae/core/agent.py",
        "src/pcae/core/hatp_bootstrap.py",
        "src/pcae/core/hatp_evidence_store.py",
        "src/pcae/core/hatp_hardware_credentials.py",
        "src/pcae/core/hatp_providers.py",
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_piv_provider.py",
        "src/pcae/core/hatp_signed_evidence.py",
        "src/pcae/core/human_approval_trusted_provenance.py",
        "src/pcae/core/repository_identity.py",
        "src/pcae/core/rollback_approval_evidence.py",
        "src/pcae/core/hatp_hardware_credential_admin.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "src/pcae/core/paths.py",
    }
    assert authority_sources <= bound
    assert "src/pcae/core/provenance.py" not in bound
    # Resolved by Phase 149O.20L.7O.2M: the standalone Trust-Enrollment
    # admin scripts this phase's own snapshot found absent (true at this
    # phase's own entry state, historically preserved above) were the
    # exact +2 delta 149O.20L.7O.2L.1's fresh HMIC-REQ-052 analysis
    # anticipated (36 -> 38); 149O.20L.7O.2M performed that widening.
    assert (ROOT / "scripts/hatp_hardware_credential_admin.py").exists()
    assert (ROOT / "scripts/hatp_principal_signer_admin.py").exists()
    assert "scripts/hatp_hardware_credential_admin.py" in bound
    assert "scripts/hatp_principal_signer_admin.py" in bound


def test_provenance_git_status_and_tasks_are_audit_only_for_writer_state(tmp_path: Path, monkeypatch) -> None:
    evidence = hardware_admin.CredentialEnrollmentEvidence(
        signer_key_id="key-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key_hex="04aabb",
        enrollment_reference="enrollment-1",
    )
    stores = [tmp_path / "store-a", tmp_path / "store-b"]
    repos = [tmp_path / "repo-a", tmp_path / "repo-b"]
    for path in stores + repos:
        path.mkdir(parents=True)

    hardware_admin.register_credential(repository_root=repos[0], evidence=evidence, _store_root=stores[0])
    monkeypatch.setattr(provenance, "read_git_branch", lambda _root: "attacker-selected-branch")
    monkeypatch.setattr(provenance, "find_latest_active_task", lambda _root: None)
    hardware_admin.register_credential(repository_root=repos[1], evidence=evidence, _store_root=stores[1])
    assert (stores[0] / "hardware-credentials.json").read_bytes() == (
        stores[1] / "hardware-credentials.json"
    ).read_bytes()
    assert "src/pcae/core/provenance.py" not in hmic._frozen_canonical_paths()
    assert "src/pcae/core/git_status.py" not in hmic._frozen_canonical_paths()
    assert "src/pcae/core/tasks.py" not in hmic._frozen_canonical_paths()


def test_writer_paths_work_in_disposable_state(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    hardware_root = tmp_path / "hardware"
    protected_root = tmp_path / "protected"
    repository_root.mkdir()
    hardware_root.mkdir()
    protected_root.mkdir()
    credential = hardware_admin.CredentialEnrollmentEvidence(
        signer_key_id="key-2",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key_hex="04ccdd",
        enrollment_reference="enrollment-2",
    )
    assert hardware_admin.register_credential(
        repository_root=repository_root, evidence=credential, _store_root=hardware_root
    ).record.status == "active"
    principal_evidence = principal_admin.PrincipalEnrollmentEvidence(
        principal_id="principal-2", election_reference="election-principal-2"
    )
    assert principal_admin.enroll_principal(
        repository_root=repository_root, evidence=principal_evidence, _protected_root=protected_root
    ).record.status == "active"
    signer_evidence = principal_admin.SignerEnrollmentEvidence(
        principal_id="principal-2",
        signer_key_id="key-2",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        election_reference="election-signer-2",
    )
    signer = principal_admin.enroll_signer(
        repository_root=repository_root,
        evidence=signer_evidence,
        _protected_root=protected_root,
        _hardware_store_root=hardware_root,
    )
    assert signer.record.principal_id == "principal-2"


def test_contract_identity_and_required_schema_are_exactly_seven() -> None:
    identity_ids = {contract_id for contract_id, _path in hmic._CONTRACT_IDENTITY_FILES}
    assert identity_ids == SEVEN_IDS
    assert hmic._CONTRACT_VERSIONS_REQUIRED_KEYS == SEVEN_IDS


def test_derive_to_parse_round_trip_carries_all_seven() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    assert set(versions) == SEVEN_IDS
    record = hmic.parse_certification_record(_base_record_document(versions))
    assert dict(record.contract_versions) == versions
    assert hmic.parse_certification_record(hmic.certification_record_to_document(record)) == record


@pytest.mark.parametrize("missing", ["HBDC-001", "HPSE-001", "HHCE-001"])
def test_missing_late_contract_identity_is_rejected(missing: str) -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    versions.pop(missing)
    with pytest.raises(hmic.CertificationMalformedError):
        hmic.parse_certification_record(_base_record_document(versions))


def test_unknown_eighth_contract_identity_is_rejected() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    versions["UNKNOWN-008"] = "1.0"
    with pytest.raises(hmic.CertificationMalformedError):
        hmic.parse_certification_record(_base_record_document(versions))


def test_historical_req_076_reproduces_normative_four_vs_seven_contradiction() -> None:
    text = _show(PRE_REPAIR, CONTRACT)
    req_076 = _requirement(text, "HMIC-REQ-076")
    req_067 = _requirement(text, "HMIC-REQ-067")
    assert "reading the four frozen contracts' own version" in req_076
    assert "Seven entries, no more, no fewer" in " ".join(req_067.split())
    assert "Certification creation proceeds exactly" in req_076


def test_current_req_076_req_067_validator_and_admin_are_seven_consistent() -> None:
    text = (ROOT / CONTRACT).read_text(encoding="utf-8")
    assert "each of the exact seven bound contracts'\n   own live version headers" in _requirement(text, "HMIC-REQ-076")
    assert "Seven entries, no more, no fewer" in " ".join(_requirement(text, "HMIC-REQ-067").split())
    assert "seven bound contracts' own\n    current version headers" in _requirement(text, "HMIC-REQ-103")
    admin_source = (ROOT / "scripts/hatp_certification_admin.py").read_text(encoding="utf-8")
    certify_calls = _calls(_function(admin_source, "certify"))
    assert {"derive_contract_versions", "CertificationRecord"} <= certify_calls


def test_current_normative_count_sweep_has_no_stale_four_five_or_six_contract_ceremony() -> None:
    text = (ROOT / CONTRACT).read_text(encoding="utf-8")
    normative = "\n".join(
        _requirement(text, req)
        for req in ("HMIC-REQ-050", "HMIC-REQ-052", "HMIC-REQ-053", "HMIC-REQ-067", "HMIC-REQ-069", "HMIC-REQ-076", "HMIC-REQ-103")
    )
    # CURRENT NORMATIVE, updated (§26 of the 149O.20L.7O.2M governing
    # prompt): Phase 149O.20L.7O.2M widened HMIC-REQ-050 36 -> 38.
    assert "thirty-eight files" in _requirement(text, "HMIC-REQ-050")
    assert "four frozen contracts' own version" not in normative
    assert "five bound contracts' own" not in normative
    assert "six bound contracts' own" not in normative
    assert normative.count("seven") >= 6


def test_historical_guard_window_accidentally_captured_req_076() -> None:
    historical = _show(GUARD_ORIGIN, CONTRACT)
    window = _old_guard_window(historical)
    assert "HMIC-REQ-145" in window
    assert "HMIC-REQ-076" in window
    assert "HMIC-REQ-077" not in window


def test_narrow_guard_preserves_exact_req_145_and_catches_internal_mutation() -> None:
    historical = _show(GUARD_ORIGIN, CONTRACT)
    current = (ROOT / CONTRACT).read_text(encoding="utf-8")
    expected = _narrow_guard_window(historical)
    assert _narrow_guard_window(current) == expected
    mutated = current.replace("**Status: CLOSED.**", "**Status: MUTATED.**", 1)
    assert _narrow_guard_window(mutated) != expected


def test_narrow_guard_ignores_neighbor_req_076_only_and_is_not_repinned() -> None:
    historical = _show(GUARD_ORIGIN, CONTRACT)
    current = (ROOT / CONTRACT).read_text(encoding="utf-8")
    expected = _narrow_guard_window(historical)
    req_076_mutated = current.replace("Certification creation proceeds exactly", "Certification creation proceeds MUTATED", 1)
    assert _narrow_guard_window(req_076_mutated) == expected
    old_test = _show(PRE_REPAIR, GUARD_TEST)
    new_test = _show(REPAIR_COMMIT, GUARD_TEST)
    assert "assert _extract_requirement_block(old_text, \"HMIC-REQ-145\") ==" in old_test
    assert "assert _extract_hmic_req_145_block(old_text) == _extract_hmic_req_145_block(new_text)" in new_test
    assert "85616f4b" in old_test and "85616f4b" in new_test


def test_v15_to_v16_production_change_only_binds_unchanged_paths() -> None:
    changed = set(_git("diff", "--name-only", PRE_REPAIR, REPAIR_COMMIT).splitlines())
    production_changed = {path for path in changed if path.startswith("src/pcae/") or path.startswith("scripts/")}
    assert production_changed == {PRODUCTION}
    assert _show(PRE_REPAIR, PATHS) == _show(REPAIR_COMMIT, PATHS)
    diff = _git("diff", "--unified=0", PRE_REPAIR, REPAIR_COMMIT, "--", PRODUCTION)
    executable_additions = [
        line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++") and not line[1:].lstrip().startswith("#")
    ]
    assert '    "core/paths.py",' in executable_additions
    assert any("assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in line for line in executable_additions)


def test_old_35_member_certification_fails_first_at_step_9(tmp_path: Path, monkeypatch) -> None:
    harness = HarnessPath(ROOT)
    old_members = tuple(path for path in hmic._frozen_canonical_paths() if path != PATHS)
    old_digest = _digest(ROOT, old_members)
    current_digest = hmic.derive_implementation_scope_digest(harness)
    assert old_digest != current_digest
    versions = dict(hmic.derive_contract_versions(harness))
    repository_instance_id = "12345678-1234-4234-8234-123456789abc"
    canonical_deployment_root = "/disposable/deployment"
    monkeypatch.setattr(hmic, "derive_repository_instance_id", lambda _root: repository_instance_id)
    monkeypatch.setattr(hmic, "derive_canonical_deployment_root", lambda _root: canonical_deployment_root)
    fields = {
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
        "implementation_commit": hmic.derive_implementation_commit(harness),
        "implementation_scope_digest": old_digest,
        "contract_versions": versions,
        "verification_record_digest": "e" * 64,
        "certified_at": "2026-08-19T00:00:00Z",
        "certified_by": "disposable-old-scope",
    }
    certification_id = hmic.derive_certification_id(fields)
    record = hmic.CertificationRecord(
        certification_id=certification_id,
        status="active",
        revoked_at=None,
        **fields,
    )
    certifications = hmic.CertificationsDocument(schema_version=1, certifications=(record,))
    binding = hmic.CertificationBinding(
        repository_instance_id=record.repository_instance_id,
        canonical_deployment_root=record.canonical_deployment_root,
        active_certification_id=record.certification_id,
    )
    bindings = hmic.CertificationBindingsDocument(schema_version=1, bindings=(binding,))
    (tmp_path / "certifications.json").write_text(
        json.dumps(hmic.certifications_document_to_document(certifications)), encoding="utf-8"
    )
    (tmp_path / "certification-bindings.json").write_text(
        json.dumps(hmic.certification_bindings_document_to_document(bindings)), encoding="utf-8"
    )
    result = hmic._validate_at_root(protected_root=tmp_path, repository_root=ROOT)
    assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH


def test_hmic_self_binding_is_fresh_sensitive_and_deterministic(tmp_path: Path) -> None:
    members = tuple(hmic._frozen_canonical_paths())
    assert PRODUCTION in members
    _copy_members(tmp_path, members)
    before = hmic.derive_implementation_scope_digest(HarnessPath(tmp_path))
    assert hmic.derive_implementation_scope_digest(HarnessPath(tmp_path)) == before
    target = tmp_path / PRODUCTION
    target.write_bytes(target.read_bytes() + b"\n# disposable self-binding mutation\n")
    assert hmic.derive_implementation_scope_digest(HarnessPath(tmp_path)) != before


def test_class_b_members_are_all_retained() -> None:
    assert CLASS_B_MEMBERS <= set(hmic._frozen_canonical_paths())


def test_repair_did_not_change_signing_enrollment_or_deployment_binding_sources() -> None:
    protected = {
        "src/pcae/core/hatp_signing_ceremony.py",
        "src/pcae/core/hatp_hardware_credential_admin.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    }
    changed = set(_git("diff", "--name-only", PRE_REPAIR, REPAIR_COMMIT).splitlines())
    assert protected.isdisjoint(changed)


def test_no_authority_upgrade_in_phase_owned_worktree() -> None:
    """Pinned to this phase's OWN entry/exit commits (149O.20L.7O.2H.3
    stayed verification-only across that fixed window), not to the live
    working tree: a later, separately-governed phase legitimately
    amending `src/pcae/`/`docs/contracts/` (e.g. Phase 149O.20L.7O.2M's
    own HMIC v1.7 widening) does not retroactively make THIS phase
    guilty of an authority upgrade it never performed. §26 of the
    149O.20L.7O.2M governing prompt: historical snapshot, preserved."""

    PHASE_EXIT = "aa9ed273"
    changed = set(_git("diff", "--name-only", PHASE_ENTRY, PHASE_EXIT).splitlines())
    forbidden_prefixes = (
        "src/pcae/",
        "docs/contracts/",
        ".pcae/certifications/",
        ".pcae/hatp/",
        "hac-dell/",
    )
    assert not [path for path in changed if path.startswith(forbidden_prefixes)]


def test_runtime_remains_observed_observe_unavailable() -> None:
    output = subprocess.run(
        ["pcae", "runtime", "inspect"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    assert "Runtime state:             Observed" in output
    assert "Execution capability:      unavailable" in output
    assert "Maximum plugin capability: observe" in output
