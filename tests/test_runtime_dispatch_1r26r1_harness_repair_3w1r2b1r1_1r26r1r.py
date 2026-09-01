"""Phase .1R.26R.1R — syntax-aware repair of two IV harness scanners."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V = "7d60eda674ec31dd2f7efafdbbfd168c358caca6"
E = V
A = "28b8b2b7"
B = "9d28f7ef"
R = "e52d2f8e"
SCANNER_FILE = "tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py"
IV_FILE = "tests/test_runtime_dispatch_1r26r_reconciliation_independent_verification_3w1r2b1r1_1r26r1.py"
FIRST_GUARD = "tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py"
SECOND_GUARD = "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py"
BLOCKED_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1_INDEPENDENT_VERIFICATION_OF_THE_N_16_4_SCOPE_FENCE_RECONCILIATION.md"


def _run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def _git(*args: str) -> str:
    result = _run("git", *args)
    assert result.returncode == 0, result.stderr
    return result.stdout


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCANNER = _load(SCANNER_FILE, "r26r1r_scanner")


@contextmanager
def _worktree(sha: str):
    with tempfile.TemporaryDirectory(prefix="pcae-1r26r1r-") as directory:
        path = Path(directory) / "wt"
        result = _run("git", "worktree", "add", "--detach", str(path), sha)
        assert result.returncode == 0, result.stderr
        try:
            yield path
        finally:
            result = _run("git", "worktree", "remove", str(path), "--force")
            assert result.returncode == 0, result.stderr


def _pytest_at(path: Path, node: str) -> subprocess.CompletedProcess:
    return _run("python3", "-m", "pytest", "-q", "-o", "addopts=", node, cwd=path)


def test_01_finalized_blocked_and_entry_shas_are_reconstructed():
    assert _git("rev-parse", V).strip() == V
    assert _git("merge-base", E, "HEAD").strip() == E
    assert _git("merge-base", R, V).strip().startswith(R)


def test_02_xfail_node_reproduces_at_finalized_blocked_head():
    node = f"{SCANNER_FILE}::test_14_no_test_weakening_in_the_r26r_diff"
    with _worktree(V) as worktree:
        result = _pytest_at(worktree, node)
    assert result.returncode != 0
    assert "test_14_no_test_weakening" in result.stdout


def test_03_wildcard_node_reproduces_at_finalized_blocked_head():
    node = f"{SCANNER_FILE}::test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff"
    with _worktree(V) as worktree:
        result = _pytest_at(worktree, node)
    assert result.returncode != 0
    assert "test_15_no_wildcard" in result.stdout


def test_04_xfail_false_positive_is_quoted_text_not_executable_structure():
    old = _git("show", f"{V}:{SCANNER_FILE}")
    assert '"xfail" in l' in old
    assert SCANNER._executable_xfail_uses(old) == []


def test_05_wildcard_false_positive_is_scanner_text_not_live_broadening():
    old = _git("show", f"{V}:{SCANNER_FILE}")
    assert '"fnmatch" in l' in old
    assert SCANNER._live_wildcard_or_fnmatch_uses(old) == []


def test_06_real_expected_failure_decorator_is_detected():
    source = "import pytest\n@pytest.mark.xfail(reason='proof')\ndef test_case(): pass\n"
    assert SCANNER._executable_xfail_uses(source) == [("decorator", 2)]


def test_07_real_expected_failure_call_is_detected():
    source = "import pytest\ndef test_case():\n    pytest.xfail('proof')\n"
    assert SCANNER._executable_xfail_uses(source) == [("call", 3)]


def test_08_imported_and_aliased_expected_failure_uses_are_detected():
    direct = "from pytest import xfail as stop\ndef test_case(): stop('proof')\n"
    marked = "import pytest as pt\n@pt.mark.xfail\ndef test_case(): pass\n"
    assert SCANNER._executable_xfail_uses(direct) == [("call", 2)]
    assert SCANNER._executable_xfail_uses(marked) == [("decorator", 2)]


def test_09_expected_failure_strings_comments_and_docstrings_are_ignored():
    source = '''"""pytest.mark.xfail and pytest.xfail("""\n# pytest.mark.xfail\nlabel = "pytest.xfail("\n'''
    assert SCANNER._executable_xfail_uses(source) == []


def test_10_live_fnmatch_calls_and_import_aliases_are_detected():
    qualified = "import fnmatch\ndef guard(path): return fnmatch.fnmatch(path, 'src/pcae/*')\n"
    direct = "from fnmatch import fnmatch as match\ndef guard(path): return match(path, '*')\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(qualified) == [("fnmatch-call", 2)]
    assert SCANNER._live_wildcard_or_fnmatch_uses(direct) == [("fnmatch-call", 2)]


def test_11_live_wildcard_allowlist_is_detected():
    source = "AUTHORIZED_SOURCES = {'src/pcae/*'}\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == [("wildcard-scope-entry", 1)]


def test_12_exact_finite_allowlist_is_accepted():
    source = "AUTHORIZED_SOURCES = {'src/pcae/core/runtime_dispatch_gate7.py'}\n"
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == []


def test_13_wildcard_and_fnmatch_fixture_text_is_ignored():
    source = '''"""fnmatch and wildcard *"""\n# fnmatch(path, "*")\nlabel = "fnmatch"\nfixture = "*"\n'''
    assert SCANNER._live_wildcard_or_fnmatch_uses(source) == []


def test_14_original_security_assertions_remain_executable_and_green():
    SCANNER.test_14_no_test_weakening_in_the_r26r_diff()
    SCANNER.test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff()


def test_15_substantive_r26r_guards_are_byte_identical_to_entry():
    for rel in (FIRST_GUARD, SECOND_GUARD):
        before = _git("show", f"{E}:{rel}").encode()
        after = (ROOT / rel).read_bytes()
        assert hashlib.sha256(after).digest() == hashlib.sha256(before).digest()


def test_16_historical_blocked_report_and_metadata_are_preserved():
    doc = _git("show", f"{V}:{BLOCKED_DOC}")
    metadata = _git("show", f"{V}:.pcae/phase-completion-metadata.json")
    assert "Verdict: BLOCKED" in doc
    assert '"status": "blocked"' in metadata


def test_17_true_42_node_result_is_preserved_independently_of_scanner_text():
    iv = _load(IV_FILE, "r26r1r_iv_count")
    assert len(iv.IMPLEMENTATION_TRIGGERED_NODES | {iv.SECOND_NODE}) == 42


def test_18_repaired_nodes_remain_green_and_exact():
    first = f"{FIRST_GUARD}::test_runtime_posture_unchanged_and_no_new_first_effect_call_site"
    second = f"{SECOND_GUARD}::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set"
    result = _pytest_at(ROOT, first)
    assert result.returncode == 0, result.stdout
    result = _pytest_at(ROOT, second)
    assert result.returncode == 0, result.stdout


def test_19_unrelated_gate6_gate10_finding_remains_preexisting_and_untouched():
    line = _git("log", "--oneline", "--reverse", "-S", "is_gate6_decision(gate6_decision)", "--", "src/pcae/core/runtime_dispatch_gate10_eligibility.py").splitlines()[0]
    assert line.startswith("302f5aba")
    assert _git("diff", "--name-only", E, "HEAD", "--", "src/pcae/core/runtime_dispatch_gate10_eligibility.py") == ""


def test_20_no_production_or_normative_contract_diff():
    assert _git("diff", "--name-only", E, "HEAD", "--", "src/pcae") == ""
    assert _git("diff", "--name-only", E, "HEAD", "--", "docs/contracts") == ""


def test_21_runtime_and_first_effect_state_are_unchanged():
    from pcae.core import runtime_introspection as runtime
    assert (runtime.CURRENT_RUNTIME_STATE, runtime.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, runtime.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")
    added = _git("diff", "--unified=0", "8603fe6a", "HEAD", "--", "src/pcae")
    assert not any(line.startswith("+") and "adapter.dispatch(" in line for line in added.splitlines())


def test_22_open_statuses_debt_and_governance_incident_are_preserved():
    status = (ROOT / "PROJECT_STATUS.md").read_text()
    repair = (ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md").read_text()
    assert "N-16-5/6/7 remain OPEN" in status or "N-16-5 / N-16-6 / N-16-7 remain OPEN" in status
    assert "N-23-2" in repair and "INFO / DEFERRED" in repair
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH" in repair
    assert "UNAUTHORIZED" in repair
