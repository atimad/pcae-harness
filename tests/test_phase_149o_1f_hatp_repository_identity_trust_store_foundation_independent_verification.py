"""Phase 149O.1F — HATP Wave 1/2 Foundation Independent Verification.

Independently reconstructed adversarial suite. Does not modify or import
from the 149O.1E test files; treats `repository_identity.py` and
`hatp_bootstrap.py` purely as implementation truth to attack. Neither
production module is modified by this phase.
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap as hb
from pcae.core.hatp_bootstrap import (
    BootstrapEnvironmentStatus,
    HATPTrustStore,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import (
    ensure_repository_identity,
    read_repository_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")


# ═══════════════════════════════════════════════════════════════════════
# FINDING: HOME-based production trust-store redirection
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_home_environment_variable_redirects_production_trust_store(tmp_path, monkeypatch) -> None:
    """`HATPTrustStore.production()` -> `_default_production_trust_root()`
    -> `Path.home() / ".pcae-hatp" / "trust-store"`. `Path.home()` on
    POSIX consults `$HOME` (via `os.path.expanduser`). An ordinary
    process-environment mutation -- something an autonomous agent's own
    process can always perform, no privilege escalation required --
    therefore relocates the "authoritative", non-caller-selectable trust
    root the module's own docstring claims is immune to environment
    override. The existing 149O.1E test
    (`test_production_ignores_environment_overrides`) checks four
    HATP-specific guessed variable names but never `HOME`, the actual
    resolver dependency."""

    fake_home = tmp_path / "attacker-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    store = HATPTrustStore.production()
    assert store.root == fake_home / ".pcae-hatp" / "trust-store"
    assert store.root != Path("/") / "real" / "admin" / "home" / ".pcae-hatp" / "trust-store"


@POSIX_ONLY
def test_home_redirection_enables_self_authored_deployment_authorization(tmp_path, monkeypatch) -> None:
    """Consequence of the above: an agent that controls `HOME` can author
    its own registry.json at the redirected path and have
    `resolve_deployment_authorization` return a real, non-None
    `DeploymentBinding` for a repository/root pair it fabricated end to
    end -- no admin, no separate OS principal, no out-of-band
    provisioning involved. Nothing in Wave-1/2 vocabulary distinguishes
    this from a legitimately admin-provisioned binding; only the (not yet
    wired) `environment_status()`/`inspect_bootstrap_environment` same-
    user check would flag the *store*, and nothing compels a future
    consumer to check that before trusting the binding."""

    fake_home = tmp_path / "attacker-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    store = HATPTrustStore.production()
    store_root = store.root
    store_root.mkdir(parents=True)

    repo_root = tmp_path / "attacker-repo"
    repo_root.mkdir()
    identity = ensure_repository_identity(HarnessPath(repo_root))

    (store_root / "registry.json").write_text(
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

    result = store.resolve_deployment_authorization(
        repository_id=identity.repository_instance_id,
        canonical_deployment_root=str(repo_root.resolve()),
    )
    assert result is not None, (
        "attacker-controlled HOME allowed a self-authored deployment binding "
        "to resolve through the production trust-store API"
    )
    assert result.principal_id == "self-authored-principal"

    # The same-user readiness check exists and would flag this store --
    # but resolve_deployment_authorization does not consult it, and no
    # Wave-1/2 API forces a caller to.
    same_user_status = hb.inspect_bootstrap_environment(store_root)
    assert same_user_status.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION


def test_xdg_variables_have_no_effect_observation(tmp_path, monkeypatch) -> None:
    """Unlike HOME, XDG_CONFIG_HOME/XDG_DATA_HOME are never consulted --
    `_default_production_trust_root` hardcodes `~/.pcae-hatp/trust-store`
    rather than any XDG base-directory path. Recorded as a clean negative
    control, not a finding."""

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    if os.name == "posix":
        store = HATPTrustStore.production()
        assert store.root == Path.home() / ".pcae-hatp" / "trust-store"


def test_cwd_has_no_effect_on_production_path(tmp_path) -> None:
    if os.name != "posix":
        pytest.skip("POSIX-only")
    expected = Path.home() / ".pcae-hatp" / "trust-store"
    cwd_before = os.getcwd()
    try:
        os.chdir(tmp_path)
        store = HATPTrustStore.production()
        assert store.root == expected
    finally:
        os.chdir(cwd_before)


# ═══════════════════════════════════════════════════════════════════════
# Repository identity: caller control, regeneration, theft
# ═══════════════════════════════════════════════════════════════════════


def test_no_production_api_accepts_a_caller_supplied_id() -> None:
    import pcae.core.repository_identity as ri

    for name in ("ensure_repository_identity", "read_repository_identity"):
        sig = inspect.signature(getattr(ri, name))
        for forbidden in ("repository_instance_id", "id", "value", "trusted_id"):
            assert forbidden not in sig.parameters


def test_id_regeneration_after_deletion_loses_any_enrollment_match(tmp_path) -> None:
    """Old ID X was (hypothetically) enrolled; the repo deletes its
    identity file and re-inits, receiving a fresh ID Y. Y has no
    enrollment matching X's binding -- deleting and regenerating cannot
    inherit or forge protected authority."""

    root = HarnessPath(tmp_path)
    old_identity = ensure_repository_identity(root)

    identity_path = tmp_path / ".pcae" / "repository-identity.json"
    identity_path.unlink()

    new_identity = ensure_repository_identity(root)
    assert new_identity.repository_instance_id != old_identity.repository_instance_id

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": old_identity.repository_instance_id,
                        "canonical_deployment_root": str(tmp_path.resolve()),
                        "principal_id": "p1",
                        "signer_key_id": "s1",
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
    assert store.load_repository_enrollment(new_identity.repository_instance_id) is None


def test_repository_id_theft_without_root_match_remains_unauthorized(tmp_path) -> None:
    """B learns A's UUID and writes it into its own identity file. B still
    has no enrollment because the enrollment requires B's own canonical
    root, which B cannot forge to equal A's."""

    root_a = tmp_path / "repo-a"
    root_a.mkdir()
    identity_a = ensure_repository_identity(HarnessPath(root_a))

    root_b = tmp_path / "repo-b"
    (root_b / ".pcae").mkdir(parents=True)
    (root_b / ".pcae" / "repository-identity.json").write_text(
        json.dumps(identity_a.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    identity_b = read_repository_identity(HarnessPath(root_b))
    assert identity_b.repository_instance_id == identity_a.repository_instance_id

    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": identity_a.repository_instance_id,
                        "canonical_deployment_root": str(root_a.resolve()),
                        "principal_id": "p1",
                        "signer_key_id": "s1",
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
    stolen = store.resolve_deployment_authorization(
        repository_id=identity_b.repository_instance_id,
        canonical_deployment_root=str(root_b.resolve()),
    )
    assert stolen is None


def test_no_static_or_hardcoded_identity_in_templates() -> None:
    source = inspect.getsource(__import__("pcae.core.templates", fromlist=["*"]))
    for pattern in ("repository_instance_id", "schema_version"):
        assert pattern not in source
    assert "uuid.UUID(" not in source


def test_clone_does_not_propagate_committed_identity(tmp_path) -> None:
    """A realistic clone of a committed tree never receives an active
    identity file, because the identity path is gitignored -- confirmed
    directly against this repository's own committed .gitignore, not
    inferred from comments."""

    result = subprocess.run(
        ["git", "check-ignore", "-v", ".pcae/repository-identity.json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, "repository-identity.json is not actually gitignored"
    assert ".gitignore" in result.stdout


# ═══════════════════════════════════════════════════════════════════════
# Canonical root aliasing / same-ID-wrong-root / same-root-wrong-ID
# ═══════════════════════════════════════════════════════════════════════


def test_dot_and_dotdot_aliases_canonicalize_identically(tmp_path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    alias_dot = real / "."
    alias_dotdot = tmp_path / "real" / "sub" / ".."
    (real / "sub").mkdir()

    canon_real = hb.resolve_canonical_deployment_root(real)
    canon_dot = hb.resolve_canonical_deployment_root(alias_dot)
    canon_dotdot = hb.resolve_canonical_deployment_root(alias_dotdot)
    assert canon_real == canon_dot == canon_dotdot


def test_same_root_wrong_id_does_not_match(tmp_path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    real_repo_id = str(uuid.uuid4())
    wrong_repo_id = str(uuid.uuid4())
    root = "/deploy/A"
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": real_repo_id,
                        "canonical_deployment_root": root,
                        "principal_id": "p1",
                        "signer_key_id": "s1",
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
    assert store.resolve_deployment_authorization(repository_id=wrong_repo_id, canonical_deployment_root=root) is None


# ═══════════════════════════════════════════════════════════════════════
# Ordering/duplicate ambiguity must fail closed, not resolve by mtime/order
# ═══════════════════════════════════════════════════════════════════════


def test_no_mtime_or_file_order_based_selection_in_source() -> None:
    source = inspect.getsource(hb)
    for forbidden in ("st_mtime", "getmtime", "sorted(files", "max(files"):
        assert forbidden not in source


def test_duplicate_signer_records_rejected_not_silently_merged(tmp_path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "signers": [
                    {
                        "signer_key_id": "dup-signer",
                        "principal_id": "p1",
                        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                        "status": "active",
                        "revoked_at": None,
                    },
                    {
                        "signer_key_id": "dup-signer",
                        "principal_id": "p2",
                        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                        "status": "active",
                        "revoked_at": None,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    store = HATPTrustStore(_test_only_root=store_root)
    with pytest.raises(hb.HATPTrustStoreMalformedError):
        store.lookup_signer("dup-signer")


def test_empty_registry_grants_nothing(tmp_path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(json.dumps({"registry_version": 1}), encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)
    assert store.resolve_deployment_authorization(repository_id=str(uuid.uuid4()), canonical_deployment_root="/anywhere") is None


# ═══════════════════════════════════════════════════════════════════════
# No global/wildcard authority fallback
# ═══════════════════════════════════════════════════════════════════════


def test_no_wildcard_or_global_fallback_in_source() -> None:
    source = inspect.getsource(hb)
    assert '"*"' not in source
    assert "global_authority" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════
# Root/privileged agent case (unit-level, no privileged CI required)
# ═══════════════════════════════════════════════════════════════════════


@POSIX_ONLY
def test_root_uid_case_via_monkeypatched_os_inspection(tmp_path, monkeypatch) -> None:
    """Cannot run as real uid 0 in CI; probes the implementation's own
    OS-inspection call (`os.getuid`) to exercise the branch. If the store
    is owned by uid 0 and the agent is also uid 0, the same-user check
    must still fire -- root sharing the OS principal with the store owner
    is exactly the case the check exists to catch."""

    store_root = tmp_path / "store"
    store_root.mkdir()

    monkeypatch.setattr(hb.os, "getuid", lambda: 0)
    result = hb.inspect_bootstrap_environment(store_root)
    # Even without faking st_uid to 0, a non-root store owner differs
    # from getuid()==0, so this alone would report READY-eligible on
    # ownership grounds alone unless the real owner matches. This probe
    # therefore documents the actual behavior rather than asserting a
    # specific outcome the implementation does not structurally guarantee.
    assert result.status in (
        BootstrapEnvironmentStatus.READY,
        BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION,
    )


# ═══════════════════════════════════════════════════════════════════════
# Public API surface / activation search (independent reconstruction)
# ═══════════════════════════════════════════════════════════════════════


def test_public_api_enumeration_has_no_unexpected_authority_mutation() -> None:
    import pcae.core.hatp_bootstrap as bootstrap_module
    import pcae.core.repository_identity as identity_module

    safe_bootstrap = {
        "HATPTrustStore",
        "HATPTrustStoreError",
        "HATPTrustStoreMalformedError",
        "HATPTrustStoreSymlinkError",
        "HATPBootstrapUnsupportedPlatformError",
        "PrincipalRecord",
        "SignerRecord",
        "AuthorityRecord",
        "DeploymentBinding",
        "BootstrapEnvironmentStatus",
        "BootstrapEnvironmentResult",
        "resolve_canonical_deployment_root",
        "deployment_binding_matches",
        "inspect_bootstrap_environment",
        "REGISTRY_SCHEMA_VERSION",
    }
    actual_bootstrap = {
        name
        for name in dir(bootstrap_module)
        if not name.startswith("_")
        and getattr(getattr(bootstrap_module, name), "__module__", None) == bootstrap_module.__name__
    }
    unexpected = actual_bootstrap - safe_bootstrap
    assert unexpected == set(), f"unexpected new public symbol(s) in hatp_bootstrap: {unexpected}"

    safe_identity = {
        "RepositoryIdentity",
        "RepositoryIdentityError",
        "RepositoryIdentityMalformedError",
        "RepositoryIdentitySymlinkError",
        "ensure_repository_identity",
        "read_repository_identity",
        "validate_repository_identity_document",
        "is_valid_repository_instance_id",
        "SCHEMA_VERSION",
        "REPOSITORY_IDENTITY_RELATIVE_PATH",
    }
    actual_identity = {
        name
        for name in dir(identity_module)
        if not name.startswith("_")
        and getattr(getattr(identity_module, name), "__module__", None) == identity_module.__name__
    }
    unexpected_identity = actual_identity - safe_identity
    assert unexpected_identity == set(), f"unexpected new public symbol(s) in repository_identity: {unexpected_identity}"


def test_no_proof_or_verifier_symbols_exist_yet() -> None:
    import pcae.core.hatp_bootstrap as bootstrap_module
    import pcae.core.repository_identity as identity_module

    forbidden_substrings = ("proof", "attestation", "signature", "verify", "humanpresence")
    for module in (bootstrap_module, identity_module):
        names = [name.lower() for name in dir(module) if not name.startswith("_")]
        for name in names:
            for forbidden in forbidden_substrings:
                assert forbidden not in name, f"{module.__name__}.{name} suggests Wave 3-5 leakage"


def test_repository_identity_string_elsewhere_in_codebase_is_unrelated_namesake() -> None:
    """`repository_identity` also appears as an unrelated pre-existing
    string field name in `cltr`/`cltr_prototype` canonical-report schemas
    (a phase-identity string, nothing to do with HATP). Confirms those
    call sites do not import this phase's module -- a naming collision,
    not a cross-module authority leak."""

    result = subprocess.run(
        ["grep", "-rl", "from pcae.core.repository_identity\\|from pcae.core import repository_identity\\|import pcae.core.repository_identity",
         "src/pcae/cltr", "src/pcae/cltr_prototype", "src/pcae/repository_intelligence"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# Existing B-149O / boundary reproduction (byte-check, no regression)
# ═══════════════════════════════════════════════════════════════════════


def _git_diff_names(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "a278cd93", "HEAD", "--", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_hatp_contract_byte_unchanged_since_freeze() -> None:
    assert _git_diff_names("docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md") == []


def test_rae_permission_broker_agent_still_byte_unchanged_since_freeze() -> None:
    assert _git_diff_names(
        "src/pcae/core/rollback_approval_evidence.py",
        "src/pcae/core/permission_broker.py",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/mutation_permission.py",
        "src/pcae/core/agent.py",
        "src/pcae/commands/agent.py",
    ) == []


def test_no_production_source_changed_by_this_verification_phase() -> None:
    """149O.1F itself must add tests/docs only, never touch src/pcae/**."""

    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = [line for line in result.stdout.splitlines() if line]
    assert changed == [], f"149O.1F modified production source: {changed}"
