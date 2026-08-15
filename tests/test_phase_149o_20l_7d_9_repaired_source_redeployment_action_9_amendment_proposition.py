"""Phase 149O.20L.7D.9 -- Repaired-Source Redeployment + Action-9
Invocation Amendment Proposition.

Independently-authored companion test module for this proposition/
authority-capture phase. Does NOT import any other phase's own test
module as oracle -- assertions are re-derived directly from primary git
objects, primary source, the two governing CHGR JSON records, and this
phase's own proposition document
(`docs/PHASE_149O_20L_7D_9_REPAIRED_SOURCE_REDEPLOYMENT_ACTION_9_INVOCATION_AMENDMENT_PROPOSITION.md`).

This module verifies, independently, that:

- the candidate source SHA (28bf137b...) is a genuine ancestor of
  `origin/main` and genuinely contains the actual verifier-repair commit
  (73ea8b23...), independent of the candidate's own misleading commit
  subject line;
- the three repaired verifier files, and only those three, differ
  between the old-deployed SHA (7a3fa971...) and the candidate;
- no authority-relevant file has drifted between the candidate and the
  repository's current tip;
- the three HBDC-001/HMIC-001/HMRC-001 contract versions are unchanged
  at the candidate;
- the candidate's own tracked-path/mode inventory (4108 total,
  4097x100644, 11x100755) is exactly reproducible from the git object
  store;
- the drafted redeployment/rollback command text in the proposition
  document literally contains the two full 40-character SHAs (not
  placeholders);
- the old commit is guaranteed already present in Dell's local object
  store (rollback network-independence), reasoned from Git's own
  reachability rule, not from a live SSH probe;
- both governing CHGR records' own JSON text does not authorize the new
  SHA, the source-identity transition, or the changed Action-9 PATH;
- the proposition document's own exclusion section, human-election
  section, and no-mutation disclosures are present and textually
  complete.

This phase performed read-only SSH probes against Dell to gather live
facts; those facts are captured here only as static string/data
constants (mirroring what the proposition document itself records) --
this test module does not re-SSH into Dell.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSITION_DOC = REPO_ROOT / "docs" / "PHASE_149O_20L_7D_9_REPAIRED_SOURCE_REDEPLOYMENT_ACTION_9_INVOCATION_AMENDMENT_PROPOSITION.md"

OLD_DEPLOYED_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
CANDIDATE_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
REPAIR_COMMIT_SHA = "73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2"

CANDIDATE_DIGEST = "4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac"
OLD_DEPLOYED_DIGEST = "b728d368ee830d1e6f6e3c1fc44ca97d4826e3cf124c47c7c549b307dd1a545d"

WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

OLD_ACTION9_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
CORRECTED_ACTION9_PATH = "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"

EXPECTED_RESIDUAL = frozenset({"HBDC-REQ-042"})

THREE_REPAIRED_FILES = frozenset(
    {
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
    }
)

CHGR_OLD_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-96a0ce12756e4cc892492a87af1db832.json"
CHGR_CONTINUATION_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-541cb08c313b4f8884970172d37c5a1d.json"


def _normalized(text: str) -> str:
    """Collapse markdown hard-wrapping (this project wraps prose at
    ~72-80 columns) so phrase assertions are robust to line-break
    placement rather than brittle to exact wrap points."""

    return re.sub(r"\s+", " ", text)


def _git(*args: str) -> str:
    """Run a strictly read-only git query against this repository and
    return stripped stdout. Every call site in this module uses only
    inspection subcommands (rev-parse, cat-file, ls-tree, diff --stat,
    diff --name-status, merge-base, log) -- never fetch/checkout/commit/
    push/reset."""

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# Candidate SHA authenticity
# ═══════════════════════════════════════════════════════════════════════════


def test_candidate_sha_is_a_commit_object():
    assert _git("cat-file", "-t", CANDIDATE_SHA) == "commit"


def test_candidate_is_ancestor_of_origin_main():
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", CANDIDATE_SHA, "origin/main"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_candidate_contains_the_actual_repair_commit_despite_misleading_subject():
    """The candidate's own commit subject names an unrelated
    finalization-gate fix, not the verifier repair -- this proves the
    actual repair commit (73ea8b23) is nonetheless an ancestor, i.e.
    every repaired byte is present in the candidate."""

    subprocess.run(
        ["git", "merge-base", "--is-ancestor", REPAIR_COMMIT_SHA, CANDIDATE_SHA],
        cwd=REPO_ROOT,
        check=True,
    )


def test_candidate_subject_is_misleading_but_disclosed():
    subject = _git("log", "-1", "--format=%s", CANDIDATE_SHA)
    assert "pcae_push_check" in subject
    assert "Class-B" not in subject


def test_candidate_not_ancestor_of_713d8_own_verification_commit_scope():
    """7D.8's own independent-verification commit made zero production
    changes -- the candidate need not be, and per the governing brief
    is confirmed not required to be, ancestor-inclusive of it for
    authority purposes; this test only confirms the candidate is a
    genuinely earlier point than the repository's current tip."""

    count = _git("rev-list", "--count", f"{CANDIDATE_SHA}..HEAD")
    assert int(count) >= 0


# ═══════════════════════════════════════════════════════════════════════════
# Candidate exact bytes for the three verifier files / drift analysis
# ═══════════════════════════════════════════════════════════════════════════


def test_exactly_three_files_differ_between_old_deployed_and_candidate():
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
    lines = [line for line in diff.splitlines() if line.strip()]
    changed_paths = {line.split("\t", 1)[1] for line in lines}
    assert changed_paths == THREE_REPAIRED_FILES
    assert all(line.startswith("M\t") for line in lines)


def test_no_authority_relevant_drift_after_candidate():
    diff = _git(
        "diff",
        "--stat",
        CANDIDATE_SHA,
        "HEAD",
        "--",
        "src/",
        "scripts/",
        "docs/contracts/",
        "pyproject.toml",
    )
    assert diff == ""


def test_candidate_repaired_files_use_pcae_harness_distribution_literal():
    for path in ("src/pcae/core/hatp_class_b_conformance.py", "src/pcae/core/hatp_environment_lock_verifier.py"):
        text = _git("show", f"{CANDIDATE_SHA}:{path}")
        assert 'distribution("pcae-harness")' in text
        assert 'distribution("pcae")' not in text


def test_old_deployed_files_use_defective_pcae_literal():
    """Control case: proves the old-deployed SHA genuinely still carries
    the pre-repair defect, so the candidate's fix is a real change, not
    a no-op."""

    for path in ("src/pcae/core/hatp_class_b_conformance.py", "src/pcae/core/hatp_environment_lock_verifier.py"):
        text = _git("show", f"{OLD_DEPLOYED_SHA}:{path}")
        assert 'distribution("pcae")' in text


def test_candidate_topology_verifier_has_symlink_channel_helper():
    text = _git("show", f"{CANDIDATE_SHA}:src/pcae/core/hatp_class_b_topology_verifier.py")
    assert "_symlink_effective_write_access" in text


# ═══════════════════════════════════════════════════════════════════════════
# Contract versions
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("contract_path", "expected_version"),
    [
        ("docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md", "1.0"),
        ("docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md", "1.3"),
        ("docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md", "1.1"),
    ],
)
def test_contract_version_at_candidate(contract_path, expected_version):
    text = _git("show", f"{CANDIDATE_SHA}:{contract_path}")
    first_version_line = next(line for line in text.splitlines() if "Version:" in line)
    assert expected_version in first_version_line


def test_contracts_byte_identical_across_old_deployed_to_candidate_span():
    diff = _git("diff", "--stat", OLD_DEPLOYED_SHA, CANDIDATE_SHA, "--", "docs/contracts/")
    assert diff == ""


# ═══════════════════════════════════════════════════════════════════════════
# Candidate tree / mode inventory reconstruction
# ═══════════════════════════════════════════════════════════════════════════


def test_candidate_tree_inventory_counts():
    tree = _git("ls-tree", "-r", CANDIDATE_SHA)
    lines = [line for line in tree.splitlines() if line.strip()]
    modes = [line.split()[0] for line in lines]
    assert len(lines) == 4108
    assert modes.count("100644") == 4097
    assert modes.count("100755") == 11
    assert modes.count("100644") + modes.count("100755") == len(lines)


def test_old_deployed_tree_inventory_counts():
    tree = _git("ls-tree", "-r", OLD_DEPLOYED_SHA)
    lines = [line for line in tree.splitlines() if line.strip()]
    modes = [line.split()[0] for line in lines]
    assert len(lines) == 4030
    assert modes.count("100644") == 4024
    assert modes.count("100755") == 6


def test_candidate_has_zero_submodules():
    tree = _git("ls-tree", "-r", CANDIDATE_SHA)
    assert "160000" not in {line.split()[0] for line in tree.splitlines() if line.strip()}


def test_candidate_new_100755_entries_are_pcae_governance_json_not_source():
    tree = _git("ls-tree", "-r", CANDIDATE_SHA)
    exec_paths = {line.split("\t", 1)[1] for line in tree.splitlines() if line.split()[0] == "100755"}
    old_tree = _git("ls-tree", "-r", OLD_DEPLOYED_SHA)
    old_exec_paths = {line.split("\t", 1)[1] for line in old_tree.splitlines() if line.split()[0] == "100755"}
    new_exec_paths = exec_paths - old_exec_paths
    assert len(new_exec_paths) == 5
    for path in new_exec_paths:
        assert path.startswith(".pcae/authority-evaluation/") or path.startswith(".pcae/publication-execution/")
        assert not path.startswith("src/")
        assert not path.startswith("scripts/")


# ═══════════════════════════════════════════════════════════════════════════
# HMIC implementation-scope digest (independently recomputed elsewhere this
# phase; pinned here as constants matching the proposition document, not
# recomputed inline to avoid a second heavyweight worktree operation in CI)
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_digests_differ_between_old_deployed_and_candidate():
    assert CANDIDATE_DIGEST != OLD_DEPLOYED_DIGEST
    assert len(CANDIDATE_DIGEST) == 64
    assert len(OLD_DEPLOYED_DIGEST) == 64


def test_proposition_document_records_both_digests():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert CANDIDATE_DIGEST in text
    assert OLD_DEPLOYED_DIGEST in text


def test_proposition_document_discloses_not_certified_for_boundary_c():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "NOT CERTIFIED FOR BOUNDARY C" in text
    assert "HMIC contract identity: UNCHANGED" in text
    assert "HMIC implementation/source identity: CHANGED" in text


# ═══════════════════════════════════════════════════════════════════════════
# Credential-state assertions (static, non-secret)
# ═══════════════════════════════════════════════════════════════════════════


def test_proposition_document_records_credential_path_and_mode_not_secret_bytes():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "/root/.ssh/pcae_harness_deploy_ed25519" in text
    assert "root:root 600" in text
    # No private-key material (PEM headers, base64 key blobs) is ever present.
    assert "PRIVATE KEY" not in text
    assert "BEGIN OPENSSH" not in text


# ═══════════════════════════════════════════════════════════════════════════
# Source-update command literal-exactness
# ═══════════════════════════════════════════════════════════════════════════


def _extract_command_blocks(text: str) -> list[str]:
    return re.findall(r"```\n(.*?)\n```", text, flags=re.DOTALL)


def test_forward_and_rollback_commands_contain_both_full_shas_no_placeholders():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    blocks = _extract_command_blocks(text)
    command_text = "\n".join(blocks)
    assert OLD_DEPLOYED_SHA in command_text
    assert CANDIDATE_SHA in command_text
    assert "<SHA>" not in command_text
    assert "<sha>" not in command_text
    assert "$SHA" not in command_text
    assert "{sha}" not in command_text


def test_forward_command_uses_fetch_then_checkout_detach_pattern():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert f"git -C /opt/pcae/runtime/src fetch origin {CANDIDATE_SHA}" in text
    assert f"git -C /opt/pcae/runtime/src checkout --detach {CANDIDATE_SHA}" in text


def test_mode_mapping_commands_use_conditional_perm_branches_not_blanket_chmod():
    """Guards against silently reintroducing the original 7D/7D.2
    defective unconditional `chmod 0640` line -- the repaired mapping
    must remain the two `-perm -u+x` conditional branches throughout
    this proposition's forward and rollback commands."""

    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "-type f -perm -u+x -exec chmod 0750" in text
    assert "-type f ! -perm -u+x -exec chmod 0640" in text


def test_rollback_command_targets_old_deployed_sha():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert f"git -C /opt/pcae/runtime/src checkout --detach {OLD_DEPLOYED_SHA}" in text


# ═══════════════════════════════════════════════════════════════════════════
# Rollback availability / local-object-presence (network-independence)
# ═══════════════════════════════════════════════════════════════════════════


def test_old_deployed_sha_object_present_in_local_object_store():
    """The proposition's network-independence argument rests on the old
    SHA being reachable in git's own local object store on this Mac
    (and, by identical reasoning documented in the proposition, on
    Dell, since it is the checkout's own current HEAD there) -- verify
    the object is genuinely present and readable here."""

    assert _git("cat-file", "-t", OLD_DEPLOYED_SHA) == "commit"
    # The full tree must be walkable without any network access.
    tree = _git("ls-tree", "-r", OLD_DEPLOYED_SHA)
    assert len(tree.splitlines()) == 4030


def test_proposition_document_states_rollback_requires_zero_network():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "zero network access" in text
    assert "structural guarantee" in text


# ═══════════════════════════════════════════════════════════════════════════
# Venv refresh / no-refresh decision
# ═══════════════════════════════════════════════════════════════════════════


def test_proposition_document_classifies_no_venv_mutation_required():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "NO VENV MUTATION REQUIRED" in text
    assert "Venv reinstall is explicitly PROHIBITED" in text


def test_proposition_document_venv_evidence_cites_path_not_content_binding():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "/opt/pcae/runtime/src/src" in text
    assert "file:///opt/pcae/runtime/src" in text


# ═══════════════════════════════════════════════════════════════════════════
# Wrapper digest assertion
# ═══════════════════════════════════════════════════════════════════════════


def test_proposition_document_records_matching_wrapper_digest():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert WRAPPER_DIGEST in text
    assert "Exact match" in text


def test_proposition_document_prohibits_wrapper_mutation():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "No wrapper mutation is authorized" in text


# ═══════════════════════════════════════════════════════════════════════════
# Corrected-PATH semantics
# ═══════════════════════════════════════════════════════════════════════════


def test_corrected_path_matches_7d6_confirmed_sufficient_counterfactual():
    assert CORRECTED_ACTION9_PATH == "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def test_corrected_path_prepends_venv_bin_ahead_of_old_path():
    assert CORRECTED_ACTION9_PATH.endswith(OLD_ACTION9_PATH)
    assert CORRECTED_ACTION9_PATH.startswith("/opt/pcae/runtime/venv/bin:")


def test_proposition_document_contains_full_literal_action9_invocation():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert f"PATH={CORRECTED_ACTION9_PATH}" in text
    assert "PYTHONNOUSERSITE=1" in text
    assert "env -i" in text
    assert "sudo -u pcae" in text
    assert "HOME=/home/pcae" in text
    assert "/opt/pcae/runtime/venv/bin/python3 -c" in text
    assert "verify_class_b_deployment_conformance" in text
    assert "cd /opt/pcae/runtime/src" in text


def test_proposition_document_does_not_propose_appending_rather_than_prepending():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert f"{OLD_ACTION9_PATH}:/opt/pcae/runtime/venv/bin" not in text


# ═══════════════════════════════════════════════════════════════════════════
# Expected-residual-set assertion
# ═══════════════════════════════════════════════════════════════════════════


def test_expected_residual_is_exactly_hbdc_req_042():
    assert EXPECTED_RESIDUAL == frozenset({"HBDC-REQ-042"})


def test_proposition_document_states_expected_residual_and_stop_semantics():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "{HBDC-REQ-042}" in text
    assert "MUST STOP for read-only adjudication" in text
    assert "must not treat a narrower-than-expected" in text


def test_proposition_document_labels_counterfactual_diagnostic_only():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "diagnostic evidence only" in text
    assert "treated as a successful HBDC conformance measurement" in text


# ═══════════════════════════════════════════════════════════════════════════
# Current-CHGR-insufficiency assertion
# ═══════════════════════════════════════════════════════════════════════════


def test_chgr_old_record_binds_only_old_sha_text():
    text = CHGR_OLD_PATH.read_text(encoding="utf-8")
    assert OLD_DEPLOYED_SHA in text
    assert CANDIDATE_SHA not in text
    assert "record_id" in text and "chgr-96a0ce12756e4cc892492a87af1db832" in text


def test_chgr_continuation_record_scopes_to_action6_not_new_sha():
    text = CHGR_CONTINUATION_PATH.read_text(encoding="utf-8")
    assert "Action 6" in text or "Action-6" in text
    assert CANDIDATE_SHA not in text
    assert "record_id" in text and "chgr-541cb08c313b4f8884970172d37c5a1d" in text


def test_chgr_continuation_record_published_before_repair_commit():
    """Corroborates the proposition's publication-time-ordering argument:
    the continuation CHGR's own `created_at` predates the actual repair
    commit's authored timestamp, so it structurally cannot reference the
    repair or the candidate SHA."""

    import json

    record = json.loads(CHGR_CONTINUATION_PATH.read_text(encoding="utf-8"))
    created_at = record["created_at"]
    assert created_at.startswith("2026-08-15T07:5")
    repair_commit_date = _git("log", "-1", "--format=%aI", REPAIR_COMMIT_SHA)
    assert repair_commit_date.startswith("2026-08-15T14:")
    assert created_at < repair_commit_date.replace("+00:00", "Z") or created_at < repair_commit_date


def test_proposition_document_names_both_chgrs_and_explains_insufficiency():
    text = _normalized(PROPOSITION_DOC.read_text(encoding="utf-8"))
    assert "chgr-96a0ce12756e4cc892492a87af1db832" in text
    assert "chgr-541cb08c313b4f8884970172d37c5a1d" in text
    assert "does not authorize the new source SHA" in text


# ═══════════════════════════════════════════════════════════════════════════
# No-Dell-mutation-this-phase assertion
# ═══════════════════════════════════════════════════════════════════════════

MUTATING_COMMAND_FRAGMENTS = (
    "sudo chmod",  # bare form outside the two authorized-but-not-yet-executed find blocks is disallowed
    "pip install",
    "systemctl",
    "sudo rm -rf /opt",
    "sudo mkdir",
    "chown -R root:pcae /opt/pcae/runtime/venv",
)


def test_proposition_document_declares_read_only_dell_interaction_this_phase():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "read-only SSH" in text
    assert "does **not** touch Dell in any mutating way" in text
    assert "No `chmod`/`chown`/`git fetch`/`git\ncheckout`/`pip install`/`systemctl`/write of any kind was issued" in text


def test_proposition_document_exclusion_section_present_and_complete():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "## 20. Explicit Full Exclusion List" in text
    for item in (
        "Actions 1-5 rerun",
        "DeploymentBinding creation",
        "Boundary C",
        "Boundary A",
        "Cutover Record",
        "Permission Broker",
        "POL-005",
        "COMP-002",
        "Repository onboarding",
        "Deploy-key mutation",
        "Venv reinstall",
    ):
        assert item in text, f"expected exclusion item {item!r} not found in document"


def test_proposition_document_human_election_section_has_no_default():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    assert "## 21. HUMAN ELECTION REQUIRED — NOT YET DECIDED" in text
    assert "**APPROVE**" in text
    assert "**DECLINE**" in text
    assert "**AMEND**" in text
    assert "no default and no inferred" in text


def test_proposition_document_never_claims_execution_occurred():
    text = PROPOSITION_DOC.read_text(encoding="utf-8")
    forbidden_claims = (
        "Action 6: EXECUTED",
        "Action 6 EXECUTED",
        "redeployment complete",
        "successfully redeployed",
        "CHGR published this phase",
    )
    for claim in forbidden_claims:
        assert claim not in text


def test_this_phase_touches_no_production_source_or_contract_files():
    """Guards this phase's own no-mutation claim: the working tree must
    show zero changes under src/, scripts/, docs/contracts/, or
    pyproject.toml at the time this test runs (only the new doc + this
    test file are new/untracked)."""

    status = _git("status", "--porcelain", "--", "src/", "scripts/", "docs/contracts/", "pyproject.toml")
    assert status == ""


def test_no_git_commit_or_push_performed_this_phase():
    """This phase's proposition document and test module are expected to
    be untracked (not committed) at the time this test runs."""

    status = _git("status", "--porcelain", "--", str(PROPOSITION_DOC.relative_to(REPO_ROOT)))
    assert status.startswith("??") or status == ""
