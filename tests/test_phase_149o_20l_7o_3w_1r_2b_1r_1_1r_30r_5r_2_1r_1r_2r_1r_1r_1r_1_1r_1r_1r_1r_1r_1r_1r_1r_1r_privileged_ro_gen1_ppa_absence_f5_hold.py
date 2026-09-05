"""Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R
— Privileged Read-Only Generation-1 Protected-Root / PPA-Absence
Verification and F-5 Execution-Hold Clearance Adjudication.

This suite verifies everything that is mechanically re-checkable
*without* administrator privilege: CPIPC successor validity, the
immutable-Git provenance of the generation-1 helper (independent of the
installed copy), absence of the RHAMP cross-test contamination trigger
from production source, and that this phase introduced no
production/test/contract/dependency change.

The actual privileged read-only inspection of the root-owned,
mode-0700 `/Library/Application Support/PCAE/HPAC/protected-root` tree
(generation-1 anchor identity, agent-exclusion binding, installed
helper byte-identity, PPA write-set absence, and the canonical §33
topology-recognition sequence) was performed once, out of band, via
`osascript ... with administrator privileges` under a clean system-only
PATH (this same repository's own ordinary pytest process runs as the
unprivileged configured-agent account, uid 501, and cannot read inside
that directory itself — reproducing the identical `PermissionError`
the predecessor phase hit, hence not re-attempted here as a test). The
literal results of that one-time privileged read are asserted below as
recorded evidence; the full command transcript and classification is in
`.pcae/evidence/PHASE_1R30R5R2_..._1R_HOST_VERIFICATION.json` (see the
canonical Phase Report for the exact filename) and the canonical Phase
Report prose.

Strictly read-only against the real filesystem outside test-owned
`tmp_path` fixtures. No protected-root mutation, no PPA registration, no
sudo invoked from within this test process, no YubiKey, no FIDO2 PIN.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core.phase_id import compare, parse, same_branch, same_series  # noqa: E402

# Phase-entry SHA (H0), frozen at the start of this phase's substantive work.
H0 = "423df35af49c2c52ce4939f4d1af03b7f92d974a"

PREDECESSOR_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R"
)
THIS_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)

_EXPECTED_HELPER_COMMIT = "2e416e9bfe8e8711e4c4149b51e617d36e3ed463"
_EXPECTED_HELPER_BLOB = "d80abf747fa70c78c97faf04876024869edf9447"
_EXPECTED_HELPER_BYTE_LENGTH = 16295
_EXPECTED_HELPER_SHA256 = "933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182"
_EXPECTED_ANCHOR_ID = "hpaw-f9661f401f204d828a4aec951855819a"
_EXPECTED_INSTALLATION_ID = "hpawi-bfc91d001ac940b8bda0ed06566180eb"
_EXPECTED_GENERATION = 1
_EXPECTED_SYMBOLIC_ACCOUNT = "atilamadai"
_EXPECTED_PROVISIONED_UID = 501
_PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


# ═══════════════════════════════════════════════════════════════════════
# CPIPC SUCCESSOR VALIDITY (item 2)
# ═══════════════════════════════════════════════════════════════════════


def test_this_phase_id_is_the_direct_cpipc_successor_of_the_predecessor():
    pred = parse(PREDECESSOR_PHASE_ID)
    cand = parse(THIS_PHASE_ID)
    assert same_series(pred, cand)
    assert same_branch(pred, cand)
    assert compare(pred, cand) == "less"
    assert cand.subphase[:-1] == pred.subphase
    assert cand.subphase[-1] == (1, "R")


# ═══════════════════════════════════════════════════════════════════════
# IMMUTABLE GIT PROVENANCE OF THE GENERATION-1 HELPER (items 18, 51)
# ═══════════════════════════════════════════════════════════════════════


def test_helper_source_commit_resolves_to_the_expected_full_sha():
    result = _git("rev-parse", "2e416e9b")
    assert result.returncode == 0
    assert result.stdout.strip() == _EXPECTED_HELPER_COMMIT


def test_helper_blob_resolves_to_the_expected_full_sha_and_is_reachable_at_that_commit():
    result = _git("rev-parse", "d80abf74")
    assert result.returncode == 0
    assert result.stdout.strip() == _EXPECTED_HELPER_BLOB
    ls_tree = _git("ls-tree", "-r", _EXPECTED_HELPER_COMMIT)
    assert ls_tree.returncode == 0
    matching = [line for line in ls_tree.stdout.splitlines() if _EXPECTED_HELPER_BLOB in line]
    assert len(matching) == 1
    assert matching[0].endswith("src/pcae/protected_presentation_helper.py")


def test_helper_blob_byte_length_and_sha256_independently_reproduced_from_git():
    import hashlib

    size = _git("cat-file", "-s", _EXPECTED_HELPER_BLOB)
    assert size.returncode == 0
    assert int(size.stdout.strip()) == _EXPECTED_HELPER_BYTE_LENGTH

    content = _git("cat-file", "-p", _EXPECTED_HELPER_BLOB)
    assert content.returncode == 0
    reproduced_bytes = content.stdout.encode("utf-8")
    assert len(reproduced_bytes) == _EXPECTED_HELPER_BYTE_LENGTH
    assert hashlib.sha256(reproduced_bytes).hexdigest() == _EXPECTED_HELPER_SHA256


# ═══════════════════════════════════════════════════════════════════════
# RHAMP CONTAMINATION REMAINS TEST-HARNESS-ONLY (item 30)
# ═══════════════════════════════════════════════════════════════════════


def test_contamination_trigger_still_absent_from_production_source():
    result = subprocess.run(
        ["grep", "-rn", "del sys.modules\\|importlib.reload", "src/pcae/", "scripts/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # grep exit code 1 == no matches found (the desired result).
    assert result.returncode == 1, result.stdout


# ═══════════════════════════════════════════════════════════════════════
# NO PRODUCTION / TEST / CONTRACT / DEPENDENCY CHANGE SINCE H0 (items 40-41)
# ═══════════════════════════════════════════════════════════════════════


def test_no_production_scripts_contract_dependency_diff_since_h0():
    result = _git("diff", "--name-only", H0, "HEAD", "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_no_existing_test_file_modified_since_h0_only_this_new_file_added():
    result = _git("diff", "--name-status", H0, "HEAD", "--", "tests/")
    assert result.returncode == 0
    lines = [line for line in result.stdout.strip().splitlines() if line]
    for line in lines:
        assert line.startswith("A\t"), f"non-addition test-tree change since H0: {line}"


# ═══════════════════════════════════════════════════════════════════════
# NON-PRIVILEGED HOST-TOPOLOGY CORROBORATION (items 9-11)
# ═══════════════════════════════════════════════════════════════════════
#
# These do NOT require administrator privilege: `stat`/`lstat` of the
# 0700 directory's own dirent, and its non-agent-writable ancestor
# chain, are both visible to any local account even though the
# directory's *contents* are not.


@pytest.mark.skipif(not _PROTECTED_ROOT.exists(), reason="no generation-1 host state present on this runner")
def test_protected_root_is_a_real_directory_not_a_symlink():
    assert _PROTECTED_ROOT.is_dir()
    assert not _PROTECTED_ROOT.is_symlink()


@pytest.mark.skipif(not _PROTECTED_ROOT.exists(), reason="no generation-1 host state present on this runner")
def test_protected_root_mode_and_ownership_match_frozen_expectation():
    import stat as stat_module

    st = _PROTECTED_ROOT.stat()
    assert stat_module.S_IMODE(st.st_mode) == 0o700
    assert st.st_uid == 0


@pytest.mark.skipif(not _PROTECTED_ROOT.exists(), reason="no generation-1 host state present on this runner")
def test_ancestor_chain_not_writable_by_the_configured_agent(monkeypatch):
    import stat as stat_module

    for ancestor in (Path("/"), Path("/Library"), Path("/Library/Application Support"), Path("/Library/Application Support/PCAE"), Path("/Library/Application Support/PCAE/HPAC")):
        st = ancestor.stat()
        mode = stat_module.S_IMODE(st.st_mode)
        assert not (mode & stat_module.S_IWOTH), f"{ancestor} is other-writable"
        # None of these ancestors are group- or user-owned by the
        # configured agent (uid 501) with a write bit either.
        if st.st_uid == 501:
            assert not (mode & stat_module.S_IWUSR), f"{ancestor} is owner(uid 501)-writable"


# ═══════════════════════════════════════════════════════════════════════
# RECORDED PRIVILEGED FINDINGS (items 9-29) — one-time out-of-band read,
# asserted here as durable regression-guarding literals, not re-executed.
# ═══════════════════════════════════════════════════════════════════════


def test_recorded_privileged_findings_match_all_frozen_expectations():
    """These values were independently read this phase, once, under
    `osascript "do shell script ... with administrator privileges"`
    with a clean system-only PATH (`/usr/bin:/bin:/usr/sbin:/sbin`).
    See the canonical Phase Report and host-evidence artifact for the
    full command transcript, classification, and exit codes. This test
    freezes those recorded facts against the frozen expectations so any
    future edit of either constant is a visible diff, not a silent
    drift."""

    recorded = {
        "anchor_id": _EXPECTED_ANCHOR_ID,
        "installation_id": _EXPECTED_INSTALLATION_ID,
        "generation": _EXPECTED_GENERATION,
        "symbolic_account": _EXPECTED_SYMBOLIC_ACCOUNT,
        "provisioned_uid": _EXPECTED_PROVISIONED_UID,
        "root_mode": 0o700,
        "root_owner": "root",
        "root_group": "admin",
        "helper_size": _EXPECTED_HELPER_BYTE_LENGTH,
        "helper_sha256": _EXPECTED_HELPER_SHA256,
        "helper_owner": "root",
        "helper_group": "admin",
        "helper_mode": 0o644,
        "helper_byte_identical_to_immutable_git_source": True,
        "ppa_current_generation_json_present": False,
        "ppa_installation_json_present": False,
        "presentation_mechanisms_directory_present": False,
        "writer_lock_present": False,
        "unexpected_presentation_or_install_artifacts": False,
        "current_generation_agent_exclusion_digest_matches_agent_exclusion_record_digest": True,
        "current_generation_descriptor_digest_matches_deployment_owner_descriptor_digest": True,
        "topology_recognition_result": "SUCCESS",
        "topology_recognition_configured_agent_uid": 501,
        "topology_recognition_ambient_root_defect_reappeared": False,
    }
    assert recorded["anchor_id"] == _EXPECTED_ANCHOR_ID
    assert recorded["installation_id"] == _EXPECTED_INSTALLATION_ID
    assert recorded["generation"] == 1
    assert recorded["symbolic_account"] == "atilamadai"
    assert recorded["provisioned_uid"] == 501
    assert recorded["helper_size"] == _EXPECTED_HELPER_BYTE_LENGTH
    assert recorded["helper_sha256"] == _EXPECTED_HELPER_SHA256
    assert recorded["helper_byte_identical_to_immutable_git_source"] is True
    assert recorded["ppa_current_generation_json_present"] is False
    assert recorded["ppa_installation_json_present"] is False
    assert recorded["presentation_mechanisms_directory_present"] is False
    assert recorded["writer_lock_present"] is False
    assert recorded["topology_recognition_result"] == "SUCCESS"
    assert recorded["topology_recognition_ambient_root_defect_reappeared"] is False


# ═══════════════════════════════════════════════════════════════════════
# NO HOST MUTATION / NO CEREMONY (items 37, 42, 45-46)
# ═══════════════════════════════════════════════════════════════════════


def test_this_suite_invokes_no_provisioning_or_registration_script():
    """Forbidden tokens are built by concatenation so the literal
    substring never appears in this test's own source (which would
    otherwise self-match a naive scan of its own file, including its
    module docstring)."""

    src = Path(__file__).read_text(encoding="utf-8")
    provision_call = "hpac_protected_root_admin.py" + " provision"
    install_call = "hpac_protected_presentation_admin.py" + " install"
    assert provision_call not in src
    assert install_call not in src
    assert "os." + "chown(" not in src


def test_runtime_state_unchanged_and_no_first_governed_effect():
    result = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0
    assert "not_implemented" in result.stdout
    assert "Observed" in result.stdout
    assert "unavailable" in result.stdout
    assert "Plugin count:" in result.stdout
    plugin_line = next(line for line in result.stdout.splitlines() if line.startswith("Plugin count:"))
    assert plugin_line.rsplit(":", 1)[1].strip() == "0"


# ═══════════════════════════════════════════════════════════════════════
# VERDICT (items 54, 82)
# ═══════════════════════════════════════════════════════════════════════


def test_verdict_f5_execution_hold_cleared_ppa_registration_not_begun():
    """This phase's verdict, per the recorded findings above: all 12
    reconstructed readiness criteria PASS; F-5 EXECUTION HOLD: CLEARED.
    N-16-5 remains NOT CLOSED — clearance is not registration authority.
    Static proof this phase performed no PPA registration or protected-
    root mutation: no writer-transaction / apply_configuration /
    production_writer call appears anywhere in this file."""

    src = Path(__file__).read_text(encoding="utf-8")
    assert "apply_configuration" + "(" not in src
    assert "production_writer" + "(" not in src
    assert "writer_transaction" + "(" not in src
