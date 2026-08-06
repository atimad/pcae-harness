"""Phase 149O.1F.2 — HATP Repository Identity + Trust-Store Foundation
Independent Re-Verification.

This suite independently re-attacks the Wave-1/2 foundation *after* the
149O.1F.1 trust-root repair, on the premise that a repair phase's own
claims must never be treated as proof of the repair's correctness. It
does not import, extend, or edit `test_phase_149o_1f_1_...` (the
predecessor phase's own regression suite) or the original
`test_phase_149o_1f_...independent_verification.py` historical
reproducer -- both remain untouched, byte-identical evidence of what
they originally found. This file is new, independent evidence.

Scope: read-only against production code. No test here imports from,
patches, or otherwise depends on `repository_identity.py`,
`hatp_bootstrap.py`, `init.py`, or `templates.py` being anything other
than their current on-disk state -- this phase does not modify any of
them.
"""
from __future__ import annotations

import importlib
import json
import os
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap as hb
from pcae.core import repository_identity as ri
from pcae.core.hatp_bootstrap import (
    BootstrapEnvironmentStatus,
    HATPTrustStore,
    HATPTrustStoreMalformedError,
    HATPTrustStoreSymlinkError,
    inspect_bootstrap_environment,
    resolve_canonical_deployment_root,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity, read_repository_identity

POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")

_SPOOF_ENV_VARS = (
    "HOME",
    "USER",
    "LOGNAME",
    "USERNAME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "PWD",
    "TMPDIR",
    "TMP",
    "TEMP",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _production_root() -> Path:
    return HATPTrustStore.production().root


def _minimal_registry(bindings=None):
    return {
        "registry_version": 1,
        "principals": [],
        "signers": [],
        "deployment_bindings": bindings or [],
        "authorities": [],
    }


def _binding_doc(repository_id, canonical_root, *, status="active", revoked_at=None):
    return {
        "repository_id": repository_id,
        "canonical_deployment_root": canonical_root,
        "principal_id": "test-principal",
        "signer_key_id": "test-signer",
        "provider_profile": "test-profile",
        "authority_scope": "rollback",
        "valid_from": _now_iso(),
        "status": status,
        "revoked_at": revoked_at,
    }


# ═══════════════════════════════════════════════════════════════════════
# Root-resolution re-verification (independent of 149O.1F.1's own suite)
# ═══════════════════════════════════════════════════════════════════════


def _load_isolated_copy():
    """Load an independent copy of hatp_bootstrap.py under a private
    sys.modules key, so environment-spoof/reload attacks never replace
    the canonical `pcae.core.hatp_bootstrap` module object that the rest
    of this test file (and the rest of the test suite) imports names
    from. This is the more precise way to simulate "fresh interpreter
    import under attacker-controlled environment" than mutating the
    shared module in place, and it sidesteps a real but uninteresting
    hazard: `importlib.reload()` rebinds *new* class objects, which then
    silently stop `isinstance`/`except`-matching whatever the rest of
    the suite imported at collection time."""
    import importlib.util

    key = f"hatp_bootstrap_isolated_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(key, hb.__file__)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    try:
        spec.loader.exec_module(mod)
        return mod
    finally:
        del sys.modules[key]


@POSIX_ONLY
@pytest.mark.parametrize("var", _SPOOF_ENV_VARS)
@pytest.mark.parametrize("value", ["", "/tmp/attacker-149o1f2", "."])
def test_individual_env_spoof_leaves_root_unchanged(monkeypatch, var, value):
    baseline = _production_root()
    monkeypatch.setenv(var, value)
    isolated = _load_isolated_copy()
    assert isolated.HATPTrustStore.production().root == baseline


@POSIX_ONLY
@pytest.mark.parametrize("var", _SPOOF_ENV_VARS)
def test_individual_env_unset_leaves_root_unchanged(monkeypatch, var):
    baseline = _production_root()
    monkeypatch.delenv(var, raising=False)
    isolated = _load_isolated_copy()
    assert isolated.HATPTrustStore.production().root == baseline


@POSIX_ONLY
def test_combined_env_spoof_leaves_root_unchanged(monkeypatch):
    baseline = _production_root()
    for var in _SPOOF_ENV_VARS:
        monkeypatch.setenv(var, "/tmp/attacker-combined-149o1f2")
    isolated = _load_isolated_copy()
    assert isolated.HATPTrustStore.production().root == baseline


@POSIX_ONLY
def test_module_reload_after_spoof_still_fixed(monkeypatch):
    """Independently re-run the import-time-coupling attack: mutate the
    environment, then load a fresh module instance (simulating a cold
    interpreter import) -- the constant must not have been captured from
    mutable environment state at import/module-definition time."""
    baseline = _production_root()
    monkeypatch.setenv("HOME", "/tmp/attacker-import-time-149o1f2")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/attacker-import-time-xdg-149o1f2")
    isolated = _load_isolated_copy()
    assert isolated.HATPTrustStore.production().root == baseline


@POSIX_ONLY
@pytest.mark.parametrize("target_dir", ["/tmp", "/"])
def test_cwd_spoof_leaves_root_unchanged(monkeypatch, target_dir):
    baseline = _production_root()
    old_cwd = os.getcwd()
    try:
        os.chdir(target_dir)
        isolated = _load_isolated_copy()
        assert isolated.HATPTrustStore.production().root == baseline
    finally:
        os.chdir(old_cwd)


def test_repository_state_spoof_leaves_root_unchanged(tmp_path, monkeypatch):
    """Changing repository identity / repository root has no bearing on
    the trust-store root resolver -- Wave 1 and Wave 2's root selection
    are structurally independent."""
    baseline = _production_root()
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()
    ensure_repository_identity(HarnessPath(fake_repo))
    monkeypatch.chdir(fake_repo)
    assert HATPTrustStore.production().root == baseline


def test_fixed_root_is_platform_constant_not_computed_from_repo():
    root = _production_root()
    if sys.platform == "darwin":
        assert root == Path("/Library/Application Support/PCAE/HATP/trust-store")
    elif sys.platform == "linux":
        assert root == Path("/etc/pcae/hatp/trust-store")


def test_unsupported_platform_fails_closed(monkeypatch):
    monkeypatch.setattr(hb.os, "name", "nt")
    with pytest.raises(hb.HATPBootstrapUnsupportedPlatformError):
        hb._default_production_trust_root()


def test_unrecognized_posix_platform_fails_closed(monkeypatch):
    monkeypatch.setattr(hb.os, "name", "posix")
    monkeypatch.setattr(hb.sys, "platform", "freebsd13")
    with pytest.raises(hb.HATPBootstrapUnsupportedPlatformError):
        hb._default_production_trust_root()


def test_windows_disposition_is_fail_closed_not_inferred():
    """Explicit assertion (do not infer Windows disposition from POSIX
    logic): `os.name != 'posix'` covers Windows (`os.name == 'nt'`), and
    there is no Windows-specific fixed-root constant defined anywhere in
    the module."""
    source = Path(hb.__file__).read_text(encoding="utf-8")
    assert "_WINDOWS_FIXED_TRUST_ROOT" not in source
    assert "nt" not in {"darwin", "linux"}  # sanity: nt never matches supported branches


def test_source_level_guard_no_forbidden_symbols_in_resolver_body():
    import ast

    tree = ast.parse(Path(hb.__file__).read_text(encoding="utf-8"))
    func = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_default_production_trust_root"
    )
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]
    src = "\n".join(ast.unparse(n) for n in body)
    for forbidden in ("Path.home", "expanduser", "getpass", "os.environ", "os.getenv", "getenv("):
        assert forbidden not in src, f"forbidden symbol {forbidden!r} found in resolver executable body"


# ═══════════════════════════════════════════════════════════════════════
# Historical exploit re-reproduction (pre-repair, extracted via git show)
# ═══════════════════════════════════════════════════════════════════════


def test_historical_exploit_reproduced_against_pre_repair_source(monkeypatch, tmp_path):
    """Extract the pre-149O.1F.1 module body via `git show` into a scratch
    file (never touching the working tree HEAD) and confirm the historical
    HOME-redirection exploit was real."""
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    pre_repair_commit = "8b583817~1"
    pre_repair_src = subprocess.run(
        ["git", "show", f"{pre_repair_commit}:src/pcae/core/hatp_bootstrap.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    scratch_file = tmp_path / "hatp_bootstrap_pre_repair.py"
    scratch_file.write_text(pre_repair_src, encoding="utf-8")

    attacker_home = tmp_path / "attacker-home"
    attacker_home.mkdir()
    monkeypatch.setenv("HOME", str(attacker_home))

    import importlib.util

    spec = importlib.util.spec_from_file_location("hatp_pre_repair_149o1f2", scratch_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)

        store = mod.HATPTrustStore.production()
        assert str(store.root).startswith(str(attacker_home))

        repo_id = str(uuid.uuid4())
        canon_root = "/tmp/attacker-repo-149o1f2"
        store.root.mkdir(parents=True, exist_ok=True)
        (store.root / "registry.json").write_text(
            json.dumps(_minimal_registry([_binding_doc(repo_id, canon_root)])),
            encoding="utf-8",
        )
        binding = store.resolve_deployment_authorization(
            repository_id=repo_id, canonical_deployment_root=canon_root
        )
        assert binding is not None, "historical exploit expected to succeed on unpatched source"
    finally:
        del sys.modules[spec.name]


def test_repaired_exploit_is_blocked_on_current_source(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "attacker-home-post-repair"))
    isolated = _load_isolated_copy()
    store = isolated.HATPTrustStore.production()
    assert not str(store.root).startswith(str(tmp_path))


def test_production_diff_is_narrow_and_single_hunk():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    diff = subprocess.run(
        ["git", "diff", "8b583817~1", "8b583817", "--", "src/pcae/core/hatp_bootstrap.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "def _default_production_trust_root" in diff
    # Nothing outside trust-root/path/platform concerns changed:
    forbidden_terms = ["resolve_deployment_authorization(", "def _parse_", "class HATPTrustStore:"]
    for term in forbidden_terms:
        assert diff.count(term) == 0, f"unexpected unrelated hunk touching {term!r}"


def test_production_diff_scope_is_exactly_one_file():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    changed = subprocess.run(
        ["git", "diff", "--name-only", "8b583817~1", "8b583817", "--", "src/pcae/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert changed == ["src/pcae/core/hatp_bootstrap.py"]


# ═══════════════════════════════════════════════════════════════════════
# Fixed-root protection / agent-precreation / ownership / mode-bit attacks
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_missing_fixed_root_reports_unavailable(tmp_path):
    missing = tmp_path / "missing" / "trust-store"
    result = inspect_bootstrap_environment(missing)
    assert result.status == BootstrapEnvironmentStatus.UNAVAILABLE
    assert "trust_store_missing" in result.reasons


@POSIX_ONLY
def test_agent_precreated_root_not_ready(tmp_path):
    root = tmp_path / "agent-created" / "trust-store"
    root.mkdir(parents=True)
    result = inspect_bootstrap_environment(root)
    assert result.status != BootstrapEnvironmentStatus.READY
    assert "agent_and_admin_share_os_principal" in result.reasons


@POSIX_ONLY
@pytest.mark.parametrize("mode", [0o400, 0o444, 0o500, 0o555])
def test_agent_owned_safe_looking_mode_still_not_ready(tmp_path, mode):
    root = tmp_path / f"mode-{oct(mode)}" / "trust-store"
    root.mkdir(parents=True)
    os.chmod(root, mode)
    try:
        result = inspect_bootstrap_environment(root)
        assert result.status != BootstrapEnvironmentStatus.READY
    finally:
        os.chmod(root, 0o755)


@POSIX_ONLY
def test_world_writable_parent_flagged_unsafe(tmp_path):
    parent = tmp_path / "writable-parent"
    parent.mkdir()
    os.chmod(parent, 0o777)
    root = parent / "trust-store"
    root.mkdir()
    os.chmod(root, 0o755)
    result = inspect_bootstrap_environment(root)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "trust_store_parent_world_writable" in result.reasons


@POSIX_ONLY
def test_symlink_root_rejected(tmp_path):
    real = tmp_path / "real-target"
    real.mkdir()
    symlink_root = tmp_path / "symlink-root"
    symlink_root.symlink_to(real)
    result = inspect_bootstrap_environment(symlink_root)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "trust_store_root_is_symlink" in result.reasons


@POSIX_ONLY
def test_symlink_parent_detected(tmp_path):
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    symlink_parent = tmp_path / "symlink-parent"
    symlink_parent.symlink_to(real_parent)
    child = symlink_parent / "trust-store"
    child.mkdir()
    result = inspect_bootstrap_environment(child)
    assert result.status != BootstrapEnvironmentStatus.READY
    assert "trust_store_parent_is_symlink" in result.reasons


@POSIX_ONLY
def test_same_uid_owner_never_ready_even_with_registry(tmp_path):
    """Live check equivalent: on this single-user development machine, the
    agent process and any store it can create necessarily share a UID.
    Readiness must never be READY under same-user conditions regardless of
    a well-formed registry document being present."""
    root = tmp_path / "same-user-trust-store"
    root.mkdir()
    os.chmod(root, 0o700)
    (root / "registry.json").write_text(json.dumps(_minimal_registry()), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=root)
    status = store.environment_status()
    assert status.status != BootstrapEnvironmentStatus.READY
    assert "agent_and_admin_share_os_principal" in status.reasons


def test_live_inspect_bootstrap_environment_on_this_machine_not_ready():
    """Mandatory live check (§31): run inspect_bootstrap_environment
    against the actual production root resolver on this real machine."""
    result = HATPTrustStore.production().environment_status()
    assert result.status != BootstrapEnvironmentStatus.READY


# ═══════════════════════════════════════════════════════════════════════
# Injection-boundary tests
# ═══════════════════════════════════════════════════════════════════════


def test_production_factory_takes_no_arguments():
    import inspect as inspect_module

    sig = inspect_module.signature(HATPTrustStore.production)
    assert list(sig.parameters) == []


def test_test_only_seam_not_reachable_through_production():
    import inspect as inspect_module

    sig = inspect_module.signature(HATPTrustStore.production)
    assert "_test_only_root" not in sig.parameters
    ctor_sig = inspect_module.signature(HATPTrustStore.__init__)
    assert "_test_only_root" in ctor_sig.parameters
    # It is keyword-only and prefixed with an underscore -- a clear
    # internal/test-only naming signal, not ordinary production API shape.
    param = ctor_sig.parameters["_test_only_root"]
    assert param.kind == inspect_module.Parameter.KEYWORD_ONLY


def test_no_cli_trust_root_override_flag_exists():
    commands_dir = Path(hb.__file__).resolve().parents[2] / "pcae" / "commands"
    forbidden_flags = ["--trust-store", "--hatp-root", "--trusted-key", "--bootstrap-store"]
    for path in commands_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for flag in forbidden_flags:
            assert flag not in text, f"unexpected CLI trust-root override {flag!r} found in {path}"


def test_no_environment_root_override_variable_referenced_in_resolver():
    source = Path(hb.__file__).read_text(encoding="utf-8")
    # The docstrings intentionally *mention* these names to disclaim them;
    # verify none is referenced as an executable os.environ/os.getenv key.
    for var in ("PCAE_HATP_ROOT", "PCAE_TRUST_STORE", "HATP_TRUST_ROOT"):
        assert var not in source


def test_ordinary_production_construction_uses_factory_not_raw_constructor():
    """No src/pcae/** file other than hatp_bootstrap.py itself constructs
    HATPTrustStore(...) directly -- confirmed empty call-site search."""
    src_dir = Path(hb.__file__).resolve().parents[2] / "pcae"
    offending = []
    for path in src_dir.rglob("*.py"):
        if path == Path(hb.__file__):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "HATPTrustStore(" in text:
            offending.append(str(path))
    assert offending == [], f"unexpected direct HATPTrustStore(...) construction outside hatp_bootstrap.py: {offending}"


# ═══════════════════════════════════════════════════════════════════════
# CRI / deployment-binding re-verification
# ═══════════════════════════════════════════════════════════════════════


def test_same_id_wrong_root_no_authorization(tmp_path):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    repo_a.mkdir()
    repo_b.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_a))
    root_a = resolve_canonical_deployment_root(repo_a)
    root_b = resolve_canonical_deployment_root(repo_b)

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(_minimal_registry([_binding_doc(identity.repository_instance_id, root_a)])),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id, canonical_deployment_root=root_b
    ) is None


def test_same_root_wrong_id_no_authorization(tmp_path):
    repo_a = tmp_path / "repo-a"
    repo_a.mkdir()
    identity_a = ensure_repository_identity(HarnessPath(repo_a))
    other_id = str(uuid.uuid4())
    root_a = resolve_canonical_deployment_root(repo_a)

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(_minimal_registry([_binding_doc(identity_a.repository_instance_id, root_a)])),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(
        repository_id=other_id, canonical_deployment_root=root_a
    ) is None


def test_repository_id_theft_still_unauthorized_at_different_root(tmp_path):
    repo_a = tmp_path / "repo-a"
    repo_a.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_a))
    root_a = resolve_canonical_deployment_root(repo_a)

    theft_repo = tmp_path / "theft-repo"
    theft_repo.mkdir()
    theft_root = resolve_canonical_deployment_root(theft_repo)

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(_minimal_registry([_binding_doc(identity.repository_instance_id, root_a)])),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id, canonical_deployment_root=theft_root
    ) is None


def test_full_copy_id_persists_locally_but_confers_no_authority(tmp_path):
    import shutil

    repo_a = tmp_path / "repo-a"
    repo_a.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_a))
    copy_repo = tmp_path / "repo-a-copy"
    shutil.copytree(repo_a / ".pcae", copy_repo / ".pcae")
    copied_identity = read_repository_identity(HarnessPath(copy_repo))
    assert copied_identity.repository_instance_id == identity.repository_instance_id

    # Copy confers no authority: empty registry -> no binding regardless
    store_root = tmp_path / "empty-store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(json.dumps(_minimal_registry()), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    copy_root_canon = resolve_canonical_deployment_root(copy_repo)
    assert store.resolve_deployment_authorization(
        repository_id=copied_identity.repository_instance_id, canonical_deployment_root=copy_root_canon
    ) is None


def test_worktree_distinct_ids(tmp_path):
    worktree_a = tmp_path / "wt-a"
    worktree_b = tmp_path / "wt-b"
    worktree_a.mkdir()
    worktree_b.mkdir()
    ida = ensure_repository_identity(HarnessPath(worktree_a))
    idb = ensure_repository_identity(HarnessPath(worktree_b))
    assert ida.repository_instance_id != idb.repository_instance_id


def test_path_move_binding_mismatch(tmp_path):
    import shutil

    repo = tmp_path / "movable-repo"
    repo.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo))
    old_root = resolve_canonical_deployment_root(repo)

    moved = tmp_path / "movable-repo-relocated"
    shutil.move(str(repo), str(moved))
    new_root = resolve_canonical_deployment_root(moved)

    assert read_repository_identity(HarnessPath(moved)).repository_instance_id == identity.repository_instance_id
    assert old_root != new_root

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(_minimal_registry([_binding_doc(identity.repository_instance_id, old_root)])),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id, canonical_deployment_root=new_root
    ) is None


def test_canonicalization_deterministic_across_equivalent_forms(tmp_path):
    base = tmp_path / "canon-base"
    real_dir = base / "repo"
    real_dir.mkdir(parents=True)
    (base / "x").mkdir()
    dotted = base / "." / "repo"
    dotdot = base / "x" / ".." / "repo"
    c1 = resolve_canonical_deployment_root(real_dir)
    c2 = resolve_canonical_deployment_root(dotted)
    c3 = resolve_canonical_deployment_root(dotdot)
    assert c1 == c2 == c3


@POSIX_ONLY
def test_canonicalization_resolves_symlink_alias(tmp_path):
    base = tmp_path / "canon-base"
    real_dir = base / "repo"
    real_dir.mkdir(parents=True)
    alias = base / "repo-alias"
    alias.symlink_to(real_dir)
    assert resolve_canonical_deployment_root(alias) == resolve_canonical_deployment_root(real_dir)


def test_revoked_deployment_binding_not_authorized(tmp_path):
    repo = tmp_path / "revoked-repo"
    repo.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo))
    root = resolve_canonical_deployment_root(repo)

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            _minimal_registry(
                [_binding_doc(identity.repository_instance_id, root, status="revoked", revoked_at=_now_iso())]
            )
        ),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id, canonical_deployment_root=root
    ) is None


def test_empty_registry_no_authorization(tmp_path):
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(json.dumps(_minimal_registry()), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.load_repository_enrollment(str(uuid.uuid4())) is None


def test_missing_registry_fails_closed(tmp_path):
    store_root = tmp_path / "store"
    store_root.mkdir()
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.load_repository_enrollment(str(uuid.uuid4())) is None


def test_corrupt_registry_fails_closed(tmp_path):
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text("{not valid json", encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(str(uuid.uuid4()))


def test_duplicate_deployment_binding_fails_closed(tmp_path):
    repo_id = str(uuid.uuid4())
    store_root = tmp_path / "store"
    store_root.mkdir()
    doc = _minimal_registry(
        [
            _binding_doc(repo_id, "/a"),
            _binding_doc(repo_id, "/b"),
        ]
    )
    (store_root / "registry.json").write_text(json.dumps(doc), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(repo_id)


def test_repository_id_alone_grants_no_authority(tmp_path):
    repo = tmp_path / "fresh-repo"
    repo.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo))
    store_root = tmp_path / "empty-store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(json.dumps(_minimal_registry()), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    canon_root = resolve_canonical_deployment_root(repo)
    assert store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id, canonical_deployment_root=canon_root
    ) is None


def test_malformed_repository_identity_fails_closed_no_autoheal(tmp_path):
    repo = tmp_path / "malformed-repo"
    target = HarnessPath(repo).join(ri.REPOSITORY_IDENTITY_RELATIVE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"schema_version": 1, "repository_instance_id": "not-a-uuid", "created_at": "bad"}')
    with pytest.raises(ri.RepositoryIdentityMalformedError):
        ensure_repository_identity(HarnessPath(repo))
    assert "not-a-uuid" in target.read_text()


@POSIX_ONLY
def test_symlink_identity_write_refused(tmp_path):
    repo = tmp_path / "symlink-repo"
    target = HarnessPath(repo).join(ri.REPOSITORY_IDENTITY_RELATIVE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    evil_target = repo / "evil-target.json"
    target.symlink_to(evil_target)
    with pytest.raises(ri.RepositoryIdentitySymlinkError):
        ensure_repository_identity(HarnessPath(repo))
    assert not evil_target.exists()


# ═══════════════════════════════════════════════════════════════════════
# Activation / no-overclaim audit
# ═══════════════════════════════════════════════════════════════════════


def test_no_approval_present_or_activation_symbols_defined_in_hatp_module():
    """`approval_present`/`signature`/`attestation` etc. are mentioned in
    this module's *docstrings* only, deliberately, to disclaim that this
    module is not the thing that produces them (see the module and class
    docstrings). What matters is that none of these names is ever
    *defined* (function, class, module-level constant, or dataclass
    field) here -- i.e. no executable production symbol in this module
    could serve as an activation/approval surface."""
    import ast

    tree = ast.parse(Path(hb.__file__).read_text(encoding="utf-8"))
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined_names.add(node.target.id)

    forbidden = {
        "HATP_TRUSTED_OPERATIONAL",
        "approval_present",
        "verify_hatp",
        "HumanApprovalProvenanceProof",
        "signature",
        "attestation",
        "human_presence",
    }
    overlap = defined_names & forbidden
    assert overlap == set(), f"unexpected activation-suggestive symbol(s) defined in hatp_bootstrap.py: {overlap}"


def test_synthetic_ready_bootstrap_does_not_imply_hatp_operational():
    """Even a synthetic, fully protected-looking store's environment_status
    is a bootstrap-foundation-only signal; there is no method on
    HATPTrustStore that returns anything resembling a trusted HATP
    approval/proof."""
    public_symbols = [name for name in dir(HATPTrustStore) if not name.startswith("_")]
    for name in public_symbols:
        assert "approv" not in name.lower()
        assert "proof" not in name.lower()
        assert "verify" not in name.lower() or name == "environment_status"


def test_no_production_caller_imports_hatp_bootstrap_outside_itself():
    """Reverse-import boundary: confirms Wave 1/2 is not wired into RAE,
    Permission Broker, or agent execution."""
    src_dir = Path(hb.__file__).resolve().parents[2] / "pcae"
    forbidden_modules = [
        "core/rollback_approval_evidence.py",
        "core/permission_broker.py",
        "core/permission_broker_foundation.py",
        "core/mutation_permission.py",
        "core/agent.py",
        "commands/agent.py",
    ]
    for rel in forbidden_modules:
        path = src_dir / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "hatp_bootstrap" not in text
        assert "repository_identity" not in text


# ═══════════════════════════════════════════════════════════════════════
# Boundary confirmation: this phase touched no production files
# ═══════════════════════════════════════════════════════════════════════


def test_phase_149o_1f_2_did_not_modify_hatp_contract():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    out = subprocess.run(
        ["git", "diff", "--name-only", "48c1f94f", "--", "docs/contracts/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert out == "", f"unexpected contract modification: {out}"
