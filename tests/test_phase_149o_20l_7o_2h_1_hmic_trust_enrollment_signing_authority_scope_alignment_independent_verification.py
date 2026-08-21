"""Independent evidence for Phase 149O.20L.7O.2H.1.

This suite reconstructs the relevant identities from the contract, source AST,
and fixed Git objects.  It deliberately does not import either 2H/2H.0 test
module or use their phase reports as an oracle.  Finding tests preserve and
demonstrate defects; they are expected to pass when the defect is present.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import replace

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
SOURCE_REL = "src/pcae/core/hatp_mandatory_certification.py"
V14 = "e65b4ce0bd17800f85e0858c78032bd968d1d574"
POST_2H = "0893f40afd5258e1ba85fb197f708095dfcc7dbc"
PHASE_ENTRY = "973258b991f0df21b9996fe29adc5c13ca06dc7b"
SIGNING_IV = "b229e423"
TRUST_ENROLLMENT_IV = "021175c9"

pytestmark = pytest.mark.fast_green


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def _blob(commit: str, path: str) -> str:
    return _git("show", f"{commit}:{path}")


def _literal_assignments(source: str) -> dict[str, object]:
    wanted = {
        "_FROZEN_SRC_PCAE_RELATIVE_FILES",
        "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES",
        "_CONTRACT_IDENTITY_FILES",
        "_CONTRACT_VERSIONS_REQUIRED_KEYS",
    }
    result: dict[str, object] = {}
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
            result[target.id] = ast.literal_eval(value)
        except ValueError:
            assert isinstance(value, ast.Call) and value.args
            result[target.id] = frozenset(ast.literal_eval(value.args[0]))
    return result


def _state(commit: str) -> dict[str, object]:
    return _literal_assignments(_blob(commit, SOURCE_REL))


def _req(text: str, number: int) -> str:
    start = text.index(f"**HMIC-REQ-{number:03d}")
    match = re.search(r"\n\*\*HMIC-REQ-\d{3}", text[start + 1 :])
    return text[start:] if match is None else text[start : start + 1 + match.start()]


def _req050_paths(text: str) -> tuple[str, ...]:
    section = _req(text, 50)
    block = re.search(r"```\n(.*?)\n```", section, re.S)
    assert block is not None
    return tuple(line.strip().split()[0] for line in block.group(1).splitlines() if line.strip())


def _production_paths(state: dict[str, object]) -> tuple[str, ...]:
    return tuple(state["_FROZEN_SRC_PCAE_RELATIVE_FILES"]) + tuple(
        state["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]
    )


def _canonical_paths(state: dict[str, object]) -> tuple[str, ...]:
    src = tuple(f"src/pcae/{p}" for p in state["_FROZEN_SRC_PCAE_RELATIVE_FILES"])
    return src + tuple(state["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])


def _copy_frozen_tree(destination: Path) -> None:
    for relative in _canonical_paths(_state(PHASE_ENTRY)):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def _record_fields(versions: dict[str, str]) -> dict[str, object]:
    return {
        "repository_instance_id": "123e4567-e89b-42d3-a456-426614174000",
        "canonical_deployment_root": "/deployment",
        "implementation_commit": "a" * 40,
        "implementation_scope_digest": "b" * 64,
        "contract_versions": versions,
        "verification_record_digest": "c" * 64,
        "certified_at": "2026-08-19T00:00:00Z",
        "certified_by": "independent-verifier",
    }


def _record_document(versions: dict[str, str]) -> dict[str, object]:
    fields = _record_fields(versions)
    return {
        "certification_id": hmic.derive_certification_id(fields),
        **fields,
        "status": "active",
    }


def test_fixed_checkpoints_reconstruct_30_5_then_35_7_6_then_35_7_7() -> None:
    v14, post, current = _state(V14), _state(POST_2H), _state(PHASE_ENTRY)
    assert (len(v14["_FROZEN_SRC_PCAE_RELATIVE_FILES"]), len(v14["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])) == (23, 7)
    assert (len(_production_paths(v14)), len(v14["_CONTRACT_IDENTITY_FILES"])) == (30, 5)
    assert (len(post["_FROZEN_SRC_PCAE_RELATIVE_FILES"]), len(post["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])) == (26, 9)
    assert (len(_production_paths(post)), len(post["_CONTRACT_IDENTITY_FILES"]), len(post["_CONTRACT_VERSIONS_REQUIRED_KEYS"])) == (35, 7, 6)
    assert (len(_production_paths(current)), len(current["_CONTRACT_IDENTITY_FILES"]), len(current["_CONTRACT_VERSIONS_REQUIRED_KEYS"])) == (35, 7, 7)


def test_v14_to_v15_frozen_delta_is_exactly_five_additions_and_no_removals() -> None:
    old, new = set(_production_paths(_state(V14))), set(_production_paths(_state(PHASE_ENTRY)))
    assert old <= new
    assert new - old == {
        "core/hatp_signing_ceremony.py",
        "core/hatp_hardware_credential_admin.py",
        "core/hatp_principal_signer_admin.py",
        "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
        "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
    }
    assert not old - new


def test_v14_to_v15_contract_identity_delta_is_exactly_hpse_hhce() -> None:
    old = set(_state(V14)["_CONTRACT_IDENTITY_FILES"])
    new = set(_state(PHASE_ENTRY)["_CONTRACT_IDENTITY_FILES"])
    assert old <= new
    assert new - old == {
        ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
        ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
    }


def test_contract_req050_and_current_production_membership_are_exactly_equal() -> None:
    text = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    assert _req050_paths(text) == _production_paths(_state(PHASE_ENTRY))
    assert len(_req050_paths(text)) == 35


def test_current_contract_normatively_requires_four_limbs_and_seven_identities() -> None:
    text = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    req052, req053, req067, req069 = (_req(text, n) for n in (52, 53, 67, 69))
    assert all(f"({letter})" in req052 for letter in "abcd")
    assert "production_sign_rollback_\nevidence" in req052
    assert "every\n`contract_versions` member" in req053 and "seven entries" in req053
    ids = {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}
    assert all(contract_id in req067 for contract_id in ids)
    assert "Seven entries,\nno more, no fewer" in req067
    assert "seven entries as of v1.5" in req069


def test_all_seven_contract_identities_are_unique_live_header_derived_and_content_bound() -> None:
    identities = tuple(hmic._CONTRACT_IDENTITY_FILES)
    assert len(identities) == len({i for i, _ in identities}) == len({p for _, p in identities}) == 7
    frozen = set(_canonical_paths(_state(PHASE_ENTRY)))
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    assert set(versions) == {i for i, _ in identities} == set(hmic._CONTRACT_VERSIONS_REQUIRED_KEYS)
    for contract_id, path in identities:
        assert path in frozen
        text = (ROOT / path).read_text(encoding="utf-8")
        assert re.search(rf"^\*\*Contract(?: ID)?:\*\*\s*{re.escape(contract_id)}\s*$", text, re.M)
        assert versions[contract_id] == re.search(r"^\*\*Version:\*\*\s*v?(\S+)", text, re.M).group(1)


def test_historical_post_2h_defect_is_exactly_hbdc_and_actual_derive_rejects_parse(tmp_path: Path) -> None:
    code = r'''
from pathlib import Path
from pcae.core.paths import HarnessPath
from pcae.core.hatp_mandatory_certification import derive_contract_versions, _require_contract_versions, CertificationMalformedError
versions = dict(derive_contract_versions(HarnessPath(Path.cwd())))
assert len(versions) == 7
try:
    _require_contract_versions(versions, context="contract_versions")
except CertificationMalformedError as exc:
    assert "HBDC-001" in str(exc) and "unrecognized" in str(exc)
else:
    raise AssertionError("historical seven-member derivation unexpectedly parsed")
six = {key: value for key, value in versions.items() if key != "HBDC-001"}
assert len(_require_contract_versions(six, context="contract_versions")) == 6
'''
    archive = subprocess.check_output(["git", "archive", POST_2H], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
        snapshot.extractall(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(tmp_path / "src"))
    completed = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr


def test_current_seven_member_derive_to_parse_round_trip() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    record = hmic.parse_certification_record(_record_document(versions))
    assert dict(record.contract_versions) == versions


@pytest.mark.parametrize("missing", ["HBDC-001", "HPSE-001", "HHCE-001"])
def test_current_parser_rejects_missing_load_bearing_contract(missing: str) -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    versions.pop(missing)
    with pytest.raises(hmic.CertificationMalformedError, match="missing required"):
        hmic.parse_certification_record(_record_document(versions))


def test_current_parser_rejects_unknown_eighth_key_and_non_string_version() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    with_unknown = {**versions, "UNKNOWN-001": "1.0"}
    with pytest.raises(hmic.CertificationMalformedError, match="unrecognized"):
        hmic.parse_certification_record(_record_document(with_unknown))
    versions["HBDC-001"] = 1  # type: ignore[assignment]
    with pytest.raises(hmic.CertificationMalformedError, match="non-empty string"):
        hmic.parse_certification_record(_record_document(versions))


def test_duplicate_json_contract_key_fails_strict_loading() -> None:
    raw = b'{"schema_version":1,"certifications":[],"certifications":[]}'
    with pytest.raises(hmic.CertificationMalformedError, match="duplicate JSON object key"):
        hmic.parse_certifications_document_from_bytes(raw)


@pytest.mark.parametrize("contract_id", ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"])
def test_certification_id_is_sensitive_to_each_contract_version(contract_id: str) -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    baseline = hmic.derive_certification_id(_record_fields(versions))
    versions[contract_id] += ".changed"
    assert hmic.derive_certification_id(_record_fields(versions)) != baseline


@pytest.mark.parametrize("wrong", [None, "HBDC-001", "HPSE-001", "HHCE-001"])
def test_validation_compares_complete_seven_member_mapping(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, wrong: str | None) -> None:
    current = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    stored = dict(current)
    if wrong:
        stored[wrong] += ".wrong"
    record = hmic.parse_certification_record(_record_document(stored))
    monkeypatch.setattr(hmic, "derive_repository_instance_id", lambda _root: record.repository_instance_id)
    monkeypatch.setattr(hmic, "derive_canonical_deployment_root", lambda _root: record.canonical_deployment_root)
    monkeypatch.setattr(hmic, "derive_implementation_commit", lambda _root: record.implementation_commit)
    monkeypatch.setattr(hmic, "derive_implementation_scope_digest", lambda _root: record.implementation_scope_digest)
    monkeypatch.setattr(hmic, "derive_contract_versions", lambda _root: current)
    binding = hmic.CertificationBinding(record.repository_instance_id, record.canonical_deployment_root, record.certification_id)
    monkeypatch.setattr(hmic, "_load_active_binding", lambda *_a, **_k: binding)
    monkeypatch.setattr(hmic, "_load_certification_record", lambda *_a, **_k: record)
    result = hmic._validate_at_root(protected_root=tmp_path / "protected", repository_root=ROOT)
    assert result.status is (hmic.CertificationStatus.VALID if wrong is None else hmic.CertificationStatus.CONTRACT_MISMATCH)


def test_historical_v14_record_fails_current_schema_before_it_can_be_valid() -> None:
    versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
    historical = {key: versions[key] for key in ("HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001")}
    with pytest.raises(hmic.CertificationMalformedError, match="missing required"):
        hmic.parse_certification_record(_record_document(historical))


@pytest.mark.parametrize(
    "relative",
    [
        "src/pcae/core/hatp_signing_ceremony.py",
        "src/pcae/core/hatp_hardware_credential_admin.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
        "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
        "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
    ],
)
def test_each_v15_content_addition_changes_scope_digest(tmp_path: Path, relative: str) -> None:
    _copy_frozen_tree(tmp_path)
    root = HarnessPath(tmp_path)
    before = hmic.derive_implementation_scope_digest(root)
    target = tmp_path / relative
    target.write_bytes(target.read_bytes() + b"\nindependent-drift-probe\n")
    assert hmic.derive_implementation_scope_digest(root) != before


@pytest.mark.parametrize(
    "contract_id,relative",
    [
        ("HBDC-001", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"),
        ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
        ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
    ],
)
def test_same_version_contract_body_drift_changes_digest_not_versions(tmp_path: Path, contract_id: str, relative: str) -> None:
    _copy_frozen_tree(tmp_path)
    root = HarnessPath(tmp_path)
    before_versions = dict(hmic.derive_contract_versions(root))
    before_digest = hmic.derive_implementation_scope_digest(root)
    target = tmp_path / relative
    target.write_bytes(target.read_bytes() + b"\nbody-only-drift\n")
    assert dict(hmic.derive_contract_versions(root)) == before_versions
    assert hmic.derive_implementation_scope_digest(root) != before_digest
    assert contract_id in before_versions


def test_self_binding_is_live_uncached_and_deterministic(tmp_path: Path) -> None:
    _copy_frozen_tree(tmp_path)
    root = HarnessPath(tmp_path)
    first = hmic.derive_implementation_scope_digest(root)
    assert hmic.derive_implementation_scope_digest(root) == first
    target = tmp_path / SOURCE_REL
    target.write_bytes(target.read_bytes() + b"\nself-binding-probe\n")
    assert hmic.derive_implementation_scope_digest(root) != first


def test_class_b_and_deployment_binding_members_are_retained() -> None:
    members = set(_production_paths(_state(PHASE_ENTRY)))
    assert {
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
        "core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    } <= members


@pytest.mark.parametrize(
    "relative,checkpoint",
    [
        ("src/pcae/core/hatp_signing_ceremony.py", SIGNING_IV),
        ("src/pcae/core/hatp_principal_signer_admin.py", TRUST_ENROLLMENT_IV),
    ],
)
def test_newly_bound_source_is_byte_unchanged_since_independent_implementation_verification(relative: str, checkpoint: str) -> None:
    assert (ROOT / relative).read_text(encoding="utf-8") == _blob(checkpoint, relative)


def test_hatp_hardware_credential_admin_diverged_from_iv_checkpoint_only_via_2n_13_vocabulary_repair() -> None:
    """`hatp_hardware_credential_admin.py` legitimately diverged from its
    `TRUST_ENROLLMENT_IV` checkpoint bytes at Phase 149O.20L.7O.2N.13,
    which repaired NBF-149O.20L.7O.2N.12-2 (a duplicated, mirrored closed
    `("FIDO2", "PIV")` protocol_name vocabulary check) by making this
    module import and consume the canonical `_PROTOCOL_VALUES` from
    `hatp_hardware_credentials.py` instead of carrying its own literal
    tuple. This replaces the prior byte-identity pin (no longer
    accurate) with an explicit, narrow diff assertion."""
    checkpoint_text = _blob(TRUST_ENROLLMENT_IV, "src/pcae/core/hatp_hardware_credential_admin.py")
    current_text = (ROOT / "src/pcae/core/hatp_hardware_credential_admin.py").read_text(encoding="utf-8")
    assert current_text != checkpoint_text
    assert 'protocol_name not in ("FIDO2", "PIV")' in checkpoint_text
    assert 'protocol_name not in ("FIDO2", "PIV")' not in current_text
    assert "_PROTOCOL_VALUES" in current_text


def test_bf1_has_zero_production_credential_identity_callers() -> None:
    callers: list[str] = []
    for path in (ROOT / "src/pcae").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "credential_identity":
                callers.append(str(path.relative_to(ROOT)))
    assert callers == []


def test_bf2_signing_uses_explicit_nonresident_signer_key_lookup() -> None:
    text = (ROOT / "src/pcae/core/hatp_fido2_provider.py").read_text(encoding="utf-8")
    request = text[text.index("def request_signature") :]
    assert "bytes.fromhex(signer_key_id)" in request
    assert "credential_identity()" not in request.split("def ", 1)[0]


def test_leaf_git_status_and_tasks_symbols_are_not_called_by_reached_agent_readers() -> None:
    tree = ast.parse((ROOT / "src/pcae/core/agent.py").read_text(encoding="utf-8"))
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in ("build_rollback_review", "lookup_promotion_execution_record"):
        used = {n.id for n in ast.walk(functions[name]) if isinstance(n, ast.Name)}
        assert "read_git_branch" not in used
        assert "read_git_changes" not in used
        assert "find_latest_active_task" not in used


def test_finding_paths_is_excluded_even_though_reached_join_can_redirect_signing_input(tmp_path: Path) -> None:
    """Blocking finding: a real paths.py byte edit changes the AG3 identity
    read while the canonical digest over all 35 bound files stays equal."""
    sandbox = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/pcae", sandbox / "src/pcae")
    _copy_frozen_tree(sandbox)
    genuine_jobs = sandbox / ".pcae/remote/jobs"
    attacker_jobs = sandbox / "attacker-jobs"
    results = sandbox / ".pcae/remote/results"
    genuine_jobs.mkdir(parents=True)
    attacker_jobs.mkdir(parents=True)
    results.mkdir(parents=True)
    (genuine_jobs / "job.json").write_text(json.dumps({"requested_agent": "x", "commit_sha": "1" * 40}))
    (attacker_jobs / "job.json").write_text(json.dumps({"requested_agent": "x", "commit_sha": "2" * 40}))
    (results / "job-result.json").write_text(json.dumps({"changed_files": ["x"], "scope_validation": {}}))

    frozen = _canonical_paths(_state(PHASE_ENTRY))
    def digest() -> str:
        records = []
        for relative in sorted(frozen):
            file_digest = hashlib.sha256((sandbox / relative).read_bytes()).hexdigest()
            records.append(f"{relative}\0{file_digest}\n".encode())
        return hashlib.sha256(b"".join(records)).hexdigest()

    code = "from pcae.core.agent import build_rollback_review; from pcae.core.paths import HarnessPath; from pathlib import Path; print(build_rollback_review(HarnessPath(Path.cwd()), 'job')['rollback_review']['original_commit_sha'])"
    env = dict(os.environ, PYTHONPATH=str(sandbox / "src"))
    baseline_digest = digest()
    before = subprocess.check_output([sys.executable, "-c", code], cwd=sandbox, env=env, text=True).strip()
    paths_file = sandbox / "src/pcae/core/paths.py"
    source = paths_file.read_text(encoding="utf-8")
    source = source.replace(
        "return self.path / relative_path",
        "return self.path / 'attacker-jobs' if str(relative_path) == '.pcae/remote/jobs' else self.path / relative_path",
    )
    paths_file.write_text(source, encoding="utf-8")
    after = subprocess.check_output([sys.executable, "-c", code], cwd=sandbox, env=env, text=True).strip()
    assert (before, after) == ("1" * 40, "2" * 40)
    assert digest() == baseline_digest
    assert "src/pcae/core/paths.py" not in frozen


def test_finding_current_normative_req076_still_says_four_while_req067_says_seven() -> None:
    text = (ROOT / CONTRACT_REL).read_text(encoding="utf-8")
    req076 = _req(text, 76)
    req067 = _req(text, 67)
    assert "reading the four frozen contracts' own version" in req076
    assert "Seven entries,\nno more, no fewer" in req067
    assert "Certification creation proceeds exactly" in req076
