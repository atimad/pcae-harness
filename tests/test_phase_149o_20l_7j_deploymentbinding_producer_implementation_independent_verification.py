"""Phase 149O.20L.7J -- DeploymentBinding Producer Implementation
Independent Verification.

Independent-oracle companion module. Does NOT import or treat
`tests/test_hatp_deployment_binding_admin.py` or
`tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py`
(7I's own suites) as ground truth -- every assertion here is derived
fresh against primary source (contract text, production source, git
history) and live adversarial execution against disposable trust
stores/repositories.

Verification-only. No producer implementation modified. No HBDC-001
text amended. No real `DeploymentBinding` created. No Dell mutation of
any kind.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from pcae.core import hatp_deployment_binding_admin as admin
from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin
from pcae.core.hatp_bootstrap import (
    HATPTrustStore,
    deployment_binding_matches,
    resolve_canonical_deployment_root,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history
from pcae.core.repository_identity import ensure_repository_identity, read_repository_identity

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRODUCER_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_deployment_binding_admin.py"
_CERT_MODULE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _enroll_prereqs(store_root: Path, *, principal_id: str, signer_key_id: str) -> None:
    """Phase 149O.20L.7O.2F (Surface E) added mandatory cross-registry
    validation; see the identical helper's rationale in
    `tests/test_hatp_deployment_binding_admin.py`."""

    hw_admin.register_credential(
        repository_root=store_root,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=signer_key_id,
            provider_profile="HATP_HARDWARE_PROVIDER_V1",
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="ab" * 20,
            enrollment_reference="CHGR-PREREQ-HW",
        ),
        _store_root=store_root,
    )
    ps_admin.enroll_principal(
        repository_root=store_root,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id=principal_id, election_reference="CHGR-PREREQ-P"),
        _protected_root=store_root,
    )
    ps_admin.enroll_signer(
        repository_root=store_root,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id=principal_id,
            signer_key_id=signer_key_id,
            provider_profile="HATP_HARDWARE_PROVIDER_V1",
            election_reference="CHGR-PREREQ-S",
        ),
        _protected_root=store_root,
        _hardware_store_root=store_root,
    )


def _authority(store_root: Path = None, **overrides: str) -> admin.AuthorityEvidence:
    principal_id = overrides.get("principal_id", "p1")
    fields = dict(
        principal_id=principal_id,
        signer_key_id=f"signer-for-{principal_id}",
        authority_scope="CLASS_B_DEPLOYMENT",
        election_reference="CHGR-TEST-7J",
    )
    fields.update(overrides)
    if store_root is not None:
        try:
            _enroll_prereqs(store_root, principal_id=fields["principal_id"], signer_key_id=fields["signer_key_id"])
        except Exception:
            pass
    return admin.AuthorityEvidence(**fields)


def _repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    root.mkdir()
    ensure_repository_identity(HarnessPath(root))
    return root


def _store(tmp_path: Path, name: str = "store") -> Path:
    root = tmp_path / name
    root.mkdir()
    return root


# ═══════════════════════════════════════════════════════════════════════════
# Immutability proofs (byte-hash, not diff inference)
# ═══════════════════════════════════════════════════════════════════════════


def test_hbdc_001_byte_identical_since_7h_baseline() -> None:
    head_hash = _git("hash-object", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
    baseline_object_hash = subprocess.run(
        ["git", "show", "c46d4db4:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"],
        cwd=_REPO_ROOT, capture_output=True, check=True,
    ).stdout
    piped = subprocess.run(
        ["git", "hash-object", "--stdin"], cwd=_REPO_ROOT, input=baseline_object_hash, capture_output=True, check=True
    ).stdout.decode().strip()
    assert head_hash == piped


def test_hatp_bootstrap_and_repository_identity_byte_identical_since_7h() -> None:
    for rel in ("src/pcae/core/hatp_bootstrap.py", "src/pcae/core/repository_identity.py"):
        head_hash = _git("hash-object", rel)
        baseline_bytes = subprocess.run(
            ["git", "show", f"e9cad634:{rel}"], cwd=_REPO_ROOT, capture_output=True, check=True
        ).stdout
        baseline_hash = subprocess.run(
            ["git", "hash-object", "--stdin"], cwd=_REPO_ROOT, input=baseline_bytes, capture_output=True, check=True
        ).stdout.decode().strip()
        assert head_hash == baseline_hash, f"{rel} drifted since the 7H-verified baseline"


def test_7i_production_diff_scope_is_exactly_two_new_files() -> None:
    diff = _git("diff", "--stat", "0b530959^", "f38e0741", "--", "src/pcae", "scripts", "schemas")
    assert "scripts/hatp_deployment_binding_admin.py" in diff
    assert "src/pcae/core/hatp_deployment_binding_admin.py" in diff
    assert diff.count("|") == 2, f"expected exactly two changed production files, got: {diff}"


def test_hatp_trust_store_still_has_zero_write_methods() -> None:
    public_names = [name for name in dir(HATPTrustStore) if not name.startswith("_")]
    forbidden_prefixes = ("create", "rotate", "revoke", "write", "enroll", "grant")
    for name in public_names:
        assert not any(name.startswith(p) for p in forbidden_prefixes), f"HATPTrustStore gained a write method: {name}"


# ═══════════════════════════════════════════════════════════════════════════
# Agent reachability (full src/pcae tree, not just the 3 files 7I's own
# test checks)
# ═══════════════════════════════════════════════════════════════════════════


def test_producer_module_not_imported_anywhere_in_src_pcae_except_itself() -> None:
    # As of Phase 149O.20L.7K (HMIC-001 v1.4, contract §55), `hatp_
    # mandatory_certification.py`'s own frozen-set enumeration
    # legitimately and intentionally names this producer as a literal
    # path string (not an import) -- mirroring the identical exception
    # already implicit in `hatp_certification_admin.py`'s long-standing
    # frozen-set membership. Data reference in a frozen enumeration, not
    # agent-reachable code; the real security property (no import, no
    # agent-executable code path) is unaffected.
    #
    # Tightened at 149O.20L.7L.1 (F-7L-7) from a whole-file exemption to
    # an exact-occurrence exemption: `hatp_mandatory_certification.py` is
    # no longer skipped outright -- every textual occurrence of the
    # producer's name in it is inspected, and only non-import (literal
    # path-string) occurrences are tolerated. A future real
    # `import`/`from` line referencing the producer in that file would
    # still fail this test.
    # Phase 149O.20L.7O.2F (HPSE-REQ-033, Surface C): `hatp_principal_
    # signer_admin.py` is the first legitimate real import of this
    # producer's write primitives, required by contract text (the
    # Principal/Signer writer and the `DeploymentBinding` writer share
    # the identical, single, whole-registry-document transition lock) --
    # see `test_phase_149o_20l_7i_deploymentbinding_producer_
    # implementation.py`'s identical exemption for the full rationale.
    importers = []
    for path in (_REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path == _PRODUCER_PATH or path.name == "hatp_principal_signer_admin.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "hatp_deployment_binding_admin" not in text:
            continue
        if path.name == "hatp_mandatory_certification.py":
            offending = [
                line
                for line in text.splitlines()
                if "hatp_deployment_binding_admin" in line
                and line.strip().split(" ", 1)[0] in ("import", "from")
            ]
            if offending:
                importers.append(str(path.relative_to(_REPO_ROOT)))
            continue
        importers.append(str(path.relative_to(_REPO_ROOT)))
    assert importers == [], f"producer module referenced outside itself: {importers}"


def test_console_script_entry_point_is_only_pcae_cli_main() -> None:
    pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_section = pyproject[pyproject.index("[project.scripts]"):]
    scripts_section = scripts_section[: scripts_section.index("\n\n")]
    assert "hatp_deployment_binding_admin" not in scripts_section
    assert 'pcae = "pcae.cli:main"' in scripts_section


# ═══════════════════════════════════════════════════════════════════════════
# Idempotency valid_from-exclusion adjudication (live)
# ═══════════════════════════════════════════════════════════════════════════


def test_idempotent_create_preserves_first_valid_from_across_temporal_repeat(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    authority = _authority(store_root)
    first = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root, _hardware_store_root=store_root)
    time.sleep(0.01)
    second = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root, _hardware_store_root=store_root)
    assert second.outcome == admin.DeploymentBindingOutcome.ALREADY_SATISFIED
    assert second.binding.valid_from == first.binding.valid_from
    raw = json.loads((store_root / "registry.json").read_text())
    assert len(raw["deployment_bindings"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# F4 audit reconstruction: explicit A->B linkage in the rotate summary
# ═══════════════════════════════════════════════════════════════════════════


def test_f4_rotate_audit_record_explicitly_links_previous_and_new_principal(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(store_root, principal_id="pA"), _protected_root=store_root, _hardware_store_root=store_root)
    admin.rotate_deployment_binding(repository_root=repo_root, authority=_authority(store_root, principal_id="pB"), _protected_root=store_root, _hardware_store_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV", _protected_root=store_root)

    raw = json.loads((store_root / "registry.json").read_text())
    assert len(raw["deployment_bindings"]) == 1
    assert raw["deployment_bindings"][0]["status"] == "revoked"

    history = read_provenance_history(HarnessPath(repo_root))
    summaries = {event.event_type: event.summary for event in history.events}
    assert set(summaries) == {
        "deployment_binding_created",
        "deployment_binding_rotated",
        "deployment_binding_revoked",
    }
    assert "pA" in summaries["deployment_binding_created"]
    assert "previous_principal_id=pA" in summaries["deployment_binding_rotated"]
    assert "new_principal_id=pB" in summaries["deployment_binding_rotated"]


# ═══════════════════════════════════════════════════════════════════════════
# Audit failure after durable mutation: propagates, mutation stays durable
# ═══════════════════════════════════════════════════════════════════════════


def test_audit_failure_after_mutation_propagates_but_mutation_stays_durable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    def failing_audit(**kwargs: object) -> None:
        raise RuntimeError("simulated audit backend failure")

    monkeypatch.setattr(admin, "_audit", failing_audit)
    with pytest.raises(RuntimeError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)

    raw = json.loads((store_root / "registry.json").read_text())
    assert len(raw["deployment_bindings"]) == 1
    assert raw["deployment_bindings"][0]["status"] == "active"

    history = read_provenance_history(HarnessPath(repo_root))
    assert list(history.events) == []


# ═══════════════════════════════════════════════════════════════════════════
# Multi-process concurrency (real OS processes, not threads)
# ═══════════════════════════════════════════════════════════════════════════


def _mp_create(repo: str, store: str, principal: str) -> None:
    import sys as _sys

    _sys.path.insert(0, str(_REPO_ROOT / "src"))
    from pcae.core import hatp_deployment_binding_admin as _admin

    try:
        _admin.create_deployment_binding(
            repository_root=Path(repo),
            authority=_admin.AuthorityEvidence(
                principal_id=principal, signer_key_id="signer-for-p1",
                authority_scope="CLASS_B_DEPLOYMENT", election_reference="CHGR-TEST-7J",
            ),
            _protected_root=Path(store),
            _hardware_store_root=Path(store),
        )
    except Exception:
        pass


def test_six_concurrent_os_processes_creating_identical_binding_converge_on_one_entry(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    _enroll_prereqs(store_root, principal_id="p1", signer_key_id="signer-for-p1")
    procs = [multiprocessing.Process(target=_mp_create, args=(str(repo_root), str(store_root), "p1")) for _ in range(6)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=15)
    raw = json.loads((store_root / "registry.json").read_text())
    assert len(raw["deployment_bindings"]) == 1


def _mp_hold_lock_then_die(store: str) -> None:
    import sys as _sys

    _sys.path.insert(0, str(_REPO_ROOT / "src"))
    from pcae.core import hatp_deployment_binding_admin as _admin

    with _admin._deployment_binding_transition_lock(Path(store)):
        os.kill(os.getpid(), signal.SIGKILL)


def test_crash_with_held_lock_does_not_block_next_writer(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    proc = multiprocessing.Process(target=_mp_hold_lock_then_die, args=(str(store_root),))
    proc.start()
    proc.join(timeout=15)
    assert proc.exitcode != 0

    start = time.time()
    result = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)
    assert time.time() - start < 10
    assert result.outcome == admin.DeploymentBindingOutcome.CREATED


# ═══════════════════════════════════════════════════════════════════════════
# Canonical root: relative and symlink convergence
# ═══════════════════════════════════════════════════════════════════════════


def test_symlinked_repository_root_converges_on_same_binding_not_a_new_entry(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    first = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)

    symlinked = tmp_path / "repo_symlink"
    os.symlink(repo_root, symlinked)
    assert resolve_canonical_deployment_root(symlinked) == resolve_canonical_deployment_root(repo_root)

    second = admin.create_deployment_binding(repository_root=symlinked, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)
    assert second.binding.repository_id == first.binding.repository_id
    assert second.binding.canonical_deployment_root == first.binding.canonical_deployment_root
    raw = json.loads((store_root / "registry.json").read_text())
    assert len(raw["deployment_bindings"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# RepositoryIdentity spoofing: known trust boundary, not re-derived
# ═══════════════════════════════════════════════════════════════════════════


def test_copied_identity_file_is_trusted_as_is_known_boundary_not_a_defect(tmp_path: Path) -> None:
    import shutil

    repo_a = _repo(tmp_path, "repoA")
    repo_b = tmp_path / "repoB"
    repo_b.mkdir()
    shutil.copytree(repo_a / ".pcae", repo_b / ".pcae")
    identity_a = read_repository_identity(HarnessPath(repo_a))
    identity_b = read_repository_identity(HarnessPath(repo_b))
    assert identity_a.repository_instance_id == identity_b.repository_instance_id

    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_a, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)
    # repoA and repoB have different canonical_deployment_root (different
    # paths), so the spoofed-identity create is a *conflicting* create, not
    # an idempotent-satisfied one -- still fail-closed, never a silent
    # second/incorrect entry.
    with pytest.raises(admin.DuplicateConflictingBindingError):
        admin.create_deployment_binding(repository_root=repo_b, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)


# ═══════════════════════════════════════════════════════════════════════════
# REQ-042 round trip and theft-defense matching
# ═══════════════════════════════════════════════════════════════════════════


def test_req_042_round_trip_theft_defense(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    identity = read_repository_identity(HarnessPath(repo_root))
    root = resolve_canonical_deployment_root(repo_root)

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(store_root), _protected_root=store_root, _hardware_store_root=store_root)
    store_obj = HATPTrustStore(_test_only_root=store_root)
    loaded = store_obj.load_repository_enrollment(identity.repository_instance_id)

    assert deployment_binding_matches(loaded, repository_id=identity.repository_instance_id, canonical_deployment_root=root)
    assert not deployment_binding_matches(loaded, repository_id=identity.repository_instance_id, canonical_deployment_root="/wrong/root")
    assert not deployment_binding_matches(loaded, repository_id="wrong-id", canonical_deployment_root=root)

    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV", _protected_root=store_root)
    loaded_after_revoke = store_obj.load_repository_enrollment(identity.repository_instance_id)
    assert not deployment_binding_matches(
        loaded_after_revoke, repository_id=identity.repository_instance_id, canonical_deployment_root=root
    )


# ═══════════════════════════════════════════════════════════════════════════
# Arbitrary-root / test-seam: no CLI-reachable protected-root override
# ═══════════════════════════════════════════════════════════════════════════


def test_admin_cli_exposes_no_protected_root_override_flag() -> None:
    for ceremony in ("create", "rotate", "revoke"):
        result = subprocess.run(
            [sys.executable, str(_ADMIN_SCRIPT_PATH), ceremony, "--help"],
            cwd=_REPO_ROOT, capture_output=True, text=True,
        )
        assert "--protected-root" not in result.stdout
        assert "--store-root" not in result.stdout


def test_admin_cli_production_path_defaults_to_real_absent_protected_root_and_writes_nothing(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable, str(_ADMIN_SCRIPT_PATH), "create",
            "--repository-root", str(repo_root),
            "--principal-id", "p1", "--signer-key-id", "s1",
            "--authority-scope", "CLASS_B_DEPLOYMENT",
            "--election-reference", "CHGR-TEST-7J", "--preview",
        ],
        cwd=_REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "DeploymentBindingTrustStoreUnavailableError" in result.stderr


# ═══════════════════════════════════════════════════════════════════════════
# HMIC frozen-source-scope gap (named finding, permanent regression guard
# so this is re-checked automatically once a future phase closes it)
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_frozen_file_set_now_includes_deployment_binding_admin_files() -> None:
    """149O.20L.7J's named HMIC source-scope gap (its own §31 finding) was
    closed by Phase 149O.20L.7K (HMIC-001 v1.3 -> v1.4, contract §55):
    both the DeploymentBinding producer and its admin-ceremony script are
    now HMIC-bound. This guard was originally written asserting the
    opposite (the gap's *presence*, at 7J's own phase-entry state) --
    flipped here, per its own original failure-message instruction, now
    that 7K has closed it. Independent verification of the 7K amendment
    itself belongs to 149O.20L.7L, not here; this guard only re-confirms
    the gap did not silently reopen."""
    cert_src = _CERT_MODULE_PATH.read_text(encoding="utf-8")
    frozen_block_start = cert_src.index("_FROZEN_SRC_PCAE_RELATIVE_FILES")
    frozen_block_end = cert_src.index("_FROZEN_AUTHORITY_BEARING_FILES", frozen_block_start)
    frozen_block = cert_src[frozen_block_start:frozen_block_end]
    assert "hatp_deployment_binding_admin" in frozen_block, (
        "hatp_deployment_binding_admin is no longer in HMIC's frozen file set -- "
        "149O.20L.7K's HMIC source-scope amendment has been reverted or lost"
    )
    # Precedent confirmed: the analogous certification admin script IS frozen.
    assert "hatp_certification_admin.py" in cert_src


def test_hbdc_contract_itself_is_in_hmic_frozen_file_set() -> None:
    cert_src = _CERT_MODULE_PATH.read_text(encoding="utf-8")
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in cert_src


# ═══════════════════════════════════════════════════════════════════════════
# Proof of no operational progression this phase
# ═══════════════════════════════════════════════════════════════════════════


def test_producer_and_admin_script_untouched_by_this_phase() -> None:
    diff = _git("diff", "--stat", "8ef3d2b3", "HEAD", "--", "src/pcae/core/hatp_deployment_binding_admin.py", "scripts/hatp_deployment_binding_admin.py")
    assert diff == ""


def test_no_real_repository_identity_in_this_repositorys_own_working_tree() -> None:
    assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()
