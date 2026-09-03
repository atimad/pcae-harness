"""Fresh verification for the .30R.5R.2.1R F-3 evidence repair.

This suite is hardware-free. It verifies historical Git evidence and does not
perform or substitute for the final real-human N-16-5 ceremony.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
A = E = "0250e5f79340b659f4c34ce391656d8f7219ccc3"
REPAIR_IMPLEMENTATION = "a85abff66b5a07f9d83b873d625aea7b1c65b19d"
I = "361114d648dea432aa3ef92ecd7e24e748a173aa"
V = R0 = "57edf6a93f8b4f01ee95d4b74ceddcaea96f53b3"
PREDECESSOR = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py"
BLOCKED_IV = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1_protected_presentation_human_election_iv_and_n16_5_certification.py"
BLOCKED_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1_PROTECTED_PRESENTATION_HUMAN_ELECTION_IV_AND_N_16_5_CERTIFICATION.md"
HELPER = "src/pcae/protected_presentation_helper.py"
LAUNCHER = "src/pcae/core/protected_presentation.py"
CTAP2 = "src/pcae/core/hpac_rhamp_ctap2.py"

CONTRACTS = (
    "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",
    "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
    "docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md",
)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=check)


def _git(*args: str) -> str:
    return _run("git", *args).stdout


def _test_functions(source: str) -> set[str]:
    return {
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def _test_01_body(source: str) -> str:
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "test_01_phase_entry_and_historical_heads_are_primary_git_objects"
    )
    return ast.get_source_segment(source, node) or ""


@pytest.mark.parametrize("sha", [A, E, REPAIR_IMPLEMENTATION, I, V, R0])
def test_01_fixed_lineage_objects_resolve(sha):
    assert _git("rev-parse", sha).strip() == sha


def test_02_phase_entry_is_implementation_parent():
    assert _git("rev-parse", f"{REPAIR_IMPLEMENTATION}^").strip() == E


def test_03_implementation_contains_phase_task_and_repair():
    names = _git("show", "--format=", "--name-only", REPAIR_IMPLEMENTATION)
    assert "30r-5r-2-n-16-5-protected-presentation" in names
    assert HELPER in names and LAUNCHER in names


def test_04_no_separate_phase_open_commit_was_assumed():
    assert _git("rev-list", "--count", f"{E}..{REPAIR_IMPLEMENTATION}").strip() == "1"


def test_05_blocked_iv_history_is_preserved():
    text = _git("show", f"{V}:{BLOCKED_DOC}")
    assert "Verdict: BLOCKED" in text and "N-16-5: NOT CLOSED" in text


def test_06_original_f3_logic_is_reproduced_from_r0_blob():
    old = _git("show", f"{R0}:{PREDECESSOR.relative_to(REPO)}")
    assert '_git("rev-parse", "HEAD").strip().startswith(ENTRY)' in old
    assert not _git("rev-parse", "HEAD").strip().startswith(A[:8])


def test_07_original_semantic_invariant_is_phase_entry_parentage():
    assert _git("rev-parse", f"{REPAIR_IMPLEMENTATION}^").strip() == A
    assert "1R.30R.5R.1" in _git("log", "-1", "--format=%s", A)
    assert "1R.30R.5R.2" in _git("log", "-1", "--format=%s", REPAIR_IMPLEMENTATION)


def test_08_repaired_assertion_uses_immutable_git_topology():
    body = _test_01_body(PREDECESSOR.read_text())
    assert 'f"{REPAIR_IMPLEMENTATION}^"' in body
    assert "== ENTRY" in body


def test_09_live_head_is_not_historical_entry_authority():
    body = _test_01_body(PREDECESSOR.read_text())
    assert '"HEAD"' not in body and "startswith(ENTRY)" not in body


def test_10_live_completion_metadata_is_not_historical_authority():
    body = _test_01_body(PREDECESSOR.read_text())
    assert "phase-completion-metadata" not in body and "PROJECT_STATUS" not in body


def test_11_current_successor_is_descended_without_being_entry():
    current = _git("rev-parse", "HEAD").strip()
    assert current != E
    assert _run("git", "merge-base", "--is-ancestor", REPAIR_IMPLEMENTATION, current).returncode == 0


def test_12_future_successors_cannot_change_fixed_parentage():
    descendants = _git("rev-list", "--ancestry-path", f"{REPAIR_IMPLEMENTATION}..HEAD").splitlines()
    assert descendants
    for _descendant in descendants:
        assert _git("rev-parse", f"{REPAIR_IMPLEMENTATION}^").strip() == E


def test_13_no_broad_future_commit_allowance():
    body = _test_01_body(PREDECESSOR.read_text())
    assert "merge-base" not in body and "ancestor" not in body and "..HEAD" not in body


def test_14_exact_repair_diff_is_narrow():
    diff = _git("diff", "--unified=0", R0, "--", str(PREDECESSOR.relative_to(REPO)))
    assert 'REPAIR_IMPLEMENTATION = "a85abff66b5a07f9d83b873d625aea7b1c65b19d"' in diff
    assert 'f"{REPAIR_IMPLEMENTATION}^"' in diff
    assert sum(line.startswith("@@") for line in diff.splitlines()) == 2


def test_15_predecessor_scope_assertions_remain_present():
    source = PREDECESSOR.read_text()
    assert "test_04_no_normative_contract_changed" in source
    assert "test_05_production_diff_is_exactly_the_two_authorized_files" in source


@pytest.mark.parametrize("rel", [HELPER, LAUNCHER, CTAP2])
def test_16_h1_h2_f2_production_bytes_unchanged(rel):
    assert _run("git", "diff", "--quiet", I, "--", rel).returncode == 0


def test_17_no_production_or_dependency_change():
    assert not _git("diff", "--name-only", R0, "--", "src/pcae", "scripts", "pyproject.toml").strip()


@pytest.mark.parametrize("rel", CONTRACTS)
def test_18_contract_bytes_unchanged(rel):
    assert _run("git", "diff", "--quiet", R0, "--", rel).returncode == 0


def test_19_no_test_definition_removed_or_renamed():
    old = _git("show", f"{R0}:{PREDECESSOR.relative_to(REPO)}")
    assert _test_functions(old) == _test_functions(PREDECESSOR.read_text())


@pytest.mark.parametrize("token", ["pytest.skip", "pytest.mark.skip", "pytest.mark.skipif", "pytest.mark.xfail"])
def test_20_no_skip_or_xfail_added(token):
    old = _git("show", f"{R0}:{PREDECESSOR.relative_to(REPO)}")
    assert PREDECESSOR.read_text().count(token) == old.count(token)


def test_21_no_wildcard_or_fnmatch_broadening():
    old = _git("show", f"{R0}:{PREDECESSOR.relative_to(REPO)}")
    new = PREDECESSOR.read_text()
    assert new.count("fnmatch") == old.count("fnmatch")
    assert new.count('"*"') == old.count('"*"')


def test_22_predecessor_suite_is_green():
    result = _run("python", "-m", "pytest", "-q", str(PREDECESSOR))
    assert "71 passed" in result.stdout


def test_23_blocked_iv_suite_remains_software_green_and_unchanged():
    assert _run("git", "diff", "--quiet", R0, "--", str(BLOCKED_IV.relative_to(REPO))).returncode == 0
    result = _run("python", "-m", "pytest", "-q", str(BLOCKED_IV), check=False)
    assert result.returncode == 1
    assert "84 passed" in result.stdout and "1 failed" in result.stdout
    assert "test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3" in result.stdout


def test_24_historical_reports_are_not_modified():
    assert not _git("diff", "--name-only", R0, "--", "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1_PROTECTED_PRESENTATION_HUMAN_ELECTION_IV_AND_N_16_5_CERTIFICATION.md").strip()


def test_25_no_real_ceremony_was_performed():
    record = json.loads((REPO / ".pcae/certification/n16_5_presentation_bound_cert_30r5r2_1.json").read_text())
    assert record["real_ceremony"]["started"] is False
    assert record["real_ceremony"]["explicit_approve_occurred"] is False
    assert record["n16_5"] == "NOT_CLOSED"


def test_26_supported_profiles_remain_nonexclusive_and_mobile_open():
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "supported-not-exclusive" in status.lower()
    assert "mobile-only" in status.lower() and "remain" in status.lower()


def test_27_runtime_and_first_effect_remain_unavailable():
    out = _run("pcae", "runtime", "inspect").stdout
    for value in ("not_implemented", "Observed", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out
    assert "adapter.dispatch(" not in _git("diff", R0, "--", "src/pcae")


def test_28_n16_6_and_n16_7_are_untouched():
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "N-16-6/N-16-7 untouched" in status
    assert not _git("diff", "--name-only", R0, "--", "src/pcae", "docs/contracts").strip()


def test_29_delegated_finalization_incident_is_preserved():
    assert "DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in (REPO / "tasks/DECISIONS.md").read_text()
