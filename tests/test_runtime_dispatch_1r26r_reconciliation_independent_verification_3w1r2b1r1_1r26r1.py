"""Independent verification for Phase 149O...1R.26R.1.

This suite re-derives the reconciliation from immutable Git objects and the
live guards.  It intentionally does not import or reuse the repair phase's
test helpers.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import subprocess
import tempfile
import types
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
A = "28b8b2b7"
I = "99d85106"  # .1R.26 production implementation, before guard reconciliation
B = "9d28f7ef"
C = "ba4d21c3"  # finalized historical .1R.27 BLOCKED head
R = "e52d2f8e"
V = R

FIRST_FILE = "tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py"
FIRST_NODE = f"{FIRST_FILE}::test_runtime_posture_unchanged_and_no_new_first_effect_call_site"
SECOND_FILE = "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py"
SECOND_NODE = f"{SECOND_FILE}::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set"
R27_SUITE = "tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py"

R26_DOC = (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26_N_16_4_REAL_POSITIVE_"
    "SINGLE_ATTEMPT_RUNTIME_ENFORCEMENT_GATE_IMPLEMENTATION.md"
)
R26R_DOC = (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_"
    "VERIFICATION_EVIDENCE_RECONCILIATION.md"
)
REPRC = "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"


def _git(*args: str, cwd: Path = ROOT, check: bool = True) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=check
    ).stdout


def _run_pytest(cwd: Path, *nodes: str, junit: Path | None = None):
    cmd = [
        "python3", "-m", "pytest", "-q", "-o", "addopts=", "-p", "no:randomly",
        "--no-header",
    ]
    if junit is not None:
        cmd.append(f"--junitxml={junit}")
    cmd.extend(nodes)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


@contextmanager
def _worktree(sha: str):
    with tempfile.TemporaryDirectory(prefix="pcae-1r26r1-") as d:
        wt = Path(d) / "wt"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(wt), sha],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        try:
            yield wt
        finally:
            subprocess.run(
                ["git", "worktree", "remove", str(wt), "--force"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )


def _load_test_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _failed_nodes(xml_path: Path) -> set[str]:
    root = ET.parse(xml_path).getroot()
    result = set()
    for case in root.iter("testcase"):
        if case.find("failure") is None and case.find("error") is None:
            continue
        rel = case.attrib.get("file")
        if rel is None:
            rel = case.attrib["classname"].replace(".", "/") + ".py"
        result.add(f"{rel}::{case.attrib['name']}")
    return result


# Forty nodes repaired by .1R.26 plus the independently discovered missed
# .1R.22 node.  This set is executed at A and at I below; it is not accepted
# from report prose.
IMPLEMENTATION_TRIGGERED_NODES = {
    "tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py::test_gate5_through_gate9_byte_unchanged",
    "tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py::test_no_contract_file_changed",
    "tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py::test_no_normative_contract_changed_since_baseline",
    "tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py::test_slice_a_and_closed_gate_modules_are_byte_unchanged_since_baseline",
    "tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py::test_slice_b_production_scope_since_baseline_is_exactly_the_authorized_set",
    "tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py::test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap",
    "tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py::test_no_contract_change_since_r20_head",
    "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py::test_earlier_gates_and_contracts_bytes_unchanged_since_baseline",
    "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py::test_production_scope_since_baseline_is_the_single_new_file",
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_file_byte_unchanged_since_phase_entry_baseline[src/pcae/core/runtime_dispatch_gate7.py]",
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_no_unpushed_divergence_at_verification_entry",
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_production_scope_since_baseline_is_exactly_one_new_file",
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_widened_guard_module_passes_at_head[test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2]",
    "tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py::test_gate_5_perm_7_8_are_byte_unchanged_since_r153_baseline",
    "tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py::test_gate_5_to_9_and_neighbour_modules_byte_identical_since_baseline",
    "tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py::test_no_normative_contract_changed_since_baseline",
    "tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py::test_no_production_source_changed_since_the_r17_head_except_authorized_slice_b",
    "tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py::test_production_scope_since_baseline_is_the_one_r17_file_plus_authorized_slice_b",
    "tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_gate5_permission_gate7_gate8_still_byte_unchanged_since_r153",
    "tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_no_contract_file_changed_since_baseline",
    "tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_no_production_source_changed_since_baseline_except_the_one_r17_file",
    "tests/test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py::test_earlier_gate_modules_unchanged[runtime_dispatch_gate7.py]",
    "tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py::test_29_meta_guard_inventory_independently_discovered_and_run",
    "tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py::test_38_n23_2_contract_wording_left_untouched_since_r23_head",
    "tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py::test_39_no_production_or_contract_diff_since_r22r1_entry",
    "tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py::test_3_production_scope_since_baseline_is_exactly_the_two_authorized_files",
    "tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py::test_first_external_effect_absent",
    "tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py::test_n23_2_deferred_no_contract_change_by_this_phase",
    "tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py::test_no_normative_contract_diff_since_baseline_beyond_the_authorized_set",
    "tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py::test_no_production_source_diff_by_this_phase",
    "tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py::test_production_scope_since_baseline_is_exactly_the_two_authorized_files",
    "tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py::test_gate7_and_gate9_and_gate10_modules_byte_unchanged",
    "tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py::test_only_authorized_contract_files_changed_since_baseline",
    "tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py::test_only_two_production_files_changed_since_baseline",
    "tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py::test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline",
    "tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py::test_no_unplanned_contract_file_changed_since_task_open",
    FIRST_NODE,
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py::test_n20_4_lifecycle_diff_since_r20_head_is_only_the_remap",
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py::test_no_normative_contract_change_since_baseline",
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py::test_no_slice_a_gate_or_item9_drift_since_r19_head[src/pcae/core/runtime_dispatch_gate7.py]",
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py::test_production_diff_since_r19_head_is_exactly_the_n20_4_remap",
}


def test_01_sha_chain_is_reconstructed_from_git():
    assert _git("rev-parse", A).strip().startswith(A)
    assert _git("rev-parse", B).strip().startswith(B)
    assert _git("rev-parse", C).strip().startswith(C)
    assert _git("rev-parse", R).strip().startswith(R)
    assert _git("merge-base", A, B).strip().startswith(A)
    assert _git("merge-base", B, C).strip().startswith(B)
    assert _git("merge-base", C, R).strip().startswith(C)
    assert _git("rev-parse", "HEAD").strip().startswith(V)


def test_02_actual_repair_commit_parent_is_the_finalized_blocked_head():
    # Precision fact: B is the semantic comparison base, while the repair
    # commit's real Git parent is C after .1R.27 governed finalization.
    assert _git("rev-parse", "8b762a35^").strip().startswith(C)


def test_03_first_node_pass_a_fail_b_pass_r():
    with _worktree(A) as wt:
        assert _run_pytest(wt, FIRST_NODE).returncode == 0
    with _worktree(B) as wt:
        assert _run_pytest(wt, FIRST_NODE).returncode != 0
    assert _run_pytest(ROOT, FIRST_NODE).returncode == 0


def test_04_first_historical_failure_is_exactly_gate7_file_addition():
    changed = set(_git("diff", "--name-only", "8603fe6a", B, "--", "src/pcae").split())
    assert changed == {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
    }


def test_05_first_guard_is_literal_exact_equality():
    tree = ast.parse((ROOT / FIRST_FILE).read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == FIRST_NODE.rsplit("::", 1)[1])
    comparisons = [n for n in ast.walk(fn) if isinstance(n, ast.Compare)]
    exact = [n for n in comparisons if isinstance(n.left, ast.Name) and n.left.id == "changed"]
    assert len(exact) == 1
    assert len(exact[0].ops) == 1 and isinstance(exact[0].ops[0], ast.Eq)
    assert isinstance(exact[0].comparators[0], ast.Set)


@pytest.mark.parametrize("mode", ["extra", "missing", "substitute"])
def test_06_first_guard_rejects_adversarial_source_sets(monkeypatch, mode):
    module = _load_test_module(FIRST_FILE, f"r26r1_first_{mode}")
    authorized = {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
    }
    if mode == "extra":
        candidate = authorized | {"src/pcae/core/runtime_dispatch_fake_effect.py"}
    elif mode == "missing":
        candidate = authorized - {"src/pcae/core/runtime_dispatch_gate7.py"}
    else:
        candidate = (authorized - {"src/pcae/core/runtime_dispatch_gate7.py"}) | {
            "src/pcae/core/runtime_dispatch_gate8.py"
        }

    def fake_run(args, **kwargs):
        output = "\n".join(sorted(candidate)) + "\n" if "--name-only" in args else ""
        return types.SimpleNamespace(stdout=output)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    with pytest.raises(AssertionError):
        module.test_runtime_posture_unchanged_and_no_new_first_effect_call_site()


def test_07_first_guard_retains_posture_and_first_effect_assertions():
    source = (ROOT / FIRST_FILE).read_text()
    start = source.index("def test_runtime_posture_unchanged_and_no_new_first_effect_call_site")
    body = source[start:start + 2600]
    assert '("Observed", "observe", "unavailable")' in body
    assert 'not any("adapter.dispatch("' in body
    assert 'runtime_dispatch_gate10.py' in body


def test_08_second_node_pass_b_fail_c_pass_r():
    with _worktree(B) as wt:
        assert _run_pytest(wt, SECOND_NODE).returncode == 0
    with _worktree(C) as wt:
        assert _run_pytest(wt, SECOND_NODE).returncode != 0
    assert _run_pytest(ROOT, SECOND_NODE).returncode == 0


def test_09_second_guard_uses_real_import_detection_and_finite_literals():
    source = (ROOT / SECOND_FILE).read_text()
    tree = ast.parse(source)
    assignment = next(
        n for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "AUTHORIZED_GATE7_TEST_IMPORTERS" for t in n.targets)
    )
    assert isinstance(assignment.value, ast.Set)
    entries = {e.value for e in assignment.value.elts if isinstance(e, ast.Constant)}
    assert len(entries) == 10 and R27_SUITE in entries
    assert all(p.startswith("tests/") and p.endswith(".py") for p in entries)
    assert all(not (set(p) & set("*?[]")) for p in entries)
    assert "git\", \"grep" in source
    assert "unexpected = hits - known" in source and "missing = known - hits" in source


@pytest.mark.parametrize("mode", ["extra", "missing"])
def test_10_second_guard_rejects_adversarial_importer_sets(monkeypatch, mode):
    module = _load_test_module(SECOND_FILE, f"r26r1_second_{mode}")
    self_rel = SECOND_FILE
    candidate = set(module.AUTHORIZED_GATE7_TEST_IMPORTERS) - {self_rel}
    if mode == "extra":
        candidate.add("tests/test_synthetic_unauthorized_gate7_importer.py")
    else:
        candidate.remove(sorted(candidate)[0])
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(stdout="\n".join(sorted(candidate)) + "\n"),
    )
    with pytest.raises(AssertionError):
        module.test_53_test_importers_of_gate7_symbols_are_a_known_finite_set()


def test_11_pre_reconciliation_run_derives_exact_41_node_set():
    assert len(IMPLEMENTATION_TRIGGERED_NODES) == 41
    with tempfile.TemporaryDirectory(prefix="pcae-1r26r1-junit-") as d:
        xml_a = Path(d) / "a.xml"
        xml_i = Path(d) / "i.xml"
        nodes = sorted(IMPLEMENTATION_TRIGGERED_NODES)
        with _worktree(A) as wt:
            baseline = _run_pytest(wt, *nodes, junit=xml_a)
        with _worktree(I) as wt:
            candidate = _run_pytest(wt, *nodes, junit=xml_i)
        assert baseline.returncode == 0, baseline.stdout[-4000:]
        assert candidate.returncode != 0
        assert _failed_nodes(xml_i) == IMPLEMENTATION_TRIGGERED_NODES


def test_12_true_attributable_set_is_exactly_42_one_to_one():
    attributable = IMPLEMENTATION_TRIGGERED_NODES | {SECOND_NODE}
    assert len(attributable) == 42
    assert FIRST_NODE in attributable and SECOND_NODE in attributable
    assert len(IMPLEMENTATION_TRIGGERED_NODES - {FIRST_NODE}) == 40


def test_13_broad_exact_scope_inventory_is_rederived_not_two_node_selected():
    found = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.List, ast.Tuple, ast.Call)):
                continue
            values = [
                n.value for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            ]
            if "diff" in values and "--name-only" in values and "src/pcae" in " ".join(values):
                if subprocess.run(
                    ["git", "cat-file", "-e", f"{A}:{path.relative_to(ROOT)}"],
                    cwd=ROOT, capture_output=True,
                ).returncode == 0:
                    found.add(path.relative_to(ROOT).as_posix())
                break
    assert len(found) >= 69
    assert FIRST_FILE in found


def test_14_original_r26_report_is_byte_prefix_preserved():
    original = subprocess.run(
        ["git", "show", f"{B}:{R26_DOC}"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    current = (ROOT / R26_DOC).read_bytes()
    assert current.startswith(original)
    assert hashlib.sha256(current[:len(original)]).digest() == hashlib.sha256(original).digest()


def test_15_erratum_count_and_chronology_are_truthful():
    text = (ROOT / R26_DOC).read_text()
    erratum = text[text.index("## 21. Erratum"):]
    for token in ("40", "true count is", "42", "`.1R.27` discovery", "Corrected historical count", "Repair"):
        assert token in erratum
    assert erratum.index("`.1R.27` discovery") < erratum.index("Corrected historical count") < erratum.index("**Repair.**")


def test_16_r27_blocked_record_and_suite_git_ownership_are_preserved():
    report = _git("show", f"{C}:.pcae/phase-completion-report.md")
    metadata = _git("show", f"{C}:.pcae/phase-completion-metadata.json")
    assert "(BLOCKED)" in report and "**Status:** BLOCKED" in report
    assert '"status": "blocked"' in metadata
    subject = _git("log", "-1", "--format=%s", "--", R27_SUITE).strip()
    assert subject.startswith("Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.27:")
    assert _git("diff", "--name-only", C, R, "--", R27_SUITE).strip() == ""


def test_17_unrelated_gate6_guard_predates_r26_and_dependency_is_fail_closed():
    first = _git(
        "log", "--oneline", "--reverse", "-S", "is_gate6_decision(gate6_decision)",
        "--", "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    ).splitlines()[0]
    assert first.startswith("302f5aba") and "1R.17" in first
    source = (ROOT / "src/pcae/core/runtime_dispatch_gate10_eligibility.py").read_text()
    assert 'if not is_gate6_decision(gate6_decision):' in source
    assert 'return None, ("gate10_untrusted_gate6_decision",)' in source
    assert 'if gate6_decision.decision != "ALLOW":' in source
    assert 'return None, ("gate10_gate6_decision_not_allow",)' in source


def test_18_r26r_changed_no_production_or_normative_contract_file():
    assert _git("diff", "--name-only", C, R, "--", "src/pcae").strip() == ""
    assert _git("diff", "--name-only", C, R, "--", "docs/contracts").strip() == ""
    assert _git("diff", "--name-only", R, "HEAD", "--", "src/pcae").strip() == ""
    assert _git("diff", "--name-only", R, "HEAD", "--", "docs/contracts").strip() == ""


def test_19_reprc_currentness_and_production_unreachability_are_unchanged():
    assert _git("show", f"{B}:{REPRC}") == _git("show", f"{R}:{REPRC}")
    g7 = (ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    g8 = (ROOT / "src/pcae/core/runtime_dispatch_gate8.py").read_text()
    g10 = (ROOT / "src/pcae/core/runtime_dispatch_gate10_eligibility.py").read_text()
    assert "authority_generation_resolver" not in g7[g7.index("def run_gate7_runtime_enforcement"):g7.index("def run_gate7_runtime_enforcement") + 500]
    assert '"currentness_binding"' not in g7
    assert "revalidate_validated_authority_projection" in g7
    assert "gate8_stale_validated_authority_projection" in g8
    assert "gate10_authority_generation_drift" in g10
    assert "gate10_re_decision_expired" in g10
    assert "# pragma: no cover - unreachable in production" in g7


def test_20_runtime_and_first_effect_remain_absent():
    from pcae.core import runtime_introspection as ri

    assert (
        ri.CURRENT_RUNTIME_STATE,
        ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        ri.EXECUTION_AVAILABILITY,
    ) == ("Observed", "observe", "unavailable")
    added_since_effect_freeze = _git(
        "diff", "--unified=0", "8603fe6a", "HEAD", "--", "src/pcae"
    )
    assert not any(
        line.startswith("+") and "adapter.dispatch(" in line
        for line in added_since_effect_freeze.splitlines()
    )
    assert not (ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()


def test_21_no_test_weakening_in_actual_r26r_diff():
    diff = _git("diff", C, R, "--", "tests")
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    assert not any(line.lstrip().startswith(("def test_", "async def test_")) for line in removed)
    weakening_marks = ("@pytest.mark." + "skip", "@pytest.mark." + "x" + "fail")
    assert not any(line.lstrip().startswith(weakening_marks) for line in added)
    repair = _git("diff", C, R, "--", FIRST_FILE, SECOND_FILE)
    assert "issubset" not in repair and "issuperset" not in repair
    assert "fn" + "match" not in repair


def test_22_statuses_and_historical_governance_incident_are_preserved():
    status = (ROOT / "PROJECT_STATUS.md").read_text()
    repair = (ROOT / R26R_DOC).read_text()
    assert "N-16-4 remains **not** CLOSED" in status
    assert "N-16-5 / N-16-6 / N-16-7 remain OPEN" in status
    assert "N-23-2" in repair and "INFO / DEFERRED" in repair
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH" in repair
    assert "UNAUTHORIZED" in repair


def test_23_phase_ids_are_unique_so_successor_must_not_reuse_r27():
    contract = (ROOT / "docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md").read_text()
    assert "Unique per phase" in contract
    assert "roadmap never reuses a phase ID" in contract
    # Canonical parser accepts the repository-conventional repair/restart id.
    from pcae.core.phase_id import parse

    assert parse("149O.20L.7O.3W.1R.2B.1R.1.1R.27R").source_text == "149O.20L.7O.3W.1R.2B.1R.1.1R.27R"
