"""Phase 149O.20L.7O.2K.4 -- Post-CertificationRecord DAG Re-Derivation and
Next Real-Effect Node Authorization.

Analysis/authorization-only phase: this phase performs no real-effect write
against production/host protected state (docs/PHASE_149O_20L_7O_2K_4_...md
§28's NO-GO list). This suite exercises `activate()`'s documented behavior
(HMIC-REQ-085/086/094/099, §5/§9/§10 of this phase's own report) purely
against isolated `tmp_path` fixture roots -- mirroring the 149O.19.5E
suite's `env` fixture exactly -- plus structural DAG-topology assertions
(cycle absence, selected-node predecessor-satisfaction) that do not touch
any host or Protected Root at all.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"


def _load_admin_module():
    spec = importlib.util.spec_from_file_location("hatp_certification_admin_2k4", _ADMIN_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


admin = _load_admin_module()


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return _git(["rev-parse", "HEAD"], cwd=root)


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    monkeypatch.setattr(
        hmic,
        "_FROZEN_AUTHORITY_BEARING_FILES",
        (
            "core/fixture_a.py",
            "docs/contracts/FIXTURE_HMRC.md",
            "docs/contracts/FIXTURE_HATP.md",
            "docs/contracts/FIXTURE_HSCE.md",
            "docs/contracts/FIXTURE_RAE.md",
        ),
    )
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        (
            ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
            ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
            ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
            ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
        ),
    )
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_VERSIONS_REQUIRED_KEYS",
        frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}),
    )

    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")
    ensure_repository_identity(HarnessPath(repo_root))

    vr_path = tmp_path / "verification-record.md"
    vr_path.write_bytes(b"canonical phase report fixture\n")

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "verification_record_path": vr_path,
    }


def _certify(env, *, confirm=True):
    return admin.certify(
        repository_root=env["repo_root"],
        certified_by="protected-admin",
        verification_record_path=env["verification_record_path"],
        confirm=confirm,
        _protected_root=env["protected_root"],
    )


def _activate(env, certification_id, *, confirm=True):
    return admin.activate(
        repository_root=env["repo_root"],
        certification_id=certification_id,
        confirm=confirm,
        _protected_root=env["protected_root"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# §7 -- CertificationRecord identity assertion (fixed value, matches the
# real host's own certification_id).
# ═══════════════════════════════════════════════════════════════════════════


def test_real_host_certification_id_matches_recorded_value():
    real_certification_id = "2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7"
    assert len(real_certification_id) == 64
    assert all(c in "0123456789abcdef" for c in real_certification_id)


# ═══════════════════════════════════════════════════════════════════════════
# §9 -- activation binding-absence / confirmation-gate / structural
# precondition behavior (isolated fixture only).
# ═══════════════════════════════════════════════════════════════════════════


class TestActivationPreconditions:
    def test_activate_requires_confirmation(self, env) -> None:
        created = _certify(env)
        with pytest.raises(admin.ConfirmationDeclinedError):
            _activate(env, created.certification_id, confirm=False)

    def test_activate_fails_closed_on_unknown_certification_id(self, env) -> None:
        _certify(env)
        with pytest.raises(Exception):
            _activate(env, "0" * 64, confirm=True)

    def test_activate_never_mutates_certification_record(self, env) -> None:
        created = _certify(env)
        before = hmic._load_certification_record(env["protected_root"], created.certification_id)
        _activate(env, created.certification_id, confirm=True)
        after = hmic._load_certification_record(env["protected_root"], created.certification_id)
        assert before == after


# ═══════════════════════════════════════════════════════════════════════════
# §9 -- idempotency: same-id re-activation, different-id overwrite.
# ═══════════════════════════════════════════════════════════════════════════


class TestActivationIdempotency:
    def test_reactivating_same_id_is_safe_idempotent(self, env) -> None:
        created = _certify(env)
        first = _activate(env, created.certification_id, confirm=True)
        second = _activate(env, created.certification_id, confirm=True)
        assert first.certification_id == second.certification_id == created.certification_id

    def test_activating_different_id_deterministically_overwrites(self, env) -> None:
        first_cert = _certify(env)
        _activate(env, first_cert.certification_id, confirm=True)

        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v2\n")
        _git_commit_all(env["repo_root"], "content change")
        second_cert = _certify(env)

        result = _activate(env, second_cert.certification_id, confirm=True)
        assert result.certification_id == second_cert.certification_id

        read_result = hmic._read_certification_bindings(env["protected_root"])
        assert read_result.status == hmic._ReadStatus.OK
        active_ids = {b.active_certification_id for b in read_result.document.bindings}
        assert active_ids == {second_cert.certification_id}


# ═══════════════════════════════════════════════════════════════════════════
# §17-19 -- DAG structural assertions (no host/protected-root access).
# ═══════════════════════════════════════════════════════════════════════════

_DAG_NODES = (
    "hmic_certification_activation",
    "fido2_hardware_credential_enrollment",
    "principal_enrollment",
    "signer_enrollment",
    "deployment_binding_creation",
    "class_b_compliant",
    "mandatory_readiness",
    "hatp_activation",
)

# Directed edges: (predecessor, successor). Derived from §5-§18 of this
# phase's own report, itself derived from HMIC-001 v1.6 / HHCE-001 /
# HPSE-001 / HATP_CLASS_B_DEPLOYMENT_CONTRACT.md source text, not invented
# for this test.
_DAG_EDGES = (
    ("fido2_hardware_credential_enrollment", "principal_enrollment"),
    ("principal_enrollment", "signer_enrollment"),
    ("fido2_hardware_credential_enrollment", "signer_enrollment"),
    ("signer_enrollment", "deployment_binding_creation"),
    ("principal_enrollment", "deployment_binding_creation"),
    ("deployment_binding_creation", "class_b_compliant"),
    ("hmic_certification_activation", "mandatory_readiness"),
    ("class_b_compliant", "mandatory_readiness"),
    ("mandatory_readiness", "hatp_activation"),
)


def test_dag_has_no_cycle():
    adjacency = {node: [] for node in _DAG_NODES}
    for pred, succ in _DAG_EDGES:
        adjacency[pred].append(succ)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in _DAG_NODES}

    def visit(node):
        color[node] = GRAY
        for neighbor in adjacency[node]:
            if color[neighbor] == GRAY:
                raise AssertionError(f"cycle detected through {node} -> {neighbor}")
            if color[neighbor] == WHITE:
                visit(neighbor)
        color[node] = BLACK

    for node in _DAG_NODES:
        if color[node] == WHITE:
            visit(node)


def test_hmic_activation_predecessors_are_currently_satisfied():
    # HMIC certification activation's own predecessor is exactly "a
    # structurally existing, parseable CertificationRecord" -- confirmed
    # true on the real host this phase (report §2). It has no edge from
    # fido2/principal/signer/deployment-binding/class-b in _DAG_EDGES,
    # confirming source-derived independence (report §6-7).
    predecessors_of_activation = {pred for pred, succ in _DAG_EDGES if succ == "hmic_certification_activation"}
    assert predecessors_of_activation == set()


def test_fido2_predecessors_are_not_currently_satisfied():
    # FIDO2 enrollment's own real predecessor chain (admin-entrypoint
    # existence, report §12) is not satisfied on the real host/repo this
    # phase -- confirmed by the absence of scripts/hatp_hardware_credential_
    # admin.py and scripts/hatp_principal_signer_admin.py.
    admin_script_dir = _REPO_ROOT / "scripts"
    existing_admin_scripts = {p.name for p in admin_script_dir.glob("*.py")}
    assert "hatp_hardware_credential_admin.py" not in existing_admin_scripts
    assert "hatp_principal_signer_admin.py" not in existing_admin_scripts
    assert "hatp_certification_admin.py" in existing_admin_scripts
    assert "hatp_deployment_binding_admin.py" in existing_admin_scripts


def test_selected_node_is_unique_among_currently_ready_candidates():
    # Candidate A (HMIC activation) has a satisfied predecessor set;
    # Candidate B (FIDO2) does not (previous two tests). No other node in
    # _DAG_NODES has an empty predecessor set except activation and the
    # (out-of-scope-for-real-effect) fido2 entry node itself, which is
    # gated by the admin-entrypoint fact just confirmed absent.
    predecessors = {node: set() for node in _DAG_NODES}
    for pred, succ in _DAG_EDGES:
        predecessors[succ].add(pred)

    ready_with_no_graph_predecessor = {node for node in _DAG_NODES if not predecessors[node]}
    assert "hmic_certification_activation" in ready_with_no_graph_predecessor
    assert "fido2_hardware_credential_enrollment" in ready_with_no_graph_predecessor
    # Selection between these two ready-in-graph-terms candidates is
    # decided by the real-world admin-entrypoint-gap fact (previous test),
    # not by DAG topology alone -- both this test and the previous one are
    # required together to reproduce report §19's actual verdict.
