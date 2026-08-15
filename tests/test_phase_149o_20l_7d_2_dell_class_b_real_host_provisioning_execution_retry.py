"""Phase 149O.20L.7D.2 -- Dell Class-B Real Host Provisioning Execution
Retry.

This phase retried the CHGR-authorized nine-action Boundary-P
provisioning plan against the real Dell host from a freshly reverified
entry state. Actions 1-5 (packages, `pcae` group/user, Protected Root,
runtime/state tree, home normalization) succeeded and were verified.
Action 6 (source clone) failed its own read-back requirement -- the
frozen forward command's blanket `chmod 0640` strips the executable
bit from a handful of tracked files, producing a non-empty
`git status --short` -- and was cleanly rolled back per its own frozen
rollback commands. Actions 7-9 were not attempted.

Like the 149O.20L.7D.1 and 149O.20L.7B.1 companion modules, this module
does not re-run live SSH mutation against the Dell -- that is an
inherently live-host, non-deterministic operation unsuitable for CI --
and instead independently re-derives the static, already-persisted
facts this phase's report
(`docs/PHASE_149O_20L_7D_2_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION_RETRY.md`)
depends on. No private key material is present anywhere in this module
or the report it checks -- only the public fingerprint and non-secret
GitHub metadata already disclosed in 149O.20L.7D.1.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"
CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
WRAPPER_DIGEST = (
    "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
)
DEPLOY_KEY_PATH = "/root/.ssh/pcae_harness_deploy_ed25519"
DEPLOY_KEY_FINGERPRINT = "SHA256:pSD+FImEdVWIut+199XjrkqMeeu6eCOZd1FldrMiTrk"
DEPLOY_KEY_GITHUB_ID = "160313031"

PHASE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_2_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION_RETRY.md"
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


def test_chgr_entry_verification_recorded_passed(phase_doc_text: str) -> None:
    assert CHGR_ID in phase_doc_text
    assert "CHGR ENTRY VERIFICATION:            PASSED" in phase_doc_text


def test_pinned_source_sha_present_and_unchanged(phase_doc_text: str) -> None:
    assert PINNED_SOURCE_SHA in phase_doc_text
    assert "no drift since" in phase_doc_text


def test_wrapper_digest_matches_frozen_value(phase_doc_text: str) -> None:
    assert WRAPPER_DIGEST in phase_doc_text


def test_credential_prerequisite_reverified_not_mutated(phase_doc_text: str) -> None:
    assert DEPLOY_KEY_PATH in phase_doc_text
    assert DEPLOY_KEY_FINGERPRINT in phase_doc_text
    assert DEPLOY_KEY_GITHUB_ID in phase_doc_text
    assert "unchanged, not mutated" in phase_doc_text.lower() or "unchanged" in phase_doc_text


def test_no_private_key_bytes_present(phase_doc_text: str) -> None:
    for marker in (
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    ):
        assert marker not in phase_doc_text


def test_actions_1_through_5_recorded_success(phase_doc_text: str) -> None:
    for n in range(1, 6):
        assert f"ACTION {n}" in phase_doc_text
    assert phase_doc_text.count("SUCCESS") >= 5


def test_action_6_recorded_as_failed_readback_and_rolled_back(
    phase_doc_text: str,
) -> None:
    assert "FAILED READ-BACK" in phase_doc_text
    assert "ROLLED BACK CLEAN" in phase_doc_text
    assert "git status --short" in phase_doc_text
    assert "0 insertions(+), 0 deletions(-)" in phase_doc_text


def test_actions_7_8_9_not_attempted(phase_doc_text: str) -> None:
    assert "ACTION 7 (venv/install):            NOT ATTEMPTED" in phase_doc_text
    assert "ACTION 8 (wrapper):                 NOT ATTEMPTED" in phase_doc_text
    assert "ACTION 9 (verifier):                NOT ATTEMPTED" in phase_doc_text


def test_no_deploymentbinding_or_boundary_c_or_a(phase_doc_text: str) -> None:
    assert "DEPLOYMENTBINDING:                  NOT CREATED" in phase_doc_text
    assert "BOUNDARY C:                         NOT AUTHORIZED" in phase_doc_text
    assert "BOUNDARY A:                         NOT AUTHORIZED" in phase_doc_text


def test_runtime_state_unchanged(phase_doc_text: str) -> None:
    assert "Observed / observe / unavailable" in phase_doc_text


def test_chgr_integrity_unchanged_not_consumed(phase_doc_text: str) -> None:
    assert "CHGR INTEGRITY:                     UNCHANGED, NOT CONSUMED" in phase_doc_text


def test_immutable_7b1_plan_reconstructed_from_pinned_commit() -> None:
    show = _git_show(IMMUTABLE_7B1_COMMIT)
    assert "Phase 149O.20L.7B.1" in show
    assert (
        "sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \\;" in show
    )


def test_no_production_source_repair(phase_doc_text: str) -> None:
    assert "src/pcae/**" in phase_doc_text
    assert "were **not** modified by this phase" in phase_doc_text


def test_no_secret_material_anywhere_in_repo_tree() -> None:
    secret_markers = (
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    )
    for marker in secret_markers:
        r = subprocess.run(
            ["git", "grep", "-l", "-F", "-e", marker, "--", ":!tests/**"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 1, f"no tracked file should contain marker: {marker}"


def test_recommended_next_phase_is_a_repair_amendment_not_7e(
    phase_doc_text: str,
) -> None:
    assert "149O.20L.7D.3" in phase_doc_text
    assert "Action-6 File-Mode Command Defect Repair" in phase_doc_text
    assert "does **not** recommend" in phase_doc_text
    assert "149O.20L.7E" in phase_doc_text
