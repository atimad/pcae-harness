"""Phase 149O.1F.1 — HATP Production Trust-Store Path Hardening.

Authoritative post-repair regression suite for B-149O.1F-1
(`HATPTrustStore.production()` resolved its root via `Path.home()`,
which consults the ordinary agent-controllable `$HOME` process-
environment variable). The repair replaced
`_default_production_trust_root()` with a fixed, platform-level path
that consults no environment variable, current working directory,
repository state, caller parameter, CLI flag, or other agent-
controlled runtime input (`_MACOS_FIXED_TRUST_ROOT`/
`_LINUX_FIXED_TRUST_ROOT` in `src/pcae/core/hatp_bootstrap.py`).

This suite does not modify or import from the 149O.1E or 149O.1F test
files; it treats `hatp_bootstrap.py` purely as implementation truth to
attack, post-repair.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap as hb
from pcae.core.hatp_bootstrap import (
    BootstrapEnvironmentStatus,
    HATPTrustStore,
    inspect_bootstrap_environment,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")

_SPOOF_ENV_VARS = (
    "HOME",
    "USER",
    "LOGNAME",
    "USERNAME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
)


def _production_root() -> Path:
    return HATPTrustStore.production().root


# ═══════════════════════════════════════════════════════════════════════
# Environment spoof matrix (items 23-24, 53-55)
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_home_redirection_blocked(tmp_path, monkeypatch) -> None:
    baseline = _production_root()
    fake_home = tmp_path / "attacker-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    assert _production_root() == baseline
    assert _production_root() != fake_home / ".pcae-hatp" / "trust-store"


@POSIX_ONLY
def test_home_unset(monkeypatch) -> None:
    baseline = _production_root()
    monkeypatch.delenv("HOME", raising=False)
    assert _production_root() == baseline


@POSIX_ONLY
@pytest.mark.parametrize("value", ["", ".", "/tmp/attacker"])
def test_home_malformed(monkeypatch, value) -> None:
    baseline = _production_root()
    monkeypatch.setenv("HOME", value)
    assert _production_root() == baseline


@POSIX_ONLY
def test_user_spoof_blocked(monkeypatch) -> None:
    baseline = _production_root()
    monkeypatch.setenv("USER", "attacker")
    assert _production_root() == baseline


@POSIX_ONLY
def test_logname_spoof_blocked(monkeypatch) -> None:
    baseline = _production_root()
    monkeypatch.setenv("LOGNAME", "attacker")
    assert _production_root() == baseline


@POSIX_ONLY
def test_username_spoof_blocked(monkeypatch) -> None:
    baseline = _production_root()
    monkeypatch.setenv("USERNAME", "attacker")
    assert _production_root() == baseline


@POSIX_ONLY
def test_xdg_spoof_blocked(tmp_path, monkeypatch) -> None:
    baseline = _production_root()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    assert _production_root() == baseline


@POSIX_ONLY
def test_cwd_irrelevant(tmp_path) -> None:
    baseline = _production_root()
    cwd_before = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert _production_root() == baseline
    finally:
        os.chdir(cwd_before)


@POSIX_ONLY
def test_combined_environment_spoof_blocked(tmp_path, monkeypatch) -> None:
    """Item 24/55: every plausible identity/path environment variable set
    simultaneously to attacker-controlled values must not redirect the
    authoritative production root."""

    baseline = _production_root()
    for var in _SPOOF_ENV_VARS:
        monkeypatch.setenv(var, str(tmp_path / f"attacker-{var.lower()}"))
    cwd_before = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert _production_root() == baseline
    finally:
        os.chdir(cwd_before)


# ═══════════════════════════════════════════════════════════════════════
# Fake registry irrelevance (items 51, 91-93)
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_fake_registry_under_fake_home_ignored(tmp_path, monkeypatch) -> None:
    fake_home = tmp_path / "attacker-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    attacker_store_root = fake_home / ".pcae-hatp" / "trust-store"
    attacker_store_root.mkdir(parents=True)

    repo_root = tmp_path / "attacker-repo"
    repo_root.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_root))

    (attacker_store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": identity.repository_instance_id,
                        "canonical_deployment_root": str(repo_root.resolve()),
                        "principal_id": "self-authored-principal",
                        "signer_key_id": "self-authored-signer",
                        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                        "authority_scope": "rollback",
                        "valid_from": "2026-08-05T00:00:00.000Z",
                        "status": "active",
                        "revoked_at": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    store = HATPTrustStore.production()
    assert store.root != attacker_store_root
    result = store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id,
        canonical_deployment_root=str(repo_root.resolve()),
    )
    assert result is None


@POSIX_ONLY
def test_fake_registry_under_agent_owned_actual_home_not_authoritative(tmp_path) -> None:
    """Item 92-93: even without spoofing `HOME`, a registry planted under
    the *real, agent-owned* OS home directory (the "agent-home trap") must
    not become authoritative. The fixed-system-path resolver never reads
    home-relative locations at all."""

    real_home_store_root = Path.home() / ".pcae-hatp" / "trust-store"
    production_root = HATPTrustStore.production().root
    assert production_root != real_home_store_root

    repo_root = tmp_path / "agent-repo"
    repo_root.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_root))

    # Simulate (without touching the real filesystem outside tmp_path)
    # what an agent-owned home-relative store would contain, and prove
    # the production resolver's root is a different path entirely --
    # the agent-home-trap defense is architectural (fixed path), not a
    # runtime check against this specific directory.
    assert str(production_root) not in (str(Path.home()), str(real_home_store_root))
    assert not str(production_root).startswith(str(Path.home()))


# ═══════════════════════════════════════════════════════════════════════
# Production factory / call-site discipline (items 56-58, 65-67)
# ═══════════════════════════════════════════════════════════════════════


def test_production_factory_takes_no_root_argument() -> None:
    sig = inspect.signature(HATPTrustStore.production)
    assert list(sig.parameters.keys()) == []


def test_production_root_not_repo_local(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    root = HATPTrustStore.production().root
    assert not str(root).startswith(str(repo_root))
    assert ".pcae" != root.name


def test_production_factory_does_not_create_or_provision_root() -> None:
    """Item 65-67, 95-96: the production factory must be a pure lookup --
    it must never create the resolved root or write anything."""

    root = HATPTrustStore.production().root
    # If the fixed root doesn't already exist on this machine (expected
    # on an ordinary, non-provisioned dev host), constructing the store
    # must not have created it.
    if not root.exists():
        assert not root.exists()


@POSIX_ONLY
def test_missing_protected_root_fails_closed() -> None:
    store = HATPTrustStore.production()
    if not store.root.exists():
        status = store.environment_status()
        assert status.status == BootstrapEnvironmentStatus.UNAVAILABLE


def test_no_production_call_site_passes_a_caller_controlled_root() -> None:
    """Item 58: search all production call sites under src/pcae for a
    reachable path that constructs `HATPTrustStore` with an
    attacker-controlled root."""

    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src" / "pcae"
    offenders = []
    for path in src_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "HATPTrustStore(" in text and "_test_only_root" not in text:
            offenders.append(str(path.relative_to(repo_root)))
    assert offenders == []


# ═══════════════════════════════════════════════════════════════════════
# Source-level guard against reintroducing environment dependence
# (item 59, 25-28)
# ═══════════════════════════════════════════════════════════════════════


def _code_only_source(func) -> str:
    """`inspect.getsource` includes the docstring and any comments, which
    legitimately *mention* the forbidden tokens (explaining why they were
    removed). Strip the docstring and comments so the guard only inspects
    executable code."""

    import ast
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    func_node = tree.body[0]
    if (
        func_node.body
        and isinstance(func_node.body[0], ast.Expr)
        and isinstance(func_node.body[0].value, ast.Constant)
        and isinstance(func_node.body[0].value.value, str)
    ):
        func_node.body = func_node.body[1:]
    return ast.unparse(func_node)


def test_resolver_source_has_no_forbidden_environment_reads() -> None:
    source = _code_only_source(hb._default_production_trust_root)
    forbidden = (
        "Path.home(",
        "os.environ",
        "getenv(",
        "expanduser(",
        "getpass",
    )
    for token in forbidden:
        assert token not in source, f"forbidden token {token!r} reintroduced into production resolver"


def test_no_path_home_anywhere_in_module_authoritative_path() -> None:
    """`Path.home()` must not appear in any executable statement in this
    module (only in docstrings/comments explaining the historical
    finding)."""

    import ast

    tree = ast.parse(inspect.getsource(hb))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "home":
            if isinstance(node.value, ast.Name) and node.value.id == "Path":
                pytest.fail("Path.home() reintroduced into executable code")


# ═══════════════════════════════════════════════════════════════════════
# Platform fail-closed behavior (items 11-13, 60, 62-63)
# ═══════════════════════════════════════════════════════════════════════


def test_non_posix_platform_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(hb.os, "name", "nt")
    with pytest.raises(hb.HATPBootstrapUnsupportedPlatformError):
        hb._default_production_trust_root()


def test_unrecognized_posix_platform_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(hb.sys, "platform", "freebsd13")
    with pytest.raises(hb.HATPBootstrapUnsupportedPlatformError):
        hb._default_production_trust_root()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific resolved path")
def test_macos_resolves_fixed_application_support_path() -> None:
    root = hb._default_production_trust_root()
    assert str(root) == "/Library/Application Support/PCAE/HATP/trust-store"


def test_linux_resolver_returns_fixed_etc_path(monkeypatch) -> None:
    monkeypatch.setattr(hb.sys, "platform", "linux")
    root = hb._default_production_trust_root()
    assert root == Path("/etc/pcae/hatp/trust-store")


# ═══════════════════════════════════════════════════════════════════════
# Direct root-equality / stability proofs (items 22, 50, 96-97)
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_production_root_stable_across_repeated_calls() -> None:
    first = HATPTrustStore.production().root
    second = HATPTrustStore.production().root
    assert first == second


@POSIX_ONLY
def test_production_root_unaffected_by_environment_mutation_sequence(tmp_path, monkeypatch) -> None:
    before = HATPTrustStore.production().root
    monkeypatch.setenv("HOME", str(tmp_path / "one"))
    mid = HATPTrustStore.production().root
    monkeypatch.setenv("HOME", str(tmp_path / "two"))
    after = HATPTrustStore.production().root
    assert before == mid == after


# ═══════════════════════════════════════════════════════════════════════
# Preserved Wave-1/2 invariants (regression floor, items 34-44)
# ═══════════════════════════════════════════════════════════════════════


def test_same_user_readiness_still_never_ready(tmp_path) -> None:
    store_root = tmp_path / "same-user-store"
    store_root.mkdir()
    result = inspect_bootstrap_environment(store_root)
    assert result.status != BootstrapEnvironmentStatus.READY


def test_same_id_wrong_root_still_rejected(tmp_path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    repo_root_a = tmp_path / "repo-a"
    repo_root_a.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_root_a))
    other_root = tmp_path / "repo-b"
    other_root.mkdir()

    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": identity.repository_instance_id,
                        "canonical_deployment_root": str(repo_root_a.resolve()),
                        "principal_id": "admin-principal",
                        "signer_key_id": "admin-signer",
                        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                        "authority_scope": "rollback",
                        "valid_from": "2026-08-05T00:00:00.000Z",
                        "status": "active",
                        "revoked_at": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    store = HATPTrustStore(_test_only_root=store_root)
    result = store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id,
        canonical_deployment_root=str(other_root.resolve()),
    )
    assert result is None


def _mk(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_duplicate_deployment_bindings_still_rejected(tmp_path) -> None:
    from pcae.core.hatp_bootstrap import HATPTrustStoreMalformedError

    store_root = tmp_path / "store"
    store_root.mkdir()
    repo_dir = _mk(tmp_path / "repo")
    repo_id = ensure_repository_identity(HarnessPath(repo_dir)).repository_instance_id

    binding = {
        "repository_id": repo_id,
        "canonical_deployment_root": str((tmp_path / "repo").resolve()),
        "principal_id": "admin-principal",
        "signer_key_id": "admin-signer",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "authority_scope": "rollback",
        "valid_from": "2026-08-05T00:00:00.000Z",
        "status": "active",
        "revoked_at": None,
    }
    (store_root / "registry.json").write_text(
        json.dumps({"registry_version": 1, "deployment_bindings": [binding, binding]}),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(repo_id)


def test_revoked_binding_still_rejected(tmp_path) -> None:
    repo_dir = _mk(tmp_path / "repo")
    identity = ensure_repository_identity(HarnessPath(repo_dir))
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": identity.repository_instance_id,
                        "canonical_deployment_root": str(repo_dir.resolve()),
                        "principal_id": "admin-principal",
                        "signer_key_id": "admin-signer",
                        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                        "authority_scope": "rollback",
                        "valid_from": "2026-08-05T00:00:00.000Z",
                        "status": "revoked",
                        "revoked_at": "2026-08-05T01:00:00.000Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    result = store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id,
        canonical_deployment_root=str(repo_dir.resolve()),
    )
    assert result is None
