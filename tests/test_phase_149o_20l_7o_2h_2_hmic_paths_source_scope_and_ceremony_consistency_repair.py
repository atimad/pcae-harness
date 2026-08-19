"""Focused repair evidence for Phase 149O.20L.7O.2H.2.

This is implementation-phase evidence, not independent verification. It
reconstructs the two entering defects from the fixed phase-entry object and
checks the narrow v1.6 repair against live contract/production state.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from scripts import hatp_certification_admin as admin


ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY = "bb652aa4d18b5568e15feaf98c525ce0a6bd9a01"
CONTRACT_REL = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
SOURCE_REL = "src/pcae/core/hatp_mandatory_certification.py"
PATHS_REL = "src/pcae/core/paths.py"
OLD_GUARD_REL = "tests/test_phase_149o_20l_7l_6_contract_preamble_and_relative_import_guard_repair_independent_verification.py"
SEVEN_IDS = {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}

pytestmark = pytest.mark.fast_green


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def _blob(commit: str, relative: str) -> str:
    return _git("show", f"{commit}:{relative}")


def _assignments(source: str) -> dict[str, object]:
    wanted = {
        "_FROZEN_SRC_PCAE_RELATIVE_FILES",
        "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES",
        "_CONTRACT_IDENTITY_FILES",
        "_CONTRACT_VERSIONS_REQUIRED_KEYS",
    }
    values: dict[str, object] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        else:
            continue
        if not isinstance(target, ast.Name) or target.id not in wanted:
            continue
        try:
            values[target.id] = ast.literal_eval(value)
        except ValueError:
            assert isinstance(value, ast.Call)
            values[target.id] = frozenset(ast.literal_eval(value.args[0]))
    return values


def _old_state() -> dict[str, object]:
    return _assignments(_blob(PHASE_ENTRY, SOURCE_REL))


def _old_members() -> tuple[str, ...]:
    state = _old_state()
    return tuple(state["_FROZEN_SRC_PCAE_RELATIVE_FILES"]) + tuple(
        state["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]
    )


def _live_members() -> tuple[str, ...]:
    return hmic._FROZEN_AUTHORITY_BEARING_FILES


def _canonical(entries: tuple[str, ...], src_count: int) -> tuple[str, ...]:
    return tuple(f"src/pcae/{entry}" if i < src_count else entry for i, entry in enumerate(entries))


def _req(text: str, number: int) -> str:
    start = text.index(f"**HMIC-REQ-{number:03d}")
    match = re.search(r"\n\*\*HMIC-REQ-\d{3}", text[start + 1 :])
    return text[start:] if match is None else text[start : start + 1 + match.start()]


def _req050_paths(text: str) -> tuple[str, ...]:
    match = re.search(r"```\n(.*?)\n```", _req(text, 50), re.S)
    assert match
    return tuple(line.split()[0] for line in match.group(1).splitlines() if line.strip())


def _copy_live_frozen_tree(destination: Path) -> None:
    for relative in hmic._frozen_canonical_paths():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def _req145(text: str) -> str:
    match = re.search(r"\*\*HMIC-REQ-145 \(.*?(?=\n---\n)", text, re.S)
    assert match
    return match.group(0)


def _record_fields(versions: dict[str, str], *, digest: str = "b" * 64) -> dict[str, object]:
    return {
        "repository_instance_id": "123e4567-e89b-42d3-a456-426614174000",
        "canonical_deployment_root": "/deployment",
        "implementation_commit": "a" * 40,
        "implementation_scope_digest": digest,
        "contract_versions": versions,
        "verification_record_digest": "c" * 64,
        "certified_at": "2026-08-19T00:00:00Z",
        "certified_by": "protected-admin",
    }


def _record(fields: dict[str, object]) -> hmic.CertificationRecord:
    return hmic.CertificationRecord(
        certification_id=hmic.derive_certification_id(fields),
        status="active",
        revoked_at=None,
        **fields,
    )


def test_phase_entry_is_exact_historical_35_member_state() -> None:
    state = _old_state()
    assert (len(state["_FROZEN_SRC_PCAE_RELATIVE_FILES"]), len(state["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])) == (26, 9)
    assert len(_old_members()) == 35
    assert "core/paths.py" not in _old_members()


def test_paths_file_is_unchanged_object_being_bound() -> None:
    assert (ROOT / PATHS_REL).read_text(encoding="utf-8") == _blob(PHASE_ENTRY, PATHS_REL)


def test_symbol_level_ag3_and_ag5_reachability_is_present() -> None:
    signing = (ROOT / "src/pcae/core/hatp_signing_ceremony.py").read_text(encoding="utf-8")
    agent = (ROOT / "src/pcae/core/agent.py").read_text(encoding="utf-8")
    assert "production_sign_rollback_evidence" in signing
    assert "resolve_signing_context" in signing
    assert "build_rollback_review(root, job_id)" in signing
    assert "lookup_promotion_execution_record(root, per_id)" in signing
    assert "jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)" in agent
    assert "store_dir = root.path / _PXR_STORE_DIR" in agent


def test_historical_paths_mutation_redirects_real_ag3_input_without_old_digest_change(tmp_path: Path) -> None:
    sandbox = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/pcae", sandbox / "src/pcae")
    genuine = sandbox / ".pcae/remote/jobs"
    attacker = sandbox / "attacker-jobs"
    results = sandbox / ".pcae/remote/results"
    genuine.mkdir(parents=True)
    attacker.mkdir(parents=True)
    results.mkdir(parents=True)
    (genuine / "job.json").write_text(json.dumps({"requested_agent": "x", "commit_sha": "1" * 40}))
    (attacker / "job.json").write_text(json.dumps({"requested_agent": "x", "commit_sha": "2" * 40}))
    (results / "job-result.json").write_text(json.dumps({"changed_files": ["x"], "scope_validation": {}}))

    old_canonical = _canonical(_old_members(), 26)
    def old_digest() -> str:
        records = []
        for relative in sorted(old_canonical):
            source = sandbox / relative if (sandbox / relative).exists() else ROOT / relative
            records.append(f"{relative}\0{hashlib.sha256(source.read_bytes()).hexdigest()}\n".encode())
        return hashlib.sha256(b"".join(records)).hexdigest()

    code = "from pcae.core.agent import build_rollback_review; from pcae.core.paths import HarnessPath; from pathlib import Path; print(build_rollback_review(HarnessPath(Path.cwd()), 'job')['rollback_review']['original_commit_sha'])"
    env = dict(os.environ, PYTHONPATH=str(sandbox / "src"))
    before_digest = old_digest()
    before = subprocess.check_output([sys.executable, "-c", code], cwd=sandbox, env=env, text=True).strip()
    path = sandbox / PATHS_REL
    path.write_text(path.read_text().replace(
        "return self.path / relative_path",
        "return self.path / 'attacker-jobs' if str(relative_path) == '.pcae/remote/jobs' else self.path / relative_path",
    ))
    after = subprocess.check_output([sys.executable, "-c", code], cwd=sandbox, env=env, text=True).strip()
    assert (before, after) == ("1" * 40, "2" * 40)
    assert old_digest() == before_digest


def test_live_paths_bytes_are_digest_sensitive_and_deterministic(tmp_path: Path) -> None:
    _copy_live_frozen_tree(tmp_path)
    root = HarnessPath(tmp_path)
    baseline = hmic.derive_implementation_scope_digest(root)
    assert hmic.derive_implementation_scope_digest(root) == baseline
    path = tmp_path / PATHS_REL
    path.write_bytes(path.read_bytes() + b"\npaths-drift-probe\n")
    assert hmic.derive_implementation_scope_digest(root) != baseline


def test_exact_live_membership_is_27_plus_9_equals_36() -> None:
    assert (len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES), len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES)) == (27, 9)
    assert len(_live_members()) == 36
    assert "core/paths.py" in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES


def test_repair_is_exactly_additive_paths_only() -> None:
    assert set(_old_members()) < set(_live_members())
    assert set(_live_members()) - set(_old_members()) == {"core/paths.py"}


def test_contract_req050_matches_production_exactly() -> None:
    text = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    assert _req050_paths(text) == _live_members()
    assert len(_req050_paths(text)) == 36


def test_contract_is_v16_and_limb_d_names_reached_paths_behavior() -> None:
    text = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    assert "**Version:** 1.6" in text
    req052 = _req(text, 52)
    assert "HarnessPath.join" in req052 and "HarnessPath.path" in req052
    assert "original_commit_\nsha" in req052 and "ecp_id" in req052


def test_seven_contract_identity_and_closed_schema_sets_are_unchanged_equal() -> None:
    identity_ids = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert identity_ids == hmic._CONTRACT_VERSIONS_REQUIRED_KEYS == SEVEN_IDS
    old = _old_state()
    assert tuple(old["_CONTRACT_IDENTITY_FILES"]) == hmic._CONTRACT_IDENTITY_FILES
    assert frozenset(old["_CONTRACT_VERSIONS_REQUIRED_KEYS"]) == hmic._CONTRACT_VERSIONS_REQUIRED_KEYS


@pytest.mark.parametrize("missing", ["HBDC-001", "HPSE-001", "HHCE-001"])
def test_missing_load_bearing_contract_still_fails_closed(missing: str) -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    versions.pop(missing)
    with pytest.raises(hmic.CertificationMalformedError, match="missing required"):
        hmic._require_contract_versions(versions, context="contract_versions")


def test_unknown_eighth_contract_still_fails_closed() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    versions["UNKNOWN-001"] = "1.0"
    with pytest.raises(hmic.CertificationMalformedError, match="unrecognized"):
        hmic._require_contract_versions(versions, context="contract_versions")


def test_historical_req076_defect_and_live_seven_contract_repair() -> None:
    old = _req(_blob(PHASE_ENTRY, CONTRACT_REL), 76)
    live = _req((ROOT / CONTRACT_REL).read_text(encoding="utf-8"), 76)
    assert "four frozen contracts" in old
    assert "exact seven bound contracts" in live
    assert "four frozen contracts" not in live


def test_old_guard_reproduction_crossed_into_req076() -> None:
    text = _blob(PHASE_ENTRY, CONTRACT_REL)
    old = re.search(r"\*\*HMIC-REQ-145 \(.*?(?=\n\*\*HMIC-REQ-\d{3} \(|\Z)", text, re.S)
    assert old and "HMIC-REQ-076" in old.group(0) and "four frozen contracts" in old.group(0)


def test_narrow_guard_preserves_historical_req145_bytes() -> None:
    historical = _blob("85616f4b", CONTRACT_REL)
    live = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    assert _req145(historical) == _req145(live)


def test_narrow_guard_detects_mutation_inside_req145() -> None:
    live = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    mutated = live.replace("**Status: CLOSED.**", "**Status: OPEN.**", 1)
    assert _req145(mutated) != _req145(live)


def test_narrow_guard_ignores_neighboring_req076_mutation() -> None:
    live = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    mutated = live.replace("each of the exact seven bound contracts'", "neighbor-only mutation")
    assert _req145(mutated) == _req145(live)


def test_guard_source_uses_exact_req145_horizontal_rule_boundary() -> None:
    source = (ROOT / OLD_GUARD_REL).read_text(encoding="utf-8")
    function = source[source.index("def _extract_hmic_req_145_block") : source.index("def test_hmic_req_050")]
    assert "(?=\\n---\\n)" in function
    assert "HMIC-REQ-\\d{{3}}" not in function


def test_current_contract_has_no_normative_four_or_six_contract_ceremony() -> None:
    req076 = _req((ROOT / CONTRACT_REL).read_text(encoding="utf-8"), 76).lower()
    assert "four" not in req076 and "five" not in req076 and "six" not in req076
    assert "seven" in req076 and "live version headers" in req076


def test_disposable_certify_carries_all_seven_versions_without_activation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("independent evidence")
    protected = tmp_path / "protected"
    versions = {key: "1.0" for key in SEVEN_IDS}
    monkeypatch.setattr(admin, "derive_repository_instance_id", lambda _root: "123e4567-e89b-42d3-a456-426614174000")
    monkeypatch.setattr(admin, "derive_canonical_deployment_root", lambda _root: "/deployment")
    monkeypatch.setattr(admin, "derive_implementation_commit", lambda _root: "a" * 40)
    monkeypatch.setattr(admin, "derive_implementation_scope_digest", lambda _root: "b" * 64)
    monkeypatch.setattr(admin, "derive_contract_versions", lambda _root: versions)
    result = admin.certify(
        repository_root=tmp_path,
        certified_by="protected-admin",
        verification_record_path=report,
        confirm=True,
        _protected_root=protected,
    )
    assert set(result.record.contract_versions) == SEVEN_IDS
    assert not (protected / "certification-bindings.json").exists()


def test_old_35_member_certification_fails_at_implementation_before_contract_check(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    fields = _record_fields(versions, digest="1" * 64)
    record = _record(fields)
    binding = hmic.CertificationBinding(record.repository_instance_id, record.canonical_deployment_root, record.certification_id)
    monkeypatch.setattr(hmic, "derive_repository_instance_id", lambda _root: record.repository_instance_id)
    monkeypatch.setattr(hmic, "derive_canonical_deployment_root", lambda _root: record.canonical_deployment_root)
    monkeypatch.setattr(hmic, "derive_implementation_commit", lambda _root: record.implementation_commit)
    monkeypatch.setattr(hmic, "derive_implementation_scope_digest", lambda _root: "2" * 64)
    monkeypatch.setattr(hmic, "derive_contract_versions", lambda _root: pytest.fail("step 10 must not run after step 9"))
    monkeypatch.setattr(hmic, "_load_active_binding", lambda *_a, **_k: binding)
    monkeypatch.setattr(hmic, "_load_certification_record", lambda *_a, **_k: record)
    result = hmic._validate_at_root(protected_root=tmp_path / "protected", repository_root=ROOT)
    assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH


def test_limb_d_remaining_leaves_are_audit_only() -> None:
    provenance = (ROOT / "src/pcae/core/provenance.py").read_text(encoding="utf-8")
    hardware = (ROOT / "src/pcae/core/hatp_hardware_credential_admin.py").read_text(encoding="utf-8")
    principal = (ROOT / "src/pcae/core/hatp_principal_signer_admin.py").read_text(encoding="utf-8")
    assert "append_provenance_event" in hardware and "append_provenance_event" in principal
    assert "read_git_branch" in provenance and "find_latest_active_task" in provenance
    for source in (hardware, principal):
        assert source.index("append_provenance_event") < source.index("def _audit")
    signing = (ROOT / "src/pcae/core/hatp_signing_ceremony.py").read_text(encoding="utf-8")
    assert "pcae.core.provenance" not in signing


def test_class_b_deployment_binding_and_v15_additions_are_retained() -> None:
    required = {
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
        "core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
        "core/hatp_signing_ceremony.py",
        "core/hatp_hardware_credential_admin.py",
        "core/hatp_principal_signer_admin.py",
        "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
        "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
    }
    assert required <= set(_live_members())


def test_self_binding_remains_live_and_uncached(tmp_path: Path) -> None:
    _copy_live_frozen_tree(tmp_path)
    root = HarnessPath(tmp_path)
    before = hmic.derive_implementation_scope_digest(root)
    target = tmp_path / SOURCE_REL
    target.write_bytes(target.read_bytes() + b"\nself-binding-probe\n")
    assert hmic.derive_implementation_scope_digest(root) != before


def test_no_protected_or_authority_state_path_is_phase_modified() -> None:
    changed = set(_git("diff", "--name-only", PHASE_ENTRY).splitlines())
    assert not {p for p in changed if p.startswith(".pcae/certifications") or p.startswith(".pcae/hatp/") or p.startswith("hac-dell/")}
    assert PATHS_REL not in changed


def test_runtime_remains_observed_observe_unavailable() -> None:
    output = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    assert "Runtime state:             Observed" in output
    assert "Maximum plugin capability: observe" in output
    assert "Execution capability:      unavailable" in output
