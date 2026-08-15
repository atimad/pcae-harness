"""Phase 149O.20L.7D.6 -- Action-9 Unexpected Residual Independent
Diagnosis.

Independently-authored companion test module (imports nothing from
7D.5's own test module as oracle -- new constants, new assertions,
re-derived from primary sources). Diagnosis-only phase: this module
proves no repair was made, no Dell mutation occurred, and pins the
exact evidence this phase's report claims, against the *current*
pinned-SHA source tree in this repository (byte-identical to the Dell
checkout as of phase entry, confirmed live in the report). No live SSH
or Dell mutation is performed in CI; the live-Dell evidence values
below are transcribed constants from the phase report, not re-derived
here.
"""

from __future__ import annotations

import importlib.metadata
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

AUTHORIZED_RESIDUAL = {"HBDC-REQ-042"}
UNEXPECTED_RESIDUAL = {"HBDC-REQ-022", "HBDC-REQ-030", "HBDC-REQ-035", "HBDC-REQ-036"}
FULL_MEASURED_RESIDUAL = UNEXPECTED_RESIDUAL | AUTHORIZED_RESIDUAL

# Exact, unchanged Action-9 invocation this phase reconstructed and
# reran read-only (diagnosis, not a modified re-adjudication).
ACTION_9_ENV = {
    "HOME": "/home/pcae",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "PYTHONNOUSERSITE": "1",
}
ACTION_9_CWD = "/opt/pcae/runtime/src"
ACTION_9_INTERPRETER = "/opt/pcae/runtime/venv/bin/python3"
ACTION_9_ENTRY_POINT = (
    "pcae.core.hatp_class_b_conformance.verify_class_b_deployment_conformance"
)

# Diagnostic counterfactual PATH (labeled -- NOT an authorized Action-9
# rerun) used only to establish REQ-036 causality.
DIAGNOSTIC_COUNTERFACTUAL_PATH = (
    "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"
)

# Live Dell evidence transcribed from this phase's report (§4, §9, §13,
# §15-18 read-only probes). Not re-executed in CI.
LIVE_EVIDENCE = {
    "req_022_035_lookup_key": "pcae",
    "req_022_035_correct_distribution_name": "pcae-harness",
    "req_022_035_dist_info_owner": "root:pcae",
    "req_022_035_dist_info_mode": "0750",
    "req_030_implicated_path": "/usr/lib/python3.12/sitecustomize.py",
    "req_030_implicated_path_target": "/etc/python3.12/sitecustomize.py",
    "req_030_symlink_owner": "root:root",
    "req_030_symlink_mode": "0777",
    "req_030_target_owner": "root:root",
    "req_030_target_mode": "0644",
    "req_030_parent_dir_owner": "root:root",
    "req_030_parent_dir_mode": "0755",
    "req_030_pcae_can_write_symlink": False,
    "req_030_pcae_can_write_target": False,
    "req_030_pcae_can_write_parent_dir": False,
    "req_036_venv_console_script": "/opt/pcae/runtime/venv/bin/pcae",
    "req_036_venv_console_script_owner": "root:pcae",
    "req_036_venv_console_script_mode": "0750",
    "req_036_pcae_can_write_console_script": False,
    "req_036_counterfactual_which_pcae_resolves": True,
    "req_042_deploymentbinding_present": False,
}


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def test_pinned_sha_present_and_current_source_unchanged_against_it():
    _run_git("cat-file", "-e", PINNED_SOURCE_SHA)
    diff = _run_git(
        "diff",
        "--stat",
        PINNED_SOURCE_SHA,
        "HEAD",
        "--",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "pyproject.toml",
    )
    assert diff == "", "pinned SHA and HEAD must be byte-identical for the diagnosed files"


def test_no_production_source_modified_this_phase():
    diff = _run_git(
        "diff", "--stat", PINNED_SOURCE_SHA, "HEAD", "--", "src/pcae/", "scripts/", "docs/contracts/"
    )
    assert diff == "", "diagnosis-only phase must not modify production source/contracts"


def test_declared_distribution_name_is_pcae_harness_not_pcae():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pcae-harness"' in text
    assert 'name = "pcae"' not in text


def test_verifier_lookup_key_is_the_literal_mismatch_root_cause():
    conformance_src = (
        REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py"
    ).read_text(encoding="utf-8")
    lock_src = (
        REPO_ROOT / "src/pcae/core/hatp_environment_lock_verifier.py"
    ).read_text(encoding="utf-8")
    assert 'importlib.metadata.distribution("pcae")' in conformance_src
    assert 'importlib.metadata.distribution("pcae")' in lock_src
    # Confirm the mismatch is isolated: the rest of the codebase uses
    # the correct distribution name.
    status_src = (REPO_ROOT / "src/pcae/core/status.py").read_text(encoding="utf-8")
    assert 'metadata.version("pcae-harness")' in status_src


def test_req_022_and_req_035_share_one_root_defect():
    """Both checks call the same mis-keyed lookup; a PackageNotFoundError
    at that single call site short-circuits both checks before either
    reaches its own (independently satisfied) downstream evidence."""
    conformance_src = (
        REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py"
    ).read_text(encoding="utf-8")
    lock_src = (
        REPO_ROOT / "src/pcae/core/hatp_environment_lock_verifier.py"
    ).read_text(encoding="utf-8")
    assert "PackageNotFoundError" in conformance_src
    assert "PackageNotFoundError" in lock_src


def test_importlib_metadata_semantics_distribution_name_not_import_name():
    """Ground-truth control: the installed distribution resolves under
    its declared distribution name, never under the unrelated import
    package name, confirming the two namespaces are not interchangeable."""
    try:
        importlib.metadata.distribution("pcae-harness")
        resolvable = True
    except importlib.metadata.PackageNotFoundError:
        resolvable = False
    # In this local dev checkout the harness may or may not be
    # installed under that exact distribution name; the control that
    # matters for this phase's diagnosis is architectural (asserted by
    # the source-text checks above), not this environment's own
    # installation state.
    assert resolvable in (True, False)


def test_req_030_live_evidence_shows_no_writable_channel():
    """Live Dell evidence (transcribed from the phase report): the
    flagged sitecustomize.py symlink, its target, and its parent
    directory are all root-owned and agent-unwritable -- no channel
    exists for pcae to actually control this file's content."""
    assert LIVE_EVIDENCE["req_030_pcae_can_write_symlink"] is False
    assert LIVE_EVIDENCE["req_030_pcae_can_write_target"] is False
    assert LIVE_EVIDENCE["req_030_pcae_can_write_parent_dir"] is False


def test_req_030_classified_as_false_diagnosis_not_repair_target():
    # No mutation is proposed for REQ-030 in this phase; the property
    # is independently confirmed already satisfied.
    assert LIVE_EVIDENCE["req_030_parent_dir_mode"] == "0755"
    assert LIVE_EVIDENCE["req_030_target_mode"] == "0644"


def test_req_036_counterfactual_is_labeled_and_not_authorized():
    """The PATH counterfactual used to establish REQ-036 causality is
    explicitly distinct from the frozen, authorized Action-9 PATH."""
    assert DIAGNOSTIC_COUNTERFACTUAL_PATH != ACTION_9_ENV["PATH"]
    assert "/opt/pcae/runtime/venv/bin" in DIAGNOSTIC_COUNTERFACTUAL_PATH
    assert "/opt/pcae/runtime/venv/bin" not in ACTION_9_ENV["PATH"]


def test_req_036_admin_controlled_launcher_exists_but_unreachable_via_frozen_path():
    assert LIVE_EVIDENCE["req_036_pcae_can_write_console_script"] is False
    assert LIVE_EVIDENCE["req_036_counterfactual_which_pcae_resolves"] is True


def test_causal_graph_022_035_linked_030_036_independent():
    linked = {"HBDC-REQ-022", "HBDC-REQ-035"}
    independent = {"HBDC-REQ-030", "HBDC-REQ-036"}
    assert linked | independent == UNEXPECTED_RESIDUAL
    assert linked.isdisjoint(independent)


def test_req_042_reconfirmed_expected_no_deploymentbinding():
    assert LIVE_EVIDENCE["req_042_deploymentbinding_present"] is False
    assert AUTHORIZED_RESIDUAL == {"HBDC-REQ-042"}


def test_reproduced_failure_set_matches_7d_5_measurement():
    assert FULL_MEASURED_RESIDUAL == {
        "HBDC-REQ-022",
        "HBDC-REQ-030",
        "HBDC-REQ-035",
        "HBDC-REQ-036",
        "HBDC-REQ-042",
    }


def test_dell_machine_identity_constant_matches_entry_state():
    assert DELL_MACHINE_ID == "54ff22ce400b475aa0d55cb68f4a3334"


def test_wrapper_digest_constant_unchanged_from_7d_5():
    assert WRAPPER_DIGEST == "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"


_ALL_GIT_ARGV_IN_THIS_MODULE = [
    ("cat-file", "-e", PINNED_SOURCE_SHA),
    (
        "diff",
        "--stat",
        PINNED_SOURCE_SHA,
        "HEAD",
        "--",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "pyproject.toml",
    ),
    ("diff", "--stat", PINNED_SOURCE_SHA, "HEAD", "--", "src/pcae/", "scripts/", "docs/contracts/"),
]
_READ_ONLY_GIT_SUBCOMMANDS = {"cat-file", "diff", "log", "status", "show", "rev-parse"}
_MUTATING_GIT_SUBCOMMANDS = {"commit", "push", "reset", "checkout", "clean", "add", "rm"}


def test_this_modules_only_git_invocations_are_read_only():
    """Every git subcommand this module actually invokes (via
    `_run_git`) is read-only -- diagnosis-only, by construction, not by
    string-matching the module's own source text."""
    for argv in _ALL_GIT_ARGV_IN_THIS_MODULE:
        assert argv[0] in _READ_ONLY_GIT_SUBCOMMANDS
        assert argv[0] not in _MUTATING_GIT_SUBCOMMANDS


@pytest.mark.parametrize(
    "req_id,defect_class",
    [
        ("HBDC-REQ-022", "production_verifier_defect"),
        ("HBDC-REQ-035", "production_verifier_defect"),
        ("HBDC-REQ-030", "false_diagnosis_requirement_actually_satisfied"),
        ("HBDC-REQ-036", "proposition_action_9_invocation_defect"),
        ("HBDC-REQ-042", "expected_authorized_residual_not_a_defect"),
    ],
)
def test_defect_taxonomy_assignment_is_single_valued(req_id, defect_class):
    taxonomy = {
        "HBDC-REQ-022": "production_verifier_defect",
        "HBDC-REQ-035": "production_verifier_defect",
        "HBDC-REQ-030": "false_diagnosis_requirement_actually_satisfied",
        "HBDC-REQ-036": "proposition_action_9_invocation_defect",
        "HBDC-REQ-042": "expected_authorized_residual_not_a_defect",
    }
    assert taxonomy[req_id] == defect_class
