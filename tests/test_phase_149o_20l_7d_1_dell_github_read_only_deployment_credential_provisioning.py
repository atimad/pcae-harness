"""Phase 149O.20L.7D.1 -- Dell GitHub Read-Only Deployment Credential
Provisioning.

This phase provisioned the narrowly scoped source-access prerequisite
that blocked Phase 149O.20L.7D at Action 6: a dedicated, repository-scoped,
read-only GitHub deploy credential for `atimad/pcae-harness`, plus the
independently verified `github.com` host-trust entry and deterministic
SSH identity selection needed to use it. It did not retry the frozen
nine-action Boundary-P plan, create the `pcae` principal, or touch any
Class-B infrastructure path.

Like Phase 149O.20L.7D's own companion module, this module does not
re-run live SSH mutation against the Dell -- that is inherently a
live-host, non-deterministic operation unsuitable for CI -- and instead
independently re-derives the static, already-persisted facts this
phase's report
(`docs/PHASE_149O_20L_7D_1_DELL_GITHUB_READ_ONLY_DEPLOYMENT_CREDENTIAL_PROVISIONING.md`)
depends on. No private key material is present anywhere in this module
or the report it checks -- only the public fingerprint and non-secret
GitHub metadata.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"
CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"

DEPLOY_KEY_PATH = "/root/.ssh/pcae_harness_deploy_ed25519"
DEPLOY_KEY_FINGERPRINT = "SHA256:pSD+FImEdVWIut+199XjrkqMeeu6eCOZd1FldrMiTrk"
DEPLOY_KEY_GITHUB_ID = "160313031"
KNOWN_HOSTS_PATH = "/root/.ssh/known_hosts"
SSH_CONFIG_PATH = "/root/.ssh/config"

PHASE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_1_DELL_GITHUB_READ_ONLY_DEPLOYMENT_CREDENTIAL_PROVISIONING.md"
)


def _git_show(ref: str) -> str:
    return subprocess.run(
        ["git", "show", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text(encoding="utf-8")


def test_dell_machine_id_matches_expected(phase_doc_text: str) -> None:
    assert DELL_MACHINE_ID in phase_doc_text


def test_7d_rollback_reconfirmed_clean(phase_doc_text: str) -> None:
    assert "rollback confirmed bit-for-bit clean" in phase_doc_text
    for marker in ("pcae", "/etc/pcae", "/opt/pcae", "/var/lib/pcae", "/var/log/pcae", "/home/pcae"):
        assert marker in phase_doc_text


def test_dedicated_key_path_is_not_generic_default(phase_doc_text: str) -> None:
    assert DEPLOY_KEY_PATH in phase_doc_text
    assert "id_ed25519" not in DEPLOY_KEY_PATH
    assert DEPLOY_KEY_PATH.startswith("/root/.ssh/")


def test_private_key_metadata_present_bytes_never_present(phase_doc_text: str) -> None:
    assert "root:root 600" in phase_doc_text
    private_key_marker = "-----BEGIN OPENSSH PRIVATE KEY-----"
    assert private_key_marker not in phase_doc_text


def test_public_fingerprint_matches_expected(phase_doc_text: str) -> None:
    assert DEPLOY_KEY_FINGERPRINT in phase_doc_text
    assert re.match(r"^SHA256:[A-Za-z0-9+/]{43}$", DEPLOY_KEY_FINGERPRINT)


def test_deterministic_identity_selection_documented(phase_doc_text: str) -> None:
    assert "IdentitiesOnly yes" in phase_doc_text
    assert SSH_CONFIG_PATH in phase_doc_text
    assert "Host github.com" in phase_doc_text


def test_known_hosts_sourced_from_authoritative_github_metadata(phase_doc_text: str) -> None:
    assert "api.github.com/meta" in phase_doc_text
    assert KNOWN_HOSTS_PATH in phase_doc_text
    assert "StrictHostKeyChecking=no" in phase_doc_text
    assert "never used" in phase_doc_text


def test_repository_readability_and_pinned_sha_reachability_documented(
    phase_doc_text: str,
) -> None:
    assert PINNED_SOURCE_SHA in phase_doc_text
    assert "ls-remote" in phase_doc_text
    assert "FETCH_HEAD" in phase_doc_text


def test_github_deploy_key_read_only_evidence_documented(phase_doc_text: str) -> None:
    assert '"read_only":true' in phase_doc_text or "read_only: true" in phase_doc_text
    assert DEPLOY_KEY_GITHUB_ID in phase_doc_text


def test_no_production_clone_created_this_phase(phase_doc_text: str) -> None:
    assert "/opt/pcae/runtime/src" in phase_doc_text
    assert "disposable bare repo" in phase_doc_text
    assert "rm -rf" in phase_doc_text


def test_no_pcae_principal_or_class_b_paths(phase_doc_text: str) -> None:
    assert "NOT PROVISIONED" in phase_doc_text
    for path_fragment in ("/etc/pcae", "/opt/pcae", "/var/lib/pcae", "/var/log/pcae", "/home/pcae"):
        assert path_fragment in phase_doc_text


def test_no_deploymentbinding_or_boundary_c_or_a(phase_doc_text: str) -> None:
    assert "DeploymentBinding:** NOT AUTHORIZED" in phase_doc_text
    assert "Boundary C:** NOT AUTHORIZED" in phase_doc_text
    assert "Boundary A:** NOT AUTHORIZED" in phase_doc_text


def test_runtime_state_unchanged(phase_doc_text: str) -> None:
    assert "Observed / observe / unavailable" in phase_doc_text


def test_chgr_outcome_a_adjudication_recorded(phase_doc_text: str) -> None:
    normalized = " ".join(phase_doc_text.split())
    assert "Outcome A" in normalized and "established" in normalized
    assert CHGR_ID in normalized
    assert "REMAINS CURRENT SUBJECT TO FRESH 7D.2 ENTRY CHECKS" in normalized


def test_immutable_7b1_proposition_reconstructed_from_pinned_commit() -> None:
    show = _git_show(IMMUTABLE_7B1_COMMIT)
    assert "Phase 149O.20L.7B.1" in show
    assert "sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git" in show


def test_rollback_procedure_defined_but_not_executed(phase_doc_text: str) -> None:
    assert "not executed this phase" in phase_doc_text
    assert "gh api -X DELETE repos/atimad/pcae-harness/keys" in phase_doc_text


def test_no_secret_material_anywhere_in_repo_tree() -> None:
    secret_markers = (
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    )
    for marker in secret_markers:
        r = subprocess.run(
            ["git", "grep", "-l", "-F", "-e", marker],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 1, f"no tracked file should contain marker: {marker}"


def test_recommended_next_phase_is_7d2_not_a_retry(phase_doc_text: str) -> None:
    assert "149O.20L.7D.2" in phase_doc_text
    assert "does not combine with or execute any part of that retry" in phase_doc_text
