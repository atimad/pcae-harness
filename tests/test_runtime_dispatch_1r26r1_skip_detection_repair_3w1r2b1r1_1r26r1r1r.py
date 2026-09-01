"""Phase .1R.26R.1R.1R — executable skip-detection harness repair."""

from __future__ import annotations

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
SCANNER_REL = "tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py"
BLOCKED_IV_REL = "tests/test_runtime_dispatch_1r26r1_harness_repair_independent_verification_3w1r2b1r1_1r26r1r1.py"
REPAIR_SUITE_REL = "tests/test_runtime_dispatch_1r26r1_harness_repair_3w1r2b1r1_1r26r1r.py"
R26R_IV_REL = "tests/test_runtime_dispatch_1r26r_reconciliation_independent_verification_3w1r2b1r1_1r26r1.py"
FIRST_GUARD = "tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py"
SECOND_GUARD = "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py"
BLOCKED_REPORT = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_1_INDEPENDENT_VERIFICATION_OF_THE_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_REPAIR.md"


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


SCANNER = _load_current(SCANNER_REL, "skip_repair_scanner")
H_SCANNER = _load_at(H, SCANNER_REL, "pre_skip_repair_scanner")


def _uses(source: str) -> list[tuple[str, int]]:
    return SCANNER._executable_test_weakening_uses(source)


def test_01_phase_sha_chain_is_reconstructed():
    for sha in (A, B, R, V, H, J):
        assert _git("rev-parse", sha).strip() == sha
    assert _git("merge-base", J, "HEAD").strip() == J


def test_02_exact_blocked_skip_false_negative_reproduces_at_h():
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_example(): pass\n"
    assert H_SCANNER._executable_xfail_uses(source) == []


def test_03_predecessor_invariant_is_reconstructed_from_v():
    source = _git("show", f"{V}:{SCANNER_REL}")
    predicate = 'assert not any("@pytest.mark.skip" in l or "xfail" in l for l in added)'
    assert predicate in source
    assert "@pytest.mark.skip" in "@pytest.mark.skipif(condition, reason='proof')"


def test_04_real_xfail_decorator_is_detected():
    source = "import pytest\n@pytest.mark.xfail(reason='proof')\ndef test_case(): pass\n"
    assert _uses(source) == [("xfail-mark", 2)]


def test_05_real_pytest_xfail_call_is_detected():
    source = "import pytest\ndef test_case(): pytest.xfail('proof')\n"
    assert _uses(source) == [("xfail-call", 2)]


def test_06_real_skip_decorator_is_detected():
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_case(): pass\n"
    assert _uses(source) == [("skip-mark", 2)]


def test_07_real_skipif_decorators_are_detected_without_condition_evaluation():
    always = "import pytest\n@pytest.mark.skipif(True, reason='proof')\ndef test_case(): pass\n"
    conditional = "import pytest\n@pytest.mark.skipif(condition, reason='proof')\ndef test_case(): pass\n"
    assert _uses(always) == [("skipif-mark", 2)]
    assert _uses(conditional) == [("skipif-mark", 2)]


def test_08_real_pytest_skip_call_is_detected():
    source = "import pytest\ndef test_case(): pytest.skip('proof')\n"
    assert _uses(source) == [("skip-call", 2)]


def test_09_xfail_strings_are_ignored():
    source = "a = 'pytest.mark.xfail'\nb = 'pytest.xfail('\n"
    assert _uses(source) == []


def test_10_skip_strings_are_ignored():
    source = "a = 'pytest.mark.skip'\nb = 'pytest.mark.skipif'\nc = 'pytest.skip('\n"
    assert _uses(source) == []


def test_11_comments_are_ignored():
    source = "# pytest.mark.skip and pytest.xfail( and skipif\nvalue = 1\n"
    assert _uses(source) == []


def test_12_docstrings_are_ignored():
    source = "\"\"\"pytest.mark.skipif and pytest.mark.xfail\"\"\"\nvalue = 1\n"
    assert _uses(source) == []


def test_13_mixed_inert_and_executable_source_finds_only_executable_use():
    source = "\"\"\"pytest.mark.xfail\"\"\"\n# pytest.mark.skip\nlabel = 'pytest.skip('\nimport pytest\ndef test_case(): pytest.skip('proof')\n"
    assert _uses(source) == [("skip-call", 5)]
    assert SCANNER._introduced_executable_test_weakening_uses("", source) == [("skip-call", 5)]
    assert SCANNER._introduced_executable_test_weakening_uses(source, source + "value = 2\n") == []


def test_14_alias_and_import_forms_are_resolved():
    source = "import pytest as pt\nfrom pytest import skip as stop, skipif as only_if, xfail as expected\n@pt.mark.skip\n@only_if(condition, reason='proof')\ndef test_case(): stop('proof'); expected('proof')\n"
    assert _uses(source) == [
        ("skip-call", 5), ("skip-mark", 3),
        ("skipif-mark", 4), ("xfail-call", 5),
    ]


def test_15_module_level_pytestmark_skip_and_skipif_are_detected():
    source = "import pytest\npytestmark = [pytest.mark.skip, pytest.mark.skipif(condition, reason='proof')]\n"
    assert _uses(source) == [("skip-mark", 2), ("skipif-mark", 2)]


def test_16_syntax_errors_fail_closed():
    with pytest.raises(SyntaxError):
        _uses("def broken(:\n")


def test_17_real_fnmatch_detection_is_preserved():
    source = "import fnmatch\ndef guard(path): return fnmatch.fnmatch(path, 'src/pcae/*')\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == [("fnmatch-call", 2)]


def test_18_live_wildcard_allowlist_detection_is_preserved():
    source = "AUTHORIZED_SOURCES = {'src/pcae/*'}\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == [("wildcard-scope-entry", 1)]


def test_19_inert_wildcard_strings_are_ignored():
    source = "\"\"\"fnmatch *\"\"\"\nfixture = '*'\nlabel = 'fnmatch'\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == []


def test_20_exact_finite_allowlist_is_accepted():
    source = "AUTHORIZED_SOURCES = {'src/pcae/core/runtime_dispatch_gate7.py'}\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == []


def test_21_substantive_r26r_guards_are_byte_identical_h_to_head():
    for rel in (FIRST_GUARD, SECOND_GUARD):
        assert hashlib.sha256(_git("show", f"{H}:{rel}").encode()).digest() == hashlib.sha256((ROOT / rel).read_bytes()).digest()


def test_22_ast_self_reference_repair_is_preserved():
    scanner_source = (ROOT / SCANNER_REL).read_text()
    assert "ast.parse(source)" in scanner_source
    assert _uses(scanner_source) == []


def test_23_blocked_iv_record_is_preserved():
    report = (ROOT / BLOCKED_REPORT).read_text()
    metadata = _git("show", f"{J}:.pcae/phase-completion-metadata.json")
    assert "Verdict: BLOCKED" in report
    assert '"status": "blocked"' in metadata


def test_24_historical_42_node_result_is_preserved():
    iv = _load_current(R26R_IV_REL, "skip_repair_count_iv")
    assert len(iv.IMPLEMENTATION_TRIGGERED_NODES | {iv.SECOND_NODE}) == 42


def test_25_repaired_a_r_nodes_remain_green():
    nodes = [
        f"{FIRST_GUARD}::test_runtime_posture_unchanged_and_no_new_first_effect_call_site",
        f"{SECOND_GUARD}::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set",
    ]
    result = _run("python3", "-m", "pytest", "-q", "-o", "addopts=", *nodes)
    assert result.returncode == 0, result.stdout


def test_26_unrelated_gate6_gate10_finding_is_untouched():
    rel = "src/pcae/core/runtime_dispatch_gate10_eligibility.py"
    assert _git("diff", "--name-only", J, "HEAD", "--", rel) == ""
    first = _git("log", "--oneline", "--reverse", "-S", "is_gate6_decision(gate6_decision)", "--", rel).splitlines()[0]
    assert first.startswith("302f5aba")


def test_27_no_production_diff():
    assert _git("diff", "--name-only", J, "HEAD", "--", "src/pcae") == ""


def test_28_no_normative_contract_diff():
    assert _git("diff", "--name-only", J, "HEAD", "--", "docs/contracts") == ""


def test_29_runtime_and_first_effect_are_unchanged():
    from pcae.core import runtime_introspection as runtime
    assert (runtime.CURRENT_RUNTIME_STATE, runtime.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, runtime.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")
    added = _git("diff", "--unified=0", "8603fe6a", "HEAD", "--", "src/pcae")
    assert not any(line.startswith("+") and "adapter.dispatch(" in line for line in added.splitlines())


def test_30_open_successors_and_deferred_debt_are_untouched():
    status = (ROOT / "PROJECT_STATUS.md").read_text()
    repair = (ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md").read_text()
    assert "N-16-5/6/7 remain OPEN" in status or "N-16-5 / N-16-6 / N-16-7 remain OPEN" in status
    assert "N-23-2" in repair and "INFO / DEFERRED" in repair


def test_31_governance_incident_is_preserved():
    repair = (ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md").read_text()
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH" in repair
    assert "UNAUTHORIZED" in repair
