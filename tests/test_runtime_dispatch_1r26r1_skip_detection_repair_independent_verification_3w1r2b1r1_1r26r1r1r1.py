"""Independent verification of the .1R.26R.1R.1R skip-detection repair."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import subprocess
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
A = "28b8b2b70dcd4642dc45d4a3961a5218402c3c7c"
B = "9d28f7efc3923bfca5e18b98e0a203881b256b7e"
R = "e52d2f8e9175015a2b344a547bea0c11058a92c8"
V = "7d60eda674ec31dd2f7efafdbbfd168c358caca6"
H = "5f894e72fb37429b221c122bfad4943be88287bd"
J = "d334c74e4c987640c612f77d64a4dba6ae160692"
K = "eeb31757098cb5b02ace9f4f0fabe14370bd40c4"
K_REPAIR = "e512f96e0a8ad179b2e71506cb7ab8a0ed59ee6b"
I = K

SCANNER_REL = "tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py"
REPAIR_SUITE_REL = "tests/test_runtime_dispatch_1r26r1_skip_detection_repair_3w1r2b1r1_1r26r1r1r.py"
BLOCKED_IV_REL = "tests/test_runtime_dispatch_1r26r1_harness_repair_independent_verification_3w1r2b1r1_1r26r1r1.py"
FIRST_GUARD = "tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py"
SECOND_GUARD = "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py"
R26R_IV_REL = "tests/test_runtime_dispatch_1r26r_reconciliation_independent_verification_3w1r2b1r1_1r26r1.py"
REPAIR_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_1R_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_SKIP_DETECTION_REPAIR.md"
FIRST_REPAIR_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_REPAIR.md"
BLOCKED_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_1_INDEPENDENT_VERIFICATION_OF_THE_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_REPAIR.md"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def _git(*args: str) -> str:
    result = _run("git", *args)
    assert result.returncode == 0, result.stderr
    return result.stdout


def _load_current(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_at(sha: str, rel: str, name: str):
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / rel)
    source = _git("show", f"{sha}:{rel}")
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


SCANNER = _load_current(SCANNER_REL, "skip_repair_iv_scanner")
J_SCANNER = _load_at(J, SCANNER_REL, "skip_repair_iv_j_scanner")


def _uses(source: str) -> list[tuple[str, int]]:
    return SCANNER._executable_test_weakening_uses(source)


def _wild(source: str) -> list[tuple[str, int]]:
    return SCANNER._live_wildcard_or_fnmatch_uses(source)


def test_01_sha_chain_is_reconstructed_from_git():
    for sha in (A, B, R, V, H, J, K_REPAIR, K, I):
        assert _git("rev-parse", sha).strip() == sha
    assert _git("merge-base", K, "HEAD").strip() == K


def test_02_historical_skip_false_negative_reproduces_at_j():
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_example(): pass\n"
    assert J_SCANNER._executable_xfail_uses(source) == []


def test_03_k_repaired_scanner_detects_the_historical_adversary():
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_example(): pass\n"
    assert _uses(source) == [("skip-mark", 2)]


def test_04_predecessor_invariant_is_reconstructed_from_v_source():
    source = _git("show", f"{V}:{SCANNER_REL}")
    predicate = 'assert not any("@pytest.mark.skip" in l or "xfail" in l for l in added)'
    assert predicate in source
    assert "@pytest.mark.skip" in "@pytest.mark.skipif(condition, reason='proof')"


def test_05_real_xfail_decorator_is_detected():
    source = "import pytest\n@pytest.mark.xfail(reason='x')\ndef test_example(): pass\n"
    assert _uses(source) == [("xfail-mark", 2)]


def test_06_real_pytest_xfail_call_is_detected():
    source = "import pytest\ndef test_example(): pytest.xfail('reason')\n"
    assert _uses(source) == [("xfail-call", 2)]


def test_07_real_skip_decorator_is_detected():
    source = "import pytest\n@pytest.mark.skip(reason='x')\ndef test_example(): pass\n"
    assert _uses(source) == [("skip-mark", 2)]


def test_08_real_skipif_true_decorator_is_detected():
    source = "import pytest\n@pytest.mark.skipif(True, reason='x')\ndef test_example(): pass\n"
    assert _uses(source) == [("skipif-mark", 2)]


def test_09_real_skipif_conditional_decorator_is_detected_without_evaluation():
    source = "import pytest\n@pytest.mark.skipif(condition, reason='x')\ndef test_example(): pass\n"
    assert _uses(source) == [("skipif-mark", 2)]


def test_10_real_pytest_skip_call_is_detected():
    source = "import pytest\ndef test_example(): pytest.skip('reason')\n"
    assert _uses(source) == [("skip-call", 2)]


def test_11_module_level_pytestmark_is_in_the_supported_surface():
    source = "import pytest\npytestmark=[pytest.mark.skip, pytest.mark.xfail(reason='x')]\n"
    assert _uses(source) == [("skip-mark", 2), ("xfail-mark", 2)]


def test_12_class_level_marks_are_in_the_supported_surface():
    source = "import pytest\n@pytest.mark.skip(reason='x')\nclass TestExample: pass\n"
    assert _uses(source) == [("skip-mark", 2)]


def test_13_pytest_alias_is_resolved():
    source = "import pytest as pt\n@pt.mark.skip\ndef test_example(): pt.xfail('x')\n"
    assert _uses(source) == [("skip-mark", 2), ("xfail-call", 3)]


def test_14_direct_import_aliases_are_resolved():
    source = "from pytest import skip as stop, skipif as iff, xfail as xf, mark as mk\n@mk.xfail\n@iff(True, reason='x')\ndef test_example(): stop('x'); xf('x')\n"
    assert _uses(source) == [
        ("skip-call", 4), ("skipif-mark", 3),
        ("xfail-call", 4), ("xfail-mark", 2),
    ]


def test_15_inert_xfail_strings_are_ignored():
    assert _uses("a='pytest.mark.xfail'\nb='pytest.xfail('\n") == []


def test_16_inert_skip_strings_are_ignored():
    assert _uses("a='pytest.mark.skip'\nb='pytest.mark.skipif'\nc='pytest.skip('\n") == []


def test_17_comments_are_ignored():
    assert _uses("# pytest.mark.skip pytest.mark.skipif pytest.xfail(\nvalue=1\n") == []


def test_18_docstrings_are_ignored():
    source = "'''pytest.mark.xfail pytest.mark.skipif pytest.skip('x')'''\nvalue=1\n"
    assert _uses(source) == []


def test_19_mixed_fixture_reports_only_the_executable_construct():
    source = "'''pytest.mark.skipif'''\n# pytest.xfail('x')\nlabel='pytest.skip('\nimport pytest\ndef test_example(): pytest.skip('x')\n"
    assert _uses(source) == [("skip-call", 5)]


def test_20_malformed_source_fails_safely():
    with pytest.raises(SyntaxError):
        _uses("def broken(:\n")


def test_21_real_fnmatch_call_is_detected():
    source = "import fnmatch\ndef guard(path): return fnmatch.fnmatch(path, 'src/pcae/*')\n"
    assert _wild(source) == [("fnmatch-call", 2)]


def test_22_live_wildcard_allowlist_is_detected():
    assert _wild("AUTHORIZED_SOURCES={'src/pcae/*'}\n") == [("wildcard-scope-entry", 1)]


def test_23_exact_finite_allowlist_is_accepted():
    source = "AUTHORIZED_SOURCES={'src/pcae/core/runtime_dispatch_gate7.py','src/pcae/core/runtime_dispatch_permission.py'}\n"
    assert _wild(source) == []


def test_24_inert_wildcard_text_is_ignored():
    source = "'''fnmatch src/pcae/*'''\n# *\nfixture='*'\nlabel='fnmatch'\n"
    assert _wild(source) == []


def test_25_prefix_broadening_is_not_overclaimed_as_part_of_this_scanner():
    source = "def guard(path): return path.startswith('src/pcae/')\n"
    assert _wild(source) == []
    historical = _git("show", f"{V}:{SCANNER_REL}")
    assert 'assert not any("fnmatch" in l for l in added)' in historical


def test_26_pre_post_security_matrix_restores_every_source_backed_form():
    fixtures = {
        "xfail-mark": "import pytest\n@pytest.mark.xfail\ndef test_x(): pass\n",
        "xfail-call": "import pytest\ndef test_x(): pytest.xfail('x')\n",
        "skip-mark": "import pytest\n@pytest.mark.skip\ndef test_x(): pass\n",
        "skipif-mark": "import pytest\n@pytest.mark.skipif(flag, reason='x')\ndef test_x(): pass\n",
        "skip-call": "import pytest\ndef test_x(): pytest.skip('x')\n",
    }
    assert {kind: _uses(source)[0][0] for kind, source in fixtures.items()} == {kind: kind for kind in fixtures}


def test_27_no_over_detection_on_legitimate_prose_and_fixture_data():
    source = "name='test_skip_history'\nenglish='skip this paragraph'\nglob='*'\ndoc='pytest.mark.xfail'\n"
    assert _uses(source) == [] and _wild(source) == []


def test_28_no_under_detection_on_the_reconstructed_executable_surface():
    source = "import pytest\n@pytest.mark.skipif(flag, reason='x')\n@pytest.mark.xfail\ndef test_x(): pytest.skip('x')\n"
    assert {kind for kind, _line in _uses(source)} == {"skipif-mark", "xfail-mark", "skip-call"}


def test_29_substantive_r26r_guards_are_byte_identical_r_to_k():
    for rel in (FIRST_GUARD, SECOND_GUARD):
        before = _git("show", f"{R}:{rel}").encode()
        after = _git("show", f"{K}:{rel}").encode()
        assert hashlib.sha256(before).digest() == hashlib.sha256(after).digest()


def test_30_harness_change_surface_is_narrow_and_classifiable():
    changed = set(_git("diff", "--name-only", J, K).splitlines())
    test_changes = {path for path in changed if path.startswith("tests/")}
    assert test_changes == {SCANNER_REL, BLOCKED_IV_REL, REPAIR_SUITE_REL}
    assert all(path.startswith((".pcae/", "docs/", "tasks/", "tests/")) or path in {"PROJECT_STATUS.md", "CHANGELOG.md"} for path in changed)


def test_31_historical_blocked_records_are_preserved():
    assert '"status": "blocked"' in _git("show", f"{J}:.pcae/phase-completion-metadata.json")
    assert "Verdict: BLOCKED" in (ROOT / BLOCKED_DOC).read_text()
    r27 = _git("show", "ba4d21c3:.pcae/phase-completion-metadata.json")
    assert '"status": "blocked"' in r27


def test_32_repair_provenance_records_the_complete_chronology():
    repair = (ROOT / REPAIR_DOC).read_text()
    first = (ROOT / FIRST_REPAIR_DOC).read_text()
    for phrase in ("V's executable policy", "H's `_executable_xfail_uses` returned `[]`", "successor adds"):
        assert phrase in repair
    assert "Successor annotation" in first
    assert "AST replacement unintentionally" in first
    assert "dropped the predecessor guard's executable skip-to-pass coverage" in first


def test_33_historical_42_node_result_is_independent_of_scanner_internals():
    iv = _load_current(R26R_IV_REL, "skip_repair_independent_count")
    assert len(iv.IMPLEMENTATION_TRIGGERED_NODES | {iv.SECOND_NODE}) == 42


def test_34_repaired_a_r_nodes_remain_green():
    nodes = [
        f"{FIRST_GUARD}::test_runtime_posture_unchanged_and_no_new_first_effect_call_site",
        f"{SECOND_GUARD}::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set",
    ]
    result = _run("python3", "-m", "pytest", "-q", "-o", "addopts=", "-p", "no:randomly", *nodes)
    assert result.returncode == 0, result.stdout


def test_35_j_k_fixed_semantic_attribution_is_exact():
    skip = "import pytest\n@pytest.mark.skip(reason='x')\ndef test_x(): pass\n"
    xfail = "import pytest\n@pytest.mark.xfail(reason='x')\ndef test_x(): pass\n"
    assert J_SCANNER._executable_xfail_uses(skip) == []
    assert _uses(skip) == [("skip-mark", 2)]
    assert J_SCANNER._executable_xfail_uses(xfail) == [("decorator", 2)]
    assert SCANNER._executable_xfail_uses(xfail) == [("decorator", 2)]


def test_36_broad_guard_selection_is_reconstructed_from_executable_git_guards():
    selected = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        source = path.read_text()
        tree = ast.parse(source)
        has_guard = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_git"
            and "src/pcae" in ast.unparse(node)
            for node in ast.walk(tree)
        )
        if has_guard or any(token in path.name for token in ("runtime_dispatch", "gate7", "narrow_eligibility", "permission_broker_observation")):
            selected.add(path.name)
    assert len(selected) >= 60
    assert Path(SCANNER_REL).name in selected and Path(REPAIR_SUITE_REL).name in selected


def test_37_unrelated_gate6_gate10_finding_is_unchanged():
    rel = "src/pcae/core/runtime_dispatch_gate10_eligibility.py"
    assert _git("diff", "--name-only", J, K, "--", rel) == ""
    first = _git("log", "--oneline", "--reverse", "-S", "is_gate6_decision(gate6_decision)", "--", rel).splitlines()[0]
    assert first.startswith("302f5aba")


def test_38_no_production_diff_in_the_repair_or_this_iv_entry():
    assert _git("diff", "--name-only", J, K, "--", "src/pcae") == ""
    assert _git("diff", "--name-only", I, "HEAD", "--", "src/pcae") == ""


def test_39_no_normative_contract_diff_in_the_repair_or_this_iv_entry():
    assert _git("diff", "--name-only", J, K, "--", "docs/contracts") == ""
    assert _git("diff", "--name-only", I, "HEAD", "--", "docs/contracts") == ""


def test_40_meta_guard_inventory_is_present_and_executable():
    for rel in (SCANNER_REL, BLOCKED_IV_REL, REPAIR_SUITE_REL, R26R_IV_REL):
        assert (ROOT / rel).exists()
    assert callable(SCANNER.test_14_no_test_weakening_in_the_r26r_diff)
    assert callable(SCANNER.test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff)


def test_41_no_test_function_removal_or_introduced_live_weakening_j_to_k():
    for rel in _git("diff", "--name-only", J, K, "--", "tests").splitlines():
        old = _git("show", f"{J}:{rel}") if _run("git", "cat-file", "-e", f"{J}:{rel}").returncode == 0 else ""
        new = _git("show", f"{K}:{rel}")
        old_defs = {n.name for n in ast.walk(ast.parse(old)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")} if old else set()
        new_defs = {n.name for n in ast.walk(ast.parse(new)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
        assert old_defs <= new_defs
        assert SCANNER._introduced_executable_test_weakening_uses(old, new) == []
        assert _wild(new) == []


def test_42_runtime_and_first_effect_boundaries_are_unchanged():
    from pcae.core import runtime_introspection as runtime
    assert (runtime.CURRENT_RUNTIME_STATE, runtime.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, runtime.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")
    added = _git("diff", "--unified=0", "8603fe6a", "HEAD", "--", "src/pcae")
    assert not any(line.startswith("+") and "adapter.dispatch(" in line for line in added.splitlines())
    assert not (ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()


def test_43_status_debt_successor_and_governance_boundaries_are_preserved():
    status = (ROOT / "PROJECT_STATUS.md").read_text()
    decisions = (ROOT / "tasks/DECISIONS.md").read_text()
    repair = (ROOT / REPAIR_DOC).read_text()
    assert "N-16-4 remains IMPLEMENTED / NOT CLOSED" in status
    assert "N-16-5/6/7 OPEN" in status
    assert "N-23-2 INFO / DEFERRED" in status
    assert "historical `.1R.27` remains BLOCKED and cannot be reused" in decisions
    assert "`.1R.27R`" in decisions
    assert "DELEGATED `.3` FINALIZATION / COMMIT / PUSH" in repair
    assert "UNAUTHORIZED" in repair
