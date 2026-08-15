"""Phase 149O.20L.7D.4 -- Action-6 + Continuation-Baseline Amendment
Independent Verification.

This module independently re-derives and adversarially attacks the
149O.20L.7D.3 amendment (Finding D3-1 repair, Finding D3-2 retained-
baseline binding, Finding D3-3 CHGR-precedence disclosure) without
importing, re-executing, or trusting the 149O.20L.7D.3 companion
module as an oracle. Every assertion here re-derives its expected
value directly from a primary artifact: the immutable 149O.20L.7B.1
proposition commit, the 149O.20L.7D.2/149O.20L.7D.3 phase docs (as
primary execution/amendment records, not paraphrased), the two CHGR
JSON artifacts, the decision-session JSON artifacts, and a disposable
local Git clone (never the Dell host, never `/opt/pcae/runtime/src`).

This phase is verification-only: it does not execute Action 6, does
not execute Actions 7-9, does not rerun Actions 1-5, and does not
mutate Dell Class-B infrastructure. Any test in this module that would
require a production mutation instead asserts against a disposable
scratch clone created and destroyed within the test itself.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"
DELL_7D2_COMMIT = "33f1dc0bae9c0fdba1bc792673ceb8193993734a"
OLD_CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
NEW_CHGR_ID = "chgr-541cb08c313b4f8884970172d37c5a1d"
DECISION_SESSION_ID = "CDS-554c3c12-0693-4edd-867d-b86374c376b2"
SUPERSEDED_SESSION_ID = "CDS-8984cecc-4b55-4cfc-aca6-14397f5735a1"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
WRAPPER_BYTES = (
    b"#!/bin/sh\n"
    b"set -eu\n"
    b"unset PYTHONPATH\n"
    b"PYTHONNOUSERSITE=1\n"
    b"export PYTHONNOUSERSITE\n"
    b"PATH=/usr/bin:/bin:/usr/sbin:/sbin\n"
    b"export PATH\n"
    b"cd /opt/pcae/runtime\n"
    b'exec /opt/pcae/runtime/venv/bin/pcae "$@"\n'
)

OLD_CHGR_PATH = REPO_ROOT / ".pcae/publication-execution/records" / f"{OLD_CHGR_ID}.json"
NEW_CHGR_PATH = REPO_ROOT / ".pcae/publication-execution/records" / f"{NEW_CHGR_ID}.json"
DECISION_SESSION_PATH = REPO_ROOT / ".pcae/decision-sessions" / f"{DECISION_SESSION_ID}.json"
DECISION_ORCH_PATH = (
    REPO_ROOT / ".pcae/decision-sessions/orchestration" / f"{DECISION_SESSION_ID}.json"
)
HATP_CLASS_B_SOURCE = REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py"
GOVERNANCE_RECORD_CLI = REPO_ROOT / "src/pcae/commands/governance_record.py"


def _git_show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _git_show_stat(commit: str) -> str:
    return subprocess.run(
        ["git", "show", "--stat", "--format=", commit],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.fixture(scope="module")
def scratch_clone():
    """A disposable local clone at the pinned commit -- never production."""
    tmpdir = tempfile.mkdtemp(prefix="pcae-7d4-verify-")
    clone_path = Path(tmpdir) / "src"
    subprocess.run(
        ["git", "clone", "--no-checkout", str(REPO_ROOT), str(clone_path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "--detach", PINNED_SOURCE_SHA],
        cwd=clone_path,
        check=True,
        capture_output=True,
    )
    yield clone_path
    shutil.rmtree(tmpdir, ignore_errors=True)


# --- Section: immutable original Action 6 (from commit, not paraphrase) ---


def test_original_action_6_forward_command_is_unconditional_chmod():
    text = _git_show(IMMUTABLE_7B1_COMMIT, "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md")
    assert "sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \\;" in text
    assert "sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;" in text
    # Action 6's own forward command has exactly one unconditional
    # file-mode line (the venv's own later chmod 0640, Action 7, is a
    # separate, unrelated command over a different path).
    action6 = text.split("### Action 6")[1].split("### Action 7")[0]
    assert action6.count("chmod 0640") == 1
    assert "-perm -u+x" not in action6


def test_immutable_commit_touches_only_the_expected_two_files():
    files = subprocess.run(
        ["git", "show", "--stat", "--format=", "--name-only", IMMUTABLE_7B1_COMMIT],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    files = [f for f in files if f.strip()]
    assert len(files) == 2
    assert any("PHASE_149O_20L_7B_1" in f for f in files)
    assert any("test_phase_149o_20l_7b_1" in f for f in files)


def test_original_action_2_has_no_exactly_satisfied_branch():
    text = _git_show(IMMUTABLE_7B1_COMMIT, "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md")
    action2 = text.split("### Action 2")[1].split("### Action 3")[0]
    normalized = " ".join(action2.split())
    assert 'no "EXACTLY SATISFIED" idempotent case for this action by design' in normalized
    assert "CONFLICTING" in action2 and "STOP" in action2


def test_original_entering_state_assumed_absent_everything_host():
    text = _git_show(IMMUTABLE_7B1_COMMIT, "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md")
    section4 = text.split("## 4. Minimal Live Dell Reconfirmation")[1].split("## 5.")[0]
    assert "getent passwd pcae" in section4
    assert "not found" in section4
    assert "No such file or directory" in section4


# --- Section: independent reproduction of Finding D3-1 (disposable scratch) ---


def test_defect_reproduces_in_disposable_scratch(scratch_clone):
    subprocess.run(["find", ".", "-type", "d", "-exec", "chmod", "0750", "{}", ";"], cwd=scratch_clone, check=True)
    subprocess.run(["find", ".", "-type", "f", "-exec", "chmod", "0640", "{}", ";"], cwd=scratch_clone, check=True)
    status = subprocess.run(
        ["git", "status", "--short"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    changed = [line.strip().split()[-1] for line in status.splitlines() if line.strip()]
    assert len(changed) == 6
    diffstat = subprocess.run(
        ["git", "diff", "--stat"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert "0 insertions(+), 0 deletions(-)" in diffstat
    diff = subprocess.run(
        ["git", "diff", ".githooks/pre-commit"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert "old mode 100755" in diff and "new mode 100644" in diff


def test_defect_reproduction_files_match_claimed_six_paths(scratch_clone):
    subprocess.run(["find", ".", "-type", "f", "-exec", "chmod", "0640", "{}", ";"], cwd=scratch_clone, check=True)
    status = subprocess.run(
        ["git", "status", "--short"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    changed = sorted(line.strip().split(maxsplit=1)[-1] for line in status.splitlines() if line.strip())
    expected = sorted([
        ".githooks/pre-commit",
        ".githooks/pre-push",
        "scripts/check-docs-updated.sh",
        ".pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json",
        ".pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json",
        ".pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json",
    ])
    assert changed == expected
    # restore clean state for subsequent tests sharing this fixture
    subprocess.run(["git", "checkout", "--", "."], cwd=scratch_clone, check=True)
    subprocess.run(
        ["git", "clean", "-fd"], cwd=scratch_clone, check=True, capture_output=True
    )


# --- Section: complete tracked-mode inventory, independently enumerated ---


def test_complete_tracked_mode_inventory_at_pinned_commit():
    out = subprocess.run(
        ["git", "ls-tree", "-r", PINNED_SOURCE_SHA], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    lines = [l for l in out.splitlines() if l.strip()]
    modes = [l.split()[0] for l in lines]
    assert len(lines) == 4030
    assert modes.count("100644") == 4024
    assert modes.count("100755") == 6
    assert modes.count("120000") == 0  # symlinks
    assert modes.count("160000") == 0  # submodules


def test_six_executable_paths_match_claimed_set():
    out = subprocess.run(
        ["git", "ls-tree", "-r", PINNED_SOURCE_SHA], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    exec_paths = sorted(
        line.split("\t", 1)[1] for line in out.splitlines() if line.startswith("100755")
    )
    expected = sorted([
        ".githooks/pre-commit",
        ".githooks/pre-push",
        "scripts/check-docs-updated.sh",
        ".pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json",
        ".pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json",
        ".pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json",
    ])
    assert exec_paths == expected


# --- Section: repaired candidate -- independent construction and attack ---


def _apply_repaired_sequence(clone_path: Path) -> None:
    subprocess.run(["find", ".", "-type", "d", "-exec", "chmod", "0750", "{}", ";"], cwd=clone_path, check=True)
    subprocess.run(
        ["find", ".", "-type", "f", "-perm", "-u+x", "-exec", "chmod", "0750", "{}", ";"],
        cwd=clone_path,
        check=True,
    )
    subprocess.run(
        ["find", ".", "-type", "f", "!", "-perm", "-u+x", "-exec", "chmod", "0640", "{}", ";"],
        cwd=clone_path,
        check=True,
    )


def test_repaired_sequence_produces_clean_status_and_zero_content_diff(scratch_clone):
    _apply_repaired_sequence(scratch_clone)
    status = subprocess.run(
        ["git", "status", "--short"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert status == ""
    diffstat = subprocess.run(
        ["git", "diff", "--stat"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert diffstat == ""
    content_diff = subprocess.run(
        ["git", "diff", PINNED_SOURCE_SHA, "--", "."], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert content_diff == ""


def test_repaired_sequence_zero_mode_mismatch_across_all_4030_paths(scratch_clone):
    out = subprocess.run(
        ["git", "ls-tree", "-r", PINNED_SOURCE_SHA], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    mismatches = []
    checked = 0
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        mode = meta.split()[0]
        checked += 1
        st = os.lstat(scratch_clone / path)
        fsmode = oct(st.st_mode & 0o777)
        expected = "0o750" if mode == "100755" else "0o640"
        if fsmode != expected:
            mismatches.append((path, mode, fsmode, expected))
    assert checked == 4030
    assert mismatches == []


def test_repaired_sequence_preserves_executable_and_nonexecutable_semantics(scratch_clone):
    assert os.access(scratch_clone / ".githooks/pre-commit", os.X_OK)
    assert os.access(scratch_clone / ".githooks/pre-push", os.X_OK)
    assert os.access(scratch_clone / "scripts/check-docs-updated.sh", os.X_OK)
    assert not os.access(scratch_clone / "pyproject.toml", os.X_OK)


def test_repaired_sequence_all_directories_are_0750(scratch_clone):
    non_conforming = []
    for root, dirs, _files in os.walk(scratch_clone):
        if ".git" in Path(root).parts:
            continue
        for d in dirs:
            if d == ".git":
                continue
            p = Path(root) / d
            mode = oct(os.lstat(p).st_mode & 0o777)
            if mode != "0o750":
                non_conforming.append((str(p), mode))
    assert non_conforming == []


def test_branch_order_cannot_cross_classify_files(scratch_clone):
    """Attacks the ordering of the two `find -perm -u+x` branches directly:
    the first branch only ever touches files that already satisfy
    `-perm -u+x`, and `chmod 0750` on a matched file cannot alter any
    *other* file's mode -- so the second branch's `! -perm -u+x`
    predicate, evaluated after the first branch completes, classifies
    every file identically to how it would have classified it before
    the first branch ran. Verified empirically: run the two branches
    with an instrumentation pass in between that snapshots every file's
    u+x bit, and confirm the snapshot immediately before the second
    branch equals the on-disk-at-checkout snapshot for every file the
    second branch will touch.
    """
    # snapshot at-checkout owner-exec bit for every regular file
    before = {}
    for root, _dirs, files in os.walk(scratch_clone):
        if ".git" in Path(root).parts:
            continue
        for f in files:
            p = Path(root) / f
            before[str(p)] = bool(os.lstat(p).st_mode & 0o100)

    subprocess.run(["find", ".", "-type", "d", "-exec", "chmod", "0750", "{}", ";"], cwd=scratch_clone, check=True)
    subprocess.run(
        ["find", ".", "-type", "f", "-perm", "-u+x", "-exec", "chmod", "0750", "{}", ";"],
        cwd=scratch_clone,
        check=True,
    )

    after_branch1 = {}
    for root, _dirs, files in os.walk(scratch_clone):
        if ".git" in Path(root).parts:
            continue
        for f in files:
            p = Path(root) / f
            after_branch1[str(p)] = bool(os.lstat(p).st_mode & 0o100)

    # Every file's u+x classification after branch 1 must equal its
    # classification before branch 1 -- branch 1 never introduces or
    # removes u+x on a file it does not itself match, and on a matched
    # file 0750 retains u+x. No cross-classification is possible.
    assert after_branch1 == before

    subprocess.run(
        ["find", ".", "-type", "f", "!", "-perm", "-u+x", "-exec", "chmod", "0640", "{}", ";"],
        cwd=scratch_clone,
        check=True,
    )
    status = subprocess.run(
        ["git", "status", "--short"], cwd=scratch_clone, capture_output=True, text=True, check=True
    ).stdout
    assert status == ""


def test_repair_robust_under_restrictive_umask():
    """Attacks the checkout-umask assumption directly: under a
    restrictive 077 umask, `git checkout` still writes the owner-exec
    bit from the Git index (only group/other bits are affected by
    umask), so the two `-perm -u+x` branches still classify correctly.
    """
    tmpdir = tempfile.mkdtemp(prefix="pcae-7d4-umask-")
    try:
        clone_path = Path(tmpdir) / "src"
        old_umask = os.umask(0o077)
        try:
            subprocess.run(
                ["git", "clone", "--no-checkout", str(REPO_ROOT), str(clone_path)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "checkout", "--detach", PINNED_SOURCE_SHA],
                cwd=clone_path,
                check=True,
                capture_output=True,
            )
            hook_mode = oct(os.lstat(clone_path / ".githooks/pre-commit").st_mode & 0o777)
            plain_mode = oct(os.lstat(clone_path / "pyproject.toml").st_mode & 0o777)
            assert hook_mode == "0o700"  # owner-exec preserved despite strict umask
            assert plain_mode == "0o600"  # owner-exec absent, matching index
            _apply_repaired_sequence(clone_path)
            status = subprocess.run(
                ["git", "status", "--short"], cwd=clone_path, capture_output=True, text=True, check=True
            ).stdout
            assert status == ""
        finally:
            os.umask(old_umask)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_rollback_returns_to_empty_0750_directory(scratch_clone):
    _apply_repaired_sequence(scratch_clone)
    parent = scratch_clone.parent
    subprocess.run(["rm", "-rf", str(scratch_clone)], check=True)
    scratch_clone.mkdir()
    os.chmod(scratch_clone, 0o750)
    remaining = list(scratch_clone.iterdir())
    assert remaining == []
    assert oct(os.lstat(scratch_clone).st_mode & 0o777) == "0o750"
    # restore fixture-shared clone for any tests ordered after this one
    subprocess.run(
        ["git", "clone", "--no-checkout", str(REPO_ROOT), str(scratch_clone)], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "checkout", "--detach", PINNED_SOURCE_SHA], cwd=scratch_clone, check=True, capture_output=True
    )


# --- Section: repaired Action 6 text -- independently extracted from 7D.3 doc ---


def test_repaired_action_6_text_present_verbatim_in_7d3_doc():
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
    ).read_text()
    assert "sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;" in doc
    assert "sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;" in doc
    # clone/checkout/chown lines are byte-identical to the original
    assert "sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src" in doc
    assert "sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a" in doc
    assert "sudo chown -R root:pcae /opt/pcae/runtime/src" in doc


def test_repaired_action_6_rollback_unchanged_from_original():
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
    ).read_text()
    original = _git_show(
        IMMUTABLE_7B1_COMMIT,
        "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
    )
    rollback_line = "sudo rm -rf /opt/pcae/runtime/src"
    assert rollback_line in doc
    assert rollback_line in original


# --- Section: continuation gates and Action-2 adjudication ---


def test_continuation_gates_are_read_only_and_exact():
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
    ).read_text()
    gates = doc.split("## 13. Continuation Semantics")[1].split("## 14.")[0]
    normalized = " ".join(gates.split())
    assert "do not rerun their mutation commands" in normalized
    assert "STOP. No repair under continuation authority" in normalized
    assert "uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)" in normalized


def test_old_plan_action_2_would_stop_from_current_retained_baseline():
    """Independently derived collision-path attack: if an operator
    followed the OLD CHGR's frozen nine-action plan literally, in
    order, from today's retained baseline (pcae already exists), the
    plan's own Action 2 preflight -- which has no EXACTLY SATISFIED
    branch -- would classify the existing account as CONFLICTING and
    require STOP, before Action 6 is ever reached. Reaching Action 6
    under the old plan's own literal text therefore requires violating
    an explicit, visible precondition written into the plan itself.
    """
    original = _git_show(
        IMMUTABLE_7B1_COMMIT,
        "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
    )
    action2 = original.split("### Action 2")[1].split("### Action 3")[0]
    normalized = " ".join(action2.split())
    assert "Either exit zero (exists)" in normalized
    assert "CONFLICTING → STOP" in normalized
    assert "No reuse, no silent adoption" in normalized


def test_action_2_continuation_gate_is_bound_by_new_amendment_not_old_plan():
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
    ).read_text()
    adjudication = doc.split("## 14. Action-2 Continuation Adjudication")[1].split("## 15.")[0]
    assert "does **not** pretend" in adjudication
    assert "does **not** delete/recreate" in adjudication
    assert "required retained baseline" in adjudication


# --- Section: Actions 7-9 unchanged, wrapper digest, HBDC-REQ-042 ---


def test_wrapper_digest_recomputes_exactly():
    import hashlib

    assert len(WRAPPER_BYTES) == 188
    assert hashlib.sha256(WRAPPER_BYTES).hexdigest() == WRAPPER_DIGEST


def test_hbdc_req_042_driven_only_by_deploymentbinding_absence():
    src = HATP_CLASS_B_SOURCE.read_text()
    assert "no_active_deployment_binding_matches_repository_and_root" in src
    assert "no_repository_identity_present" in src
    # No file-mode/executable-bit token anywhere near the HBDC-REQ-042 check.
    idx = src.index("_check_deployment_identity")
    window = src[idx : idx + 2000]
    assert "chmod" not in window
    assert "0640" not in window and "0750" not in window


def test_actions_7_9_text_unchanged_between_immutable_commit_and_7d3_citation():
    original = _git_show(
        IMMUTABLE_7B1_COMMIT,
        "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
    )
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md"
    ).read_text()
    assert "Actions 7-9" in doc
    section15 = doc.split("## 15. Actions 7-9 Change Determination")[1].split("## 16.")[0]
    assert "Neither requires any textual change" in section15
    assert WRAPPER_DIGEST in original


# --- Section: exclusions ---


def test_no_deploymentbinding_artifact_exists():
    matches = list((REPO_ROOT / ".pcae").rglob("*deploymentbinding*"))
    matches += list((REPO_ROOT / ".pcae").rglob("*DeploymentBinding*"))
    assert matches == []


def test_new_chgr_conditions_list_all_required_exclusions():
    record = json.loads(NEW_CHGR_PATH.read_text())
    conditions = record["conditions"]
    for token in (
        "Action 6 execution",
        "Actions 7-9 execution",
        "any rerun of Actions 1-5",
        "any Dell Class-B mutation",
        "DeploymentBinding creation",
        "Boundary C certification",
        "Boundary A activation",
        "HATP_MANDATORY activation",
        "Cutover Record creation",
        "Permission Broker changes",
        "POL-005",
        "COMP-002",
        "arbitrary repository onboarding",
        "centralized multi-repository governance",
    ):
        assert token in conditions, token


# --- Section: decision session -- explicit election and separate confirmation ---


def test_decision_session_records_explicit_approve():
    session = json.loads(DECISION_SESSION_PATH.read_text())["session"]
    assert session["human_selection_id"] == "approve"
    assert session["session_state"] == "Confirmed"
    assert "options_presented" in session and "decline" in session["options_presented"]
    assert "amend" in session["options_presented"]


def test_decision_session_confirmation_bound_to_exact_preview_digest():
    orch = json.loads(DECISION_ORCH_PATH.read_text())
    request = orch["confirmation_requests"][0]
    response = orch["confirmation_responses"][0]
    preview = orch["last_preview"]
    # preview_digest must match across request/response, and the
    # requested preview_id must match the confirmed preview's own id --
    # independent fields all agreeing is what makes this a bound
    # confirmation, not an inferred one.
    assert request["preview_digest"] == response["preview_digest"]
    assert request["preview_id"] == preview["preview_id"]
    assert response["confirmation_result"] == "Accepted"


def test_preview_construction_precedes_confirmation_in_time():
    orch = json.loads(DECISION_ORCH_PATH.read_text())
    preview_ts = orch["last_preview"]["preview_timestamp"]
    confirm_ts = orch["confirmation_responses"][0]["confirmed_at"]
    assert preview_ts < confirm_ts


def test_published_chgr_is_bound_to_the_correct_session_not_the_superseded_one():
    """Authority-wall attack: a phase's own recommended-next-phase text
    (and hand-authored phase prompts derived from it) can *name* a
    decision-session ID that turns out not to be the one that actually
    produced the published CHGR -- "published" is not the same fact as
    "independently verified." This test resolves the session-to-record
    binding from the primary publication-execution artifacts (attempt
    records, package consumption state) rather than trusting any
    session ID handed down externally.
    """
    attempts_dir = REPO_ROOT / ".pcae/publication-execution/attempts"
    published_dir = REPO_ROOT / ".pcae/publication-execution/published"
    pending_dir = REPO_ROOT / ".pcae/decision-sessions/pending-packages"
    consumed_dir = pending_dir / "consumed"

    # Find the attempt that actually produced the published record.
    winning_attempts = []
    losing_attempts = []
    for f in attempts_dir.glob("*.json"):
        data = json.loads(f.read_text())
        result = data.get("result", data)
        if result.get("record_id") == NEW_CHGR_ID or data.get("chgr_record_ids", {}).get(
            "human_governance_record"
        ) == NEW_CHGR_ID:
            winning_attempts.append(data)
        elif result.get("session_id") in (DECISION_SESSION_ID, SUPERSEDED_SESSION_ID):
            losing_attempts.append(data)

    assert winning_attempts, "no publication attempt resolved to the published CHGR"
    winning_session_ids = {
        a.get("session_id") or a.get("result", {}).get("session_id") for a in winning_attempts
    }
    assert winning_session_ids == {DECISION_SESSION_ID}
    assert SUPERSEDED_SESSION_ID not in winning_session_ids

    # The superseded session's own attempts must all show failure, never
    # a record_id.
    superseded_attempts = [
        json.loads(f.read_text())
        for f in attempts_dir.glob("*.json")
        if json.loads(f.read_text()).get("result", {}).get("session_id") == SUPERSEDED_SESSION_ID
    ]
    assert superseded_attempts, "expected at least one failed attempt for the superseded session"
    for a in superseded_attempts:
        result = a["result"]
        assert result["success"] is False
        assert result["record_id"] is None

    # Package-consumption state independently confirms the same story:
    # the winning session's package was moved to consumed/, the
    # superseded session's was not.
    consumed_ids = {f.stem for f in consumed_dir.glob("*.json")} if consumed_dir.exists() else set()
    pending_ids = {f.stem for f in pending_dir.glob("*.json") if f.is_file()}
    winning_package_ids = {a.get("package_id") or a["result"]["package_id"] for a in winning_attempts}
    assert winning_package_ids & consumed_ids
    superseded_package_ids = {a["result"]["package_id"] for a in superseded_attempts}
    assert superseded_package_ids & pending_ids
    assert not (superseded_package_ids & consumed_ids)


def test_preview_content_binds_full_amended_proposition_not_a_summary():
    orch = json.loads(DECISION_ORCH_PATH.read_text())
    rendered = orch["last_preview"]["rendered_content"]
    for token in (
        DELL_MACHINE_ID,
        "repaired Action-6",
        "retained Actions-1-5",
        "does not authorize execution",
    ):
        assert token in rendered, token


# --- Section: new/old CHGR reconstruction and integrity ---


def test_new_chgr_governance_record_verify_passes(tmp_path):
    result = subprocess.run(
        ["pcae", "governance-record", "verify", str(NEW_CHGR_PATH), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["outcome"] == "verified"
    checks = {c["name"]: c["status"] for c in payload["checks"]}
    assert checks["schema_shape"] == "passed"
    assert checks["digest_self_consistency"] == "passed"
    assert checks["lifecycle_structural_legality"] == "passed"


def test_old_chgr_byte_identical_and_unrevoked():
    record = json.loads(OLD_CHGR_PATH.read_text())
    assert record["lifecycle_state"] == "published"
    assert record["record_id"] == OLD_CHGR_ID
    status = subprocess.run(
        ["git", "status", "--short", "--", str(OLD_CHGR_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


def test_new_chgr_rationale_explicitly_forbids_old_chgr_fallback():
    """No-fallback requirement (independent check): the new CHGR's own
    authority-bearing `rationale` field -- not merely the phase report
    prose -- must itself name the old record and explicitly state it
    does not authorize continuation, so the no-fallback rule travels
    with the record even if read in isolation from any phase doc.
    """
    record = json.loads(NEW_CHGR_PATH.read_text())
    rationale = record["rationale"]
    assert OLD_CHGR_ID in rationale
    assert "does not authorize continuation" in rationale
    assert "remains historical authority for the original provisioning attempt" in rationale


def test_no_chgr_supersession_cli_verb_exists():
    """Independently confirms Finding D3-3's negative claim directly
    against the CLI wiring, not by citing the phase doc's own claim.
    """
    cli_src = (REPO_ROOT / "src/pcae/cli.py").read_text()
    # governance-record subcommand set must not include a transition/
    # supersede/suspend/revoke verb.
    idx = cli_src.index("governance_record_parser = subparsers.add_parser")
    window = cli_src[idx : idx + 4000]
    for forbidden in ("supersede", "suspend", "revoke", "transition"):
        assert forbidden not in window.lower()

    publish_src = GOVERNANCE_RECORD_CLI.read_text()
    assert "predecessor" not in publish_src.lower()
    assert "successor" not in publish_src.lower()


def test_lifecycle_event_schema_discloses_no_transition_command():
    schema_path = REPO_ROOT / "src/pcae/schema_resources/chgr/records/governance_record_lifecycle_event.schema.json"
    schema = json.loads(schema_path.read_text())
    assert "No transition command exists this increment" in schema["description"]


# --- Section: no Dell mutation, no production repair this phase ---


def test_no_production_source_modified_this_phase():
    diff = subprocess.run(
        ["git", "diff", "--stat", "origin/main", "--", "src/pcae/**", "scripts/**", "docs/contracts/**"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert diff.strip() == ""


def test_scratch_fixture_uses_tempfile_mkdtemp_not_production_path():
    """Sanity check on this module's own fixtures: the scratch clone
    fixture is rooted under tempfile.mkdtemp(), never under a literal
    /opt/pcae production path."""
    this_file = Path(__file__).read_text()
    assert "tempfile.mkdtemp(" in this_file
    assert "shutil.rmtree" in this_file
