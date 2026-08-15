"""Phase 149O.20L.7D.3 -- Action-6 File-Mode + Continuation-Baseline
Proposition Amendment.

This phase is analysis + proposition amendment + human election +
authorization publication only -- it does not execute Action 6, does
not execute Actions 7-9, does not rerun Actions 1-5, and does not
mutate Dell Class-B infrastructure. It repairs Finding D3-1 (Action 6's
frozen `chmod 0640` blanket-strips tracked executable bits, defeating
its own clean-working-tree read-back) with a narrow, deterministic
Git-index-mode-to-filesystem-mode mapping, and discloses Finding D3-2
(the retained Actions-1-5 baseline requires a fresh, explicitly bound
continuation authority rather than silent reuse of the original
absent-everything-host authorization) and Finding D3-3 (no canonical
CHGR supersession/lifecycle-transition CLI mechanism exists yet, so
precedence between the old and new CHGR is established textually, not
by an invented linkage field).

Independent of the 149O.20L.7D.2 companion module: this module neither
imports nor re-executes any of that module's fixtures or assertions.
Where the underlying defect/repair is a pure Git/filesystem operation
(not a live-SSH Dell mutation), this module reproduces it directly
against a disposable local clone of this very repository -- no network
access, no `sudo`, no Dell host -- rather than only re-deriving static
prose facts from the phase doc. Dell-host-specific facts (live SSH
baseline reconfirmation) and the human-election chain are checked
against the phase doc and the published CHGR artifact, which are this
phase's own persisted evidence for those inherently non-reproducible-
in-CI facts.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"
DELL_2_7D2_COMMIT = "33f1dc0bae9c0fdba1bc792673ceb8193993734a"
OLD_CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
NEW_CHGR_ID = "chgr-541cb08c313b4f8884970172d37c5a1d"
WRAPPER_DIGEST = (
    "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
)

PHASE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
)
NEW_CHGR_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / f"{NEW_CHGR_ID}.json"
)
OLD_CHGR_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / f"{OLD_CHGR_ID}.json"
)

EXPECTED_100755_PATHS = {
    ".githooks/pre-commit",
    ".githooks/pre-push",
    "scripts/check-docs-updated.sh",
    ".pcae/authority-evaluation/records/records/"
    "prp-03cfe21aca284d009e71a2581c984dc0/"
    "aeval-5b7a1a65be774d45b494b3489e3ed33b.json",
    ".pcae/authority-evaluation/records/records/"
    "prp-af987a7157804bdfb13dc06e6a060459/"
    "aeval-e7c6272fc2c1456babda84600b474805.json",
    ".pcae/publication-execution/published/"
    "prp-af987a7157804bdfb13dc06e6a060459.json",
}


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_doc_text_unwrapped(phase_doc_text: str) -> str:
    """Markdown prose is hard-wrapped at ~72 cols; some phrases this
    module checks for span a wrap point. Collapse all whitespace runs
    (including the wrap-induced newline) to a single space so those
    checks are insensitive to line-wrap position, not to actual content.
    """
    return " ".join(phase_doc_text.split())


@pytest.fixture(scope="module")
def phase_doc_text_no_whitespace(phase_doc_text: str) -> str:
    """For tokens (digests, SHAs) that may be split mid-token by a hard
    line wrap with no hyphen -- strip all whitespace entirely.
    """
    return re.sub(r"\s+", "", phase_doc_text)


@pytest.fixture(scope="module")
def new_chgr_record() -> dict:
    return json.loads(NEW_CHGR_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pinned_tree_listing() -> list[tuple[str, str]]:
    """(index_mode, path) for every tracked entry at the pinned commit."""
    out = _git(["ls-tree", "-r", PINNED_SOURCE_SHA], cwd=REPO_ROOT).stdout
    entries = []
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        idx_mode = meta.split()[0]
        entries.append((idx_mode, path))
    return entries


@pytest.fixture(scope="module")
def scratch_checkout(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A disposable local clone of this repo, checked out at the pinned
    commit -- never the production /opt/pcae path, never a live host.
    """
    scratch_dir = tmp_path_factory.mktemp("phase_149o_20l_7d_3_scratch")
    src = scratch_dir / "src"
    _git(["clone", "--no-checkout", str(REPO_ROOT), str(src)], cwd=scratch_dir)
    _git(["checkout", "--detach", PINNED_SOURCE_SHA], cwd=src)
    return src


# -- Immutable-plan reconstruction (from commit, not paraphrase) -----------


def test_immutable_7b1_commit_contains_original_defective_command(tmp_path: Path) -> None:
    text = _git(
        [
            "show",
            f"{IMMUTABLE_7B1_COMMIT}:docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
        ],
        cwd=REPO_ROOT,
    ).stdout
    assert "sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \\;" in text
    assert PINNED_SOURCE_SHA in text


def test_7d2_commit_reconstructs_real_failure_evidence() -> None:
    text = _git(
        [
            "show",
            f"{DELL_2_7D2_COMMIT}:docs/PHASE_149O_20L_7D_2_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION_RETRY.md",
        ],
        cwd=REPO_ROOT,
    ).stdout
    assert "6 files changed, 0 insertions(+), 0 deletions(-)" in text
    assert "old mode 100755" in text
    assert "new mode 100644" in text
    assert OLD_CHGR_ID in text


# -- Tracked-mode inventory (full, not just the six exposed paths) ---------


def test_pinned_tree_has_exactly_4030_tracked_entries(
    pinned_tree_listing: list[tuple[str, str]]
) -> None:
    assert len(pinned_tree_listing) == 4030


def test_pinned_tree_mode_breakdown_matches_disclosed_inventory(
    pinned_tree_listing: list[tuple[str, str]]
) -> None:
    modes = [m for m, _ in pinned_tree_listing]
    assert modes.count("100644") == 4024
    assert modes.count("100755") == 6
    assert "120000" not in modes  # no symlinks
    assert "160000" not in modes  # no submodules


def test_pinned_tree_100755_paths_match_exactly_the_disclosed_six(
    pinned_tree_listing: list[tuple[str, str]]
) -> None:
    actual = {path for mode, path in pinned_tree_listing if mode == "100755"}
    assert actual == EXPECTED_100755_PATHS


# -- Defect classification: reproduce the real defect in scratch -----------


def test_original_defective_command_reproduces_exact_six_file_dirty_status(
    scratch_checkout: Path,
) -> None:
    for root, dirs, files in os.walk(scratch_checkout):
        dirs[:] = [d for d in dirs if d != ".git"]
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o750)
        for f in files:
            os.chmod(os.path.join(root, f), 0o640)

    status = _git(["status", "--short"], cwd=scratch_checkout).stdout
    dirty_paths = {line[3:] for line in status.splitlines()}
    assert dirty_paths == EXPECTED_100755_PATHS

    diff_stat = _git(["diff", "--stat"], cwd=scratch_checkout).stdout
    assert "6 files changed, 0 insertions(+), 0 deletions(-)" in diff_stat


def test_defect_reproduction_is_mode_only_zero_content_diff(
    scratch_checkout: Path,
) -> None:
    # Continues from the dirtied state left by the previous test's
    # module-scoped fixture reuse would be order-dependent; re-dirty
    # explicitly here to keep this test independently meaningful.
    for root, dirs, files in os.walk(scratch_checkout):
        if root.endswith("/.git") or "/.git/" in root:
            continue
        for f in files:
            os.chmod(os.path.join(root, f), 0o640)

    diff_text = _git(
        ["diff", PINNED_SOURCE_SHA, "--", "."], cwd=scratch_checkout
    ).stdout
    # A pure mode-change diff has no +/- content lines, only headers.
    content_lines = [
        line
        for line in diff_text.splitlines()
        if line.startswith("+") or line.startswith("-")
        if not line.startswith("+++") and not line.startswith("---")
    ]
    assert content_lines == []


# -- Repaired candidate: deterministic index-mode mapping -------------------


def _apply_repaired_mode_mapping(root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath.endswith("/.git") or "/.git/" in dirpath or dirpath.endswith("/.git"):
            continue
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for d in dirnames:
            os.chmod(os.path.join(dirpath, d), 0o750)
        for f in filenames:
            full = os.path.join(dirpath, f)
            is_exec = os.stat(full).st_mode & 0o100 != 0
            os.chmod(full, 0o750 if is_exec else 0o640)


def test_repaired_candidate_produces_clean_git_status(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    scratch_dir = tmp_path_factory.mktemp("phase_149o_20l_7d_3_repair_scratch")
    src = scratch_dir / "src"
    _git(["clone", "--no-checkout", str(REPO_ROOT), str(src)], cwd=scratch_dir)
    _git(["checkout", "--detach", PINNED_SOURCE_SHA], cwd=src)

    _apply_repaired_mode_mapping(src)

    assert _git(["status", "--short"], cwd=src).stdout == ""
    assert _git(["diff", "--stat"], cwd=src).stdout == ""


def test_repaired_candidate_preserves_all_tracked_modes_deterministically(
    tmp_path_factory: pytest.TempPathFactory,
    pinned_tree_listing: list[tuple[str, str]],
) -> None:
    scratch_dir = tmp_path_factory.mktemp("phase_149o_20l_7d_3_repair_full_scratch")
    src = scratch_dir / "src"
    _git(["clone", "--no-checkout", str(REPO_ROOT), str(src)], cwd=scratch_dir)
    _git(["checkout", "--detach", PINNED_SOURCE_SHA], cwd=src)

    _apply_repaired_mode_mapping(src)

    mismatches = []
    for idx_mode, path in pinned_tree_listing:
        want = "750" if idx_mode == "100755" else "640"
        got = oct(os.lstat(src / path).st_mode & 0o777)[2:]
        if got != want:
            mismatches.append((path, idx_mode, got, want))
    assert mismatches == []


def test_repaired_candidate_preserves_executable_invocability(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    scratch_dir = tmp_path_factory.mktemp("phase_149o_20l_7d_3_exec_scratch")
    src = scratch_dir / "src"
    _git(["clone", "--no-checkout", str(REPO_ROOT), str(src)], cwd=scratch_dir)
    _git(["checkout", "--detach", PINNED_SOURCE_SHA], cwd=src)

    _apply_repaired_mode_mapping(src)

    assert os.access(src / ".githooks" / "pre-commit", os.X_OK)
    assert os.access(src / "scripts" / "check-docs-updated.sh", os.X_OK)
    assert not os.access(src / "pyproject.toml", os.X_OK)


def test_repaired_candidate_rollback_matches_action_4_postcondition(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    scratch_dir = tmp_path_factory.mktemp("phase_149o_20l_7d_3_rollback_scratch")
    src = scratch_dir / "src"
    _git(["clone", "--no-checkout", str(REPO_ROOT), str(src)], cwd=scratch_dir)
    _git(["checkout", "--detach", PINNED_SOURCE_SHA], cwd=src)
    _apply_repaired_mode_mapping(src)

    # Frozen Action-6 rollback (single explicit non-glob path).
    import shutil

    shutil.rmtree(src)
    src.mkdir(parents=True)
    os.chmod(src, 0o750)

    assert list(src.iterdir()) == []
    assert oct(src.stat().st_mode & 0o777) == "0o750"


# -- Continuation-baseline / Action-2 / Actions-7-9 disclosures -------------


def test_phase_doc_discloses_finding_d3_1(phase_doc_text: str) -> None:
    assert "Finding D3-1" in phase_doc_text
    assert re.search(
        r"proposition \(command-\s*text\) defect", phase_doc_text
    )


def test_phase_doc_discloses_finding_d3_2_retained_baseline(phase_doc_text: str) -> None:
    assert "Finding D3-2" in phase_doc_text
    assert "retained-baseline authority gap" in phase_doc_text


def test_phase_doc_discloses_finding_d3_3_chgr_machinery_gap(phase_doc_text: str) -> None:
    assert "Finding D3-3" in phase_doc_text
    assert "No transition command exists this increment" in phase_doc_text


def test_phase_doc_defines_continuation_gates_with_stop_semantics(phase_doc_text: str) -> None:
    assert "Continuation gates for Actions 1-5" in phase_doc_text
    assert "STOP. No repair under continuation authority" in phase_doc_text


def test_phase_doc_adjudicates_action_2_as_retained_principal_not_fresh(
    phase_doc_text: str, phase_doc_text_unwrapped: str
) -> None:
    assert "does **not** pretend the existing `pcae` principal is a" in phase_doc_text
    assert "does **not** delete/recreate the account" in phase_doc_text_unwrapped


def test_phase_doc_determines_actions_7_9_unchanged(phase_doc_text: str) -> None:
    assert "no downstream change is hidden" in phase_doc_text


def test_phase_doc_defines_rollback_semantics_not_auto_teardown_1_5(
    phase_doc_text: str,
) -> None:
    assert (
        "Actions 1-5 are explicitly NOT automatically rolled back"
        in phase_doc_text
    )


def test_phase_doc_reconfirms_pinned_sha_wrapper_digest_and_hbdc_042_unchanged(
    phase_doc_text: str, phase_doc_text_no_whitespace: str
) -> None:
    assert PINNED_SOURCE_SHA in phase_doc_text
    assert WRAPPER_DIGEST in phase_doc_text_no_whitespace
    assert "HBDC-REQ-042" in phase_doc_text


def test_hbdc_req_042_source_still_driven_only_by_deploymentbinding_absence() -> None:
    verifier = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py").read_text()
    assert "no_active_deployment_binding_matches_repository_and_root" in verifier
    assert "no_repository_identity_present" in verifier


# -- Exclusions ---------------------------------------------------------


def test_phase_doc_preserves_all_named_exclusions(phase_doc_text: str) -> None:
    for phrase in (
        "No DeploymentBinding",
        "Boundary C: NOT AUTHORIZED",
        "Boundary A: NOT AUTHORIZED",
        "No Dell mutation this phase",
        "No production/contracts modification",
    ):
        assert phrase in phase_doc_text


def test_no_production_or_contract_files_touched_this_phase() -> None:
    diff = _git(
        [
            "diff",
            "--stat",
            f"{DELL_2_7D2_COMMIT}..HEAD",
            "--",
            "src/pcae/**",
            "scripts/**",
            "docs/contracts/**",
        ],
        cwd=REPO_ROOT,
    ).stdout
    assert diff.strip() == ""


# -- Authority / election / confirmation / CHGR chain -----------------------


def test_old_chgr_still_verifies_and_is_untouched() -> None:
    result = subprocess.run(
        ["pcae", "governance-record", "verify", str(OLD_CHGR_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "outcome: verified" in result.stdout


def test_new_chgr_verifies(new_chgr_record: dict) -> None:
    result = subprocess.run(
        ["pcae", "governance-record", "verify", str(NEW_CHGR_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "outcome: verified" in result.stdout


def test_new_chgr_selected_option_is_approve(new_chgr_record: dict) -> None:
    assert new_chgr_record["selected_option_id"] == "approve"
    assert new_chgr_record["lifecycle_state"] == "published"


def test_new_chgr_decision_subject_names_dell_and_findings(new_chgr_record: dict) -> None:
    subject = new_chgr_record["decision_subject"]
    assert DELL_MACHINE_ID in subject
    assert "D3-1" in subject
    assert "D3-2" in subject
    assert "No execution authorized this phase." in subject


def test_new_chgr_rationale_names_old_chgr_and_denies_reuse(new_chgr_record: dict) -> None:
    rationale = new_chgr_record["rationale"]
    assert OLD_CHGR_ID in rationale
    assert "does not authorize continuation" in rationale


def test_new_chgr_conditions_exclude_execution_and_boundaries(new_chgr_record: dict) -> None:
    conditions = new_chgr_record["conditions"]
    for phrase in (
        "Action 6 execution",
        "Actions 7-9 execution",
        "Boundary C certification",
        "Boundary A activation",
        "Permission Broker",
    ):
        assert phrase in conditions


def test_new_chgr_decision_maker_is_named_human_not_generic_role(
    new_chgr_record: dict,
) -> None:
    identity = new_chgr_record["decision_maker_identity_evidence"]["identifier"]
    assert identity == "Atila Madai"


def test_new_chgr_and_old_chgr_have_distinct_record_ids(new_chgr_record: dict) -> None:
    assert new_chgr_record["record_id"] != OLD_CHGR_ID
    assert new_chgr_record["record_id"] == NEW_CHGR_ID


# -- No production Dell mutation this phase (static disclosure check) -------


def test_phase_doc_records_read_only_ssh_evidence_not_mutation_commands(
    phase_doc_text: str,
) -> None:
    # Fresh baseline verification section must use read-only forms only.
    section_marker = "## 9. Fresh Read-Only Dell Baseline Verification"
    assert section_marker in phase_doc_text
    idx = phase_doc_text.index(section_marker)
    next_section_idx = phase_doc_text.index("## 10.", idx)
    section_text = phase_doc_text[idx:next_section_idx]
    for forbidden in ("git clone", "chmod 0640", "useradd", "groupadd", "apt-get install"):
        assert forbidden not in section_text
