"""Phase 149O.1E independent-verification-preparation adversarial suite.

Cross-cutting invariants spanning `repository_identity.py` (Wave 1) and
`hatp_bootstrap.py` (Wave 2) that neither module's own unit-test file
tests in isolation: that no combination of Wave-1/2 state can cause
production HATP evidence to be trusted, that the current repository's
own live deployment is NOT READY, and that the frozen contract/RAE/
Permission-Broker boundaries are untouched by this phase's diff.
"""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

from pcae.core.hatp_bootstrap import (
    BootstrapEnvironmentStatus,
    HATPTrustStore,
    inspect_bootstrap_environment,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── No path to production HATP activation from Wave-1/2 state alone ─────


def test_no_activation_gate_symbol_exists_yet() -> None:
    """Wave 4 (verifier) and Wave 6 (RAE integration) own
    `HATP_TRUSTED_OPERATIONAL`/`approval_present` derivation -- neither
    exists after this phase. A future regression that starts deriving
    trust from Wave-1/2 state alone would first have to introduce one of
    these symbols; absence is the guarantee."""

    import pcae.core.hatp_bootstrap as bootstrap_module
    import pcae.core.repository_identity as identity_module

    for module in (bootstrap_module, identity_module):
        public_names = {name.lower() for name in dir(module) if not name.startswith("_")}
        assert "approval_present" not in public_names
        assert "hatp_trusted_operational" not in public_names
        assert not any("verify" in name for name in public_names)


def test_repository_identity_alone_grants_no_authority(tmp_path: Path) -> None:
    """HATP-REQ-051: identity existing, being known, or being copied
    confers nothing. A store with no matching binding treats even a
    real, freshly-generated identity as unauthorized."""

    root = HarnessPath(tmp_path)
    identity = ensure_repository_identity(root)

    store = HATPTrustStore(_test_only_root=tmp_path / "empty-store")
    assert store.load_repository_enrollment(identity.repository_instance_id) is None
    assert (
        store.resolve_deployment_authorization(
            repository_id=identity.repository_instance_id,
            canonical_deployment_root=str(tmp_path),
        )
        is None
    )


def test_trust_store_alone_without_matching_repository_id_grants_nothing(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "deployment_bindings": [
                    {
                        "repository_id": str(uuid.uuid4()),
                        "canonical_deployment_root": "/some/other/deployment",
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

    unrelated_repo_id = str(uuid.uuid4())
    assert store.load_repository_enrollment(unrelated_repo_id) is None


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")
def test_current_repository_deployment_is_not_ready() -> None:
    """Mandatory live negative control (149O.1D plan §39, item 105):
    this repository's own current deployment -- same OS user for agent
    and admin roles -- must never report READY."""

    store_root = Path.home() / ".pcae-hatp" / "trust-store"
    if store_root.exists():
        result = inspect_bootstrap_environment(store_root)
    else:
        result = inspect_bootstrap_environment(store_root)
    assert result.status in (BootstrapEnvironmentStatus.UNAVAILABLE, BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION)
    assert result.status != BootstrapEnvironmentStatus.READY


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")
def test_same_user_environment_can_never_report_ready(tmp_path: Path) -> None:
    """No file permission on a store this test process itself owns can
    make `inspect_bootstrap_environment` return READY -- the same-OS-
    principal check is unconditional."""

    for mode in (0o700, 0o600, 0o400, 0o755):
        store_root = tmp_path / f"store-{mode:o}"
        store_root.mkdir()
        store_root.chmod(mode)
        result = inspect_bootstrap_environment(store_root)
        assert result.status != BootstrapEnvironmentStatus.READY
        store_root.chmod(0o700)  # restore for cleanup


# ── Contract / RAE / Permission Broker boundary diffs ────────────────────


def _git_diff_names(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_hatp_contract_byte_unchanged() -> None:
    assert _git_diff_names("docs/contracts/") == []


def test_rae_module_untouched() -> None:
    assert _git_diff_names("src/pcae/core/rollback_approval_evidence.py") == []


def test_permission_broker_untouched() -> None:
    assert _git_diff_names(
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/permission_broker.py",
        "src/pcae/core/mutation_permission.py",
    ) == []


def test_agent_module_untouched() -> None:
    assert _git_diff_names("src/pcae/core/agent.py", "src/pcae/commands/agent.py") == []


def test_only_expected_production_files_changed() -> None:
    changed = set(_git_diff_names("src/pcae/"))
    expected = {
        "src/pcae/commands/init.py",
        "src/pcae/core/templates.py",
        "src/pcae/core/repository_identity.py",
        "src/pcae/core/hatp_bootstrap.py",
        # 149O.1G, Wave 3: proof models + canonical serialization. This
        # phase's own diff-scope check (`test_phase_149o_1g_...py`)
        # separately reconfirms `repository_identity.py`/
        # `hatp_bootstrap.py` remain byte-unchanged; this widening only
        # accounts for a later, legitimate phase's new file, mirroring
        # this project's established allowed-file-widening precedent.
        "src/pcae/core/human_approval_trusted_provenance.py",
        # 149O.1I, Wave 4: verification engine + provider-neutral
        # interface / deterministic test provider. Same allowed-file-
        # widening precedent as 149O.1G's entry above.
        "src/pcae/core/hatp_providers.py",
    }
    # New files show up as untracked, not in `git diff`; check those separately.
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    all_touched = changed | set(untracked)
    assert all_touched <= expected, f"unexpected src/pcae/ hunks: {all_touched - expected}"


# ── Runtime state unaffected ─────────────────────────────────────────────


def test_runtime_state_still_observe_only() -> None:
    result = subprocess.run(
        ["pcae", "runtime", "inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Observed" in result.stdout
    assert "unavailable" in result.stdout
    assert "observe" in result.stdout
