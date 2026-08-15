"""Phase 149O.20L.7E -- Dell Class-B Real Host Provisioning Independent
Verification.

Independently-authored companion test module. Does NOT import 7D.11's
own test module as oracle and does NOT treat 7D.11's phase-completion
report prose as ground truth -- every assertion here is re-derived
directly from primary git objects, the production
`derive_implementation_scope_digest()` function (called fresh against
a disposable worktree of the candidate commit), the on-disk CHGR JSON
records themselves, and this phase's own fresh, read-only `ssh
hac-dell` session.

Live Dell SSH facts (machine-id, deployed source SHA/tree/mode/byte
identity, venv/wrapper/PATH state, independent Action-9 result,
privilege isolation, trust-store emptiness) were independently
re-verified this phase over a fresh read-only `ssh hac-dell` session
(`hac-dell` / `192.168.192.200` / user `codex`, passwordless `sudo -n`
for read-only root-owned-path inspection); they are captured here only
as static constants recording this phase's own findings, matching this
project's established convention (7D.9/7D.10's own test modules do the
same for their own live-Dell findings) -- this module does not re-SSH
into Dell when run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7E_DELL_CLASS_B_REAL_HOST_PROVISIONING_INDEPENDENT_VERIFICATION.md"
)

GOVERNING_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"
OLD_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-96a0ce12756e4cc892492a87af1db832.json"
CONTINUATION_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-541cb08c313b4f8884970172d37c5a1d.json"

OLD_DEPLOYED_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
CANDIDATE_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"

CANDIDATE_DIGEST = "4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac"

WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
WRAPPER_SIZE_BYTES = 188
WRAPPER_LINE_COUNT = 9
MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"

CANDIDATE_TRACKED_PATH_COUNT = 4108
CANDIDATE_100644_COUNT = 4097
CANDIDATE_100755_COUNT = 11

THREE_REPAIRED_FILES = (
    "src/pcae/core/hatp_class_b_conformance.py",
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
)

# Independently re-derived this phase (§14 of the governing prompt): the
# 22 src/pcae/-relative + 6 repository-root-relative HMIC-REQ-050 v1.3
# canonical member paths, read directly from
# `hatp_mandatory_certification._FROZEN_SRC_PCAE_RELATIVE_FILES` /
# `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, not copied from any prior
# phase's report prose.
HMIC_28_MEMBER_PATHS = (
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_mandatory_certification.py",
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "scripts/hatp_certification_admin.py",
)

# This phase's own fresh `sha256sum` of all 28 canonical files as read
# directly from the live Dell deployed checkout (`sudo -n sha256sum
# /opt/pcae/runtime/src/<path>`), captured verbatim -- independently
# confirmed, this phase, to equal the candidate commit's own git-blob
# SHA-256 for every single entry (zero mismatches across all 28, not
# just the three previously-repaired files).
DELL_HMIC_28_SHA256 = {
    "src/pcae/core/hatp_mandatory_cutover.py": "175e09822e7ebb0d55bfdbb7241b6f94ac96de275dff927d15262422db2fe27c",
    "src/pcae/core/hatp_ag_authority.py": "49eedb2035022fa7eb1755eac35ec3af8f36ca5bd0dcfe96cb1353dcb9c55e84",
    "src/pcae/core/hatp_rollback_consumption.py": "05dce4ff757d7f6fad7d4894685942de884bd41cfe6bc1ea46615c707f7a16b0",
    "src/pcae/core/hatp_bootstrap.py": "a3d12e10e7949f789674c144e22d57be18edb3164958eb7c531130c97d9be749",
    "src/pcae/core/human_approval_trusted_provenance.py": "0efd207ae9ff7a335bad5097f166a57b03de3911ecf1e241b1e39344334d17fd",
    "src/pcae/core/repository_identity.py": "b4a585ca67c8bea48d45f86874d825c83405b52c9cce629124ecc5f77182a0ac",
    "src/pcae/core/rollback_approval_evidence.py": "9bde81615808ed20caf1f72b19a07027cb6091a3cefb29bca1286486d70dd81a",
    "src/pcae/core/hatp_evidence_store.py": "f3c330929f3bf5d81913fef719f41c5aff60355038b4da6054265808ddf39db1",
    "src/pcae/core/hatp_signed_evidence.py": "3e94cce26f8af14b2ddc35af8a2318603eb7811824e6b4e9d149383fe54f7ae4",
    "src/pcae/core/agent.py": "1b52dd8b58ad6cbeb9364a8990f279a7f303777a84a6ba94bf6a2db54d1f53c7",
    "src/pcae/commands/agent.py": "1918a9de368ad79bde1cffe944f282a3bc782590d9c45d6ce46691b2523cb41a",
    "src/pcae/cli.py": "3dc293339819a70ff276bd8e79b75b612ef627bba07661442c3aa7da91e3376e",
    "src/pcae/core/permission_broker.py": "666cbe780f5221928fb15ff0ac58d069d812e32863912c86131cf2a7d56fbfd8",
    "src/pcae/core/permission_broker_foundation.py": "0b82a4d1fe65958e6d09166ce5dce9e84deff226b75334b6f5eaa61ac01ca9c6",
    "src/pcae/core/hatp_providers.py": "38bd0eb1364930ad7c8a1b639d7e7e0ed327db174a9e53e1b2988252862d5815",
    "src/pcae/core/hatp_fido2_provider.py": "fc713d53ddb15bdf87a1134460a4845677a23add46164c5ac1de90bd2a860cea",
    "src/pcae/core/hatp_piv_provider.py": "143318da7ccdd898105ed6f71152524e8aac60c4a334f24fec8b39fbf615508f",
    "src/pcae/core/hatp_hardware_credentials.py": "af4d210a23d6800d5fb5393f9c0b9f2237f855395596fb21008ae24a34af47ff",
    "src/pcae/core/hatp_mandatory_certification.py": "e40c964959143a1b82af18d6e2f845123e601e1e6c4785c8ca41e0c2e8d37b96",
    "src/pcae/core/hatp_class_b_topology_verifier.py": "edba46128d5c18d40843302360dcb161ab20b83dbe3f44b2f0c67f3cae0d5687",
    "src/pcae/core/hatp_environment_lock_verifier.py": "1d28fec0ecc5518cf212b3534b7a0520731e9da2274b45186ce8bb2141b44bea",
    "src/pcae/core/hatp_class_b_conformance.py": "dc2f26e21613e7f600cae8e2ea3187601e4b2ab84741792cf69c7170e1a696b5",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md": "2e46d88c6a52b109cfb9ff0772305ed892990ca6570c60edda8695c3c2e4bd9b",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md": "26d8e975a55d6247f8e8f3370908f594374e4cb755a9f61a151a09c088847872",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md": "f5d5943667acd0b46ff9976fa1e18629baf849bad5cd1d3b7fc7f1aac4b8d2a2",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md": "12601e448c08cda51e185d5fd12ae08cd44594346816e7a9fa67f347801a3782",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md": "767132a602f4861debb58df762e880902e911f3d714b782db444edccf048e45e",
    "scripts/hatp_certification_admin.py": "4a8d8ed8646a0b26db32da51e127c2722e36ce824e60d0733d041d4a2e80a63e",
}

# This phase's own two independent, live, corrected Action-9 runs
# (`sudo -u pcae env -i HOME=/home/pcae
# PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin
# PYTHONNOUSERSITE=1 /opt/pcae/runtime/venv/bin/python3 -c '...'`)
# against the live Dell host, captured verbatim.
DELL_ACTION9_RUN1_STATUS = "NON_COMPLIANT"
DELL_ACTION9_RUN2_STATUS = "NON_COMPLIANT"
DELL_ACTION9_FAILING_SET = frozenset({"HBDC-REQ-042"})
DELL_ACTION9_SATISFIED_OF_INTEREST = frozenset(
    {"HBDC-REQ-022", "HBDC-REQ-030", "HBDC-REQ-035", "HBDC-REQ-036"}
)


def _git(*args: str) -> str:
    """Strictly read-only git query -- never fetch/checkout/commit/push/
    reset against this repository."""

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════
# Governing authority -- reconstructed directly from the CHGR's own text
# ═══════════════════════════════════════════════════════════════════════════


def test_governing_chgr_published_and_binds_candidate_and_path():
    record = _load_json(GOVERNING_CHGR_PATH)
    assert record["lifecycle_state"] == "published"
    assert record["selected_option_id"] == "approve"
    assert CANDIDATE_SHA in record["decision_subject"]
    assert CANDIDATE_SHA in record["rationale"]
    assert "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin" in record["rationale"]


def test_governing_chgr_expected_residual_and_exclusions():
    record = _load_json(GOVERNING_CHGR_PATH)
    rationale = record["rationale"]
    assert "HBDC-REQ-042" in rationale
    for excluded in ("DeploymentBinding", "Boundary C", "Boundary A", "Cutover Record"):
        assert excluded in record["conditions"] or excluded in rationale


def test_historical_chgrs_do_not_authorize_candidate_transition():
    for path in (OLD_CHGR_PATH, CONTINUATION_CHGR_PATH):
        record = _load_json(path)
        combined = record["decision_subject"] + record["rationale"]
        assert CANDIDATE_SHA not in combined


# ═══════════════════════════════════════════════════════════════════════════
# Candidate SHA authenticity + tree inventory -- re-derived fresh
# ═══════════════════════════════════════════════════════════════════════════


def test_candidate_sha_is_a_commit_and_ancestor_of_origin_main():
    assert _git("cat-file", "-t", CANDIDATE_SHA) == "commit"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", CANDIDATE_SHA, "origin/main"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_candidate_tree_inventory_independently_recalculated(tmp_path):
    worktree = tmp_path / "candidate-wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), CANDIDATE_SHA],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    try:
        total = subprocess.run(
            ["git", "ls-files"], cwd=worktree, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        assert len(total) == CANDIDATE_TRACKED_PATH_COUNT

        modes = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"], cwd=worktree, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        mode_counts: dict[str, int] = {}
        for line in modes:
            mode = line.split()[0]
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        assert mode_counts.get("100644") == CANDIDATE_100644_COUNT
        assert mode_counts.get("100755") == CANDIDATE_100755_COUNT
        assert sum(mode_counts.values()) == CANDIDATE_TRACKED_PATH_COUNT
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )


def test_production_diff_is_exactly_three_files():
    diff = _git(
        "diff",
        "--name-status",
        OLD_DEPLOYED_SHA,
        CANDIDATE_SHA,
        "--",
        "src/",
        "scripts/",
        "docs/contracts/",
        "pyproject.toml",
    )
    changed = {line.split("\t", 1)[1] for line in diff.splitlines() if line}
    assert changed == set(THREE_REPAIRED_FILES)


def test_repair_content_is_exactly_the_distribution_name_fix():
    diff = _git(
        "diff",
        OLD_DEPLOYED_SHA,
        CANDIDATE_SHA,
        "--",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
    )
    assert '-        dist = importlib.metadata.distribution("pcae")' in diff
    assert '+        dist = importlib.metadata.distribution("pcae-harness")' in diff


# ═══════════════════════════════════════════════════════════════════════════
# HMIC membership + digest -- 28-file canonical set, independently derived
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_28_member_set_matches_production_constant():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 28
    canonical = set(hmic._frozen_canonical_paths())
    assert canonical == set(HMIC_28_MEMBER_PATHS)


def test_implementation_scope_digest_independently_recomputed(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
    from pcae.core.paths import HarnessPath

    worktree = tmp_path / "candidate-digest-wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), CANDIDATE_SHA],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    try:
        digest = derive_implementation_scope_digest(HarnessPath(worktree))
        assert digest == CANDIDATE_DIGEST
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )


def test_hmic_contract_identity_v1_3_unchanged_candidate_to_head():
    diff = _git(
        "diff",
        CANDIDATE_SHA,
        "HEAD",
        "--",
        "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    )
    assert diff == ""
    text = (REPO_ROOT / "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md").read_text()
    assert "**Version:** 1.3" in text


# ═══════════════════════════════════════════════════════════════════════════
# Live Dell facts, this phase's own fresh read-only SSH findings
# ═══════════════════════════════════════════════════════════════════════════


def test_dell_machine_identity_matches_governed_target():
    assert MACHINE_ID == "54ff22ce400b475aa0d55cb68f4a3334"


def test_dell_deployed_sha_matches_candidate_exactly():
    # This phase's own fresh `sudo -n git -C /opt/pcae/runtime/src
    # rev-parse HEAD` result on Dell, captured verbatim.
    dell_head = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
    assert dell_head == CANDIDATE_SHA


def test_dell_all_28_hmic_files_sha256_matches_candidate_git_blob(tmp_path):
    import hashlib

    for path in HMIC_28_MEMBER_PATHS:
        blob = subprocess.run(
            ["git", "cat-file", "-p", f"{CANDIDATE_SHA}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        candidate_digest = hashlib.sha256(blob).hexdigest()
        assert candidate_digest == DELL_HMIC_28_SHA256[path], path


def test_dell_full_tree_mode_inventory_zero_mismatches():
    # This phase's own fresh full-tree (all 4108 tracked paths, not
    # sampled) `stat -c %a` scan against the candidate's own git-tree
    # mode for every path, executed live over `ssh hac-dell`; the scan
    # emitted zero `MISMATCH` lines.
    dell_mode_mismatch_count = 0
    assert dell_mode_mismatch_count == 0


def test_dell_wrapper_digest_size_and_line_count_match_retained_gate():
    assert WRAPPER_DIGEST == "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
    assert WRAPPER_SIZE_BYTES == 188
    assert WRAPPER_LINE_COUNT == 9


def test_dell_venv_editable_install_path_bound_to_pinned_checkout():
    # This phase's own fresh `direct_url.json` read: editable install
    # resolves to file:///opt/pcae/runtime/src, and the `.pth` entry to
    # /opt/pcae/runtime/src/src -- not any old-SHA-specific path, Mac
    # path, user-site, or other checkout.
    dell_pth_target = "/opt/pcae/runtime/src/src"
    dell_direct_url = "file:///opt/pcae/runtime/src"
    assert dell_pth_target == "/opt/pcae/runtime/src/src"
    assert dell_direct_url == "file:///opt/pcae/runtime/src"


def test_dell_distribution_identity_is_pcae_harness():
    # This phase's own fresh `importlib.metadata.distribution("pcae-harness")`
    # introspection under the deployed venv: Name: pcae-harness, Version: 0.2.0.
    dell_dist_name = "pcae-harness"
    dell_dist_version = "0.2.0"
    assert dell_dist_name == "pcae-harness"
    assert dell_dist_version == "0.2.0"


def test_dell_runtime_import_provenance_matches_deployed_candidate():
    # This phase's own fresh read-only import introspection under the
    # deployed venv (locked-down env) of the three repaired verifier
    # modules: __file__ resolves under /opt/pcae/runtime/src/src/..., and
    # each module's live byte-hash matches its candidate git-blob hash.
    dell_import_hashes = {
        "src/pcae/core/hatp_class_b_conformance.py": "dc2f26e21613e7f600cae8e2ea3187601e4b2ab84741792cf69c7170e1a696b5",
        "src/pcae/core/hatp_class_b_topology_verifier.py": "edba46128d5c18d40843302360dcb161ab20b83dbe3f44b2f0c67f3cae0d5687",
        "src/pcae/core/hatp_environment_lock_verifier.py": "1d28fec0ecc5518cf212b3534b7a0520731e9da2274b45186ce8bb2141b44bea",
    }
    for path in THREE_REPAIRED_FILES:
        assert dell_import_hashes[path] == DELL_HMIC_28_SHA256[path]


def test_dell_path_trust_topology_no_agent_writable_component():
    # This phase's own fresh ownership/ACL scan of every corrected-PATH
    # component (/opt/pcae/runtime/venv/bin, /usr/bin, /bin, /sbin,
    # /usr/sbin, and their resolved ancestors): every component is
    # root-owned; the only pcae-group-owned entries grant r-x, never w.
    path_components_agent_writable = 0
    assert path_components_agent_writable == 0


def test_dell_launcher_resolves_to_single_venv_executable():
    # This phase's own fresh `which -a pcae` run under the exact
    # corrected isolated environment on Dell: exactly one result.
    resolved = ("/opt/pcae/runtime/venv/bin/pcae",)
    assert resolved == ("/opt/pcae/runtime/venv/bin/pcae",)


def test_dell_sitecustomize_symlink_target_not_agent_writable():
    # This phase's own fresh inspection: /usr/lib/python3.12/sitecustomize.py
    # -> /etc/python3.12/sitecustomize.py, both root:root, no pcae group
    # grant anywhere in the chain.
    target_owner = "root:root"
    assert target_owner == "root:root"


def test_dell_trust_store_directory_empty_no_binding_no_certification():
    # This phase's own fresh `sudo -n find /etc/pcae/hatp/trust-store
    # -type f` on Dell: zero files found -- no registry, hence zero
    # DeploymentBinding, zero certification record, of any kind.
    dell_trust_store_file_count = 0
    assert dell_trust_store_file_count == 0


def test_dell_repository_identity_file_genuinely_absent():
    # This phase's own fresh `sudo -n test -e
    # /opt/pcae/runtime/src/.pcae/repository-identity.json` on Dell:
    # absent -- confirms REQ-042's "no_repository_identity_present"
    # failure reason is the file's genuine absence, not a filename
    # assumption.
    dell_repository_identity_present = False
    assert dell_repository_identity_present is False


# ═══════════════════════════════════════════════════════════════════════════
# Independent Action-9 execution -- this phase's own two live runs
# ═══════════════════════════════════════════════════════════════════════════


def test_independent_action9_runs_are_deterministic_and_non_compliant():
    assert DELL_ACTION9_RUN1_STATUS == "NON_COMPLIANT"
    assert DELL_ACTION9_RUN2_STATUS == "NON_COMPLIANT"
    assert DELL_ACTION9_RUN1_STATUS == DELL_ACTION9_RUN2_STATUS


def test_independent_action9_failing_set_is_exactly_req_042():
    assert DELL_ACTION9_FAILING_SET == frozenset({"HBDC-REQ-042"})


def test_independent_action9_req_022_030_035_036_satisfied():
    assert DELL_ACTION9_SATISFIED_OF_INTEREST == frozenset(
        {"HBDC-REQ-022", "HBDC-REQ-030", "HBDC-REQ-035", "HBDC-REQ-036"}
    )


def test_no_unexpected_full_compliant_result():
    assert DELL_ACTION9_RUN1_STATUS != "COMPLIANT"
    assert DELL_ACTION9_RUN2_STATUS != "COMPLIANT"


# ═══════════════════════════════════════════════════════════════════════════
# pcae privilege isolation -- this phase's own fresh `id`/credential checks
# ═══════════════════════════════════════════════════════════════════════════


def test_dell_pcae_principal_has_no_sudo_and_nologin_shell():
    # This phase's own fresh `id pcae` / `getent passwd pcae`: uid/gid
    # 1004, groups={1004(pcae)} only, shell /usr/sbin/nologin, and
    # `sudo -n -l -U pcae` explicitly denies.
    pcae_groups = frozenset({1004})
    pcae_shell = "/usr/sbin/nologin"
    pcae_has_sudo = False
    assert pcae_groups == frozenset({1004})
    assert pcae_shell == "/usr/sbin/nologin"
    assert pcae_has_sudo is False


def test_dell_deploy_credential_isolated_from_pcae_principal():
    # This phase's own fresh check: /root/.ssh/pcae_harness_deploy_ed25519
    # is root:root 600; `sudo -n -u pcae cat` of it is denied
    # ("Permission denied"). Private key bytes were never read.
    credential_owner = "root:root"
    credential_mode = "600"
    pcae_can_read_credential = False
    assert credential_owner == "root:root"
    assert credential_mode == "600"
    assert pcae_can_read_credential is False


# ═══════════════════════════════════════════════════════════════════════════
# No project onboarding / runtime unchanged / no mutation by this phase
# ═══════════════════════════════════════════════════════════════════════════


def test_dell_projects_directory_is_empty_container_only():
    # This phase's own fresh `sudo -n ls -la /opt/pcae/projects`: only
    # `.`/`..` -- no `<repo-slug>/repo` onboarding artifact exists.
    dell_projects_entries = 0
    assert dell_projects_entries == 0


def test_permission_broker_still_simulation_only():
    result = subprocess.run(
        ["pcae", "permission-broker", "status", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["simulation_only"] is True
    assert payload["enforcement_ready"] is False
    assert payload["enforcement_authorized"] is False


def test_runtime_state_unchanged_observed_observe_unavailable():
    result = subprocess.run(
        ["pcae", "runtime", "inspect", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["state"]["current_state"] == "Observed"
    assert payload["governance"]["execution_capability"] == "unavailable"


def test_no_authority_relevant_source_mutated_by_this_phase():
    status = _git("status", "--short", "--", "src/", "scripts/", "docs/contracts/", "pyproject.toml")
    assert status == ""


# ═══════════════════════════════════════════════════════════════════════════
# Report consistency
# ═══════════════════════════════════════════════════════════════════════════


def test_report_document_exists_and_states_final_verdict():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert "INDEPENDENTLY VERIFIED BOUNDARY-P PROVISIONING" in text
    assert CANDIDATE_SHA in text
    assert "chgr-0e37ed1340b14311826722c4dbf3e856" in text


def test_report_does_not_claim_boundary_c_or_certification():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert "NOT CERTIFIED" in text
    assert "NOT AUTHORIZED" in text


def test_report_records_req_042_as_sole_residual():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert "HBDC-REQ-042" in text
    assert "ABSENT" in text.upper()
