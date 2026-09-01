"""BLOCKED IV evidence for phase .1R.26R.1R.1.

The repair correctly recognizes executable xfail constructs, but it dropped
the predecessor guard's executable skip prohibition.  This suite freezes the
primary-source evidence without modifying the finalized repair harness.
"""

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
I = "ee473b94f2411b6d7776a15e6585e834f82008a4"
SCANNER_REL = "tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py"
FIRST_GUARD = "tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py"
SECOND_GUARD = "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py"
BLOCKED_DOC = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1_INDEPENDENT_VERIFICATION_OF_THE_N_16_4_SCOPE_FENCE_RECONCILIATION.md"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def _git(*args: str) -> str:
    result = _run("git", *args)
    assert result.returncode == 0, result.stderr
    return result.stdout


def _load_scanner():
    spec = importlib.util.spec_from_file_location("blocked_iv_scanner", ROOT / SCANNER_REL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCANNER = _load_scanner()


def _load_historical_scanner(sha: str):
    module = types.ModuleType(f"historical_scanner_{sha}")
    module.__file__ = str(ROOT / SCANNER_REL)
    source = _git("show", f"{sha}:{SCANNER_REL}")
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


H_SCANNER = _load_historical_scanner(H)


def test_01_immutable_sha_chain_is_reconstructed():
    for sha in (A, B, R, V, H, I):
        assert _git("rev-parse", sha).strip() == sha
    assert _git("merge-base", I, "HEAD").strip() == I


def test_02_pre_repair_guard_explicitly_prohibited_skip_to_pass():
    source = _git("show", f"{V}:{SCANNER_REL}")
    assert 'assert not any("@pytest.mark.skip" in l or "xfail" in l for l in added)' in source
    synthetic_added_line = "+@pytest.mark.skip(reason='proof')"
    assert "@pytest.mark.skip" in synthetic_added_line


def test_03_repaired_ast_helper_misses_real_skip_decorator():
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_example(): pass\n"
    assert H_SCANNER._executable_xfail_uses(source) == []
    assert SCANNER._executable_test_weakening_uses(source) == [("skip-mark", 2)]


def test_04_repaired_ast_helper_misses_real_pytest_skip_call():
    source = "import pytest\ndef test_example(): pytest.skip('proof')\n"
    assert H_SCANNER._executable_xfail_uses(source) == []
    assert SCANNER._executable_test_weakening_uses(source) == [("skip-call", 2)]


def test_05_repaired_no_weakening_test_false_negatives_executable_skip(monkeypatch):
    source = "import pytest\n@pytest.mark.skip(reason='proof')\ndef test_example(): pass\n"
    monkeypatch.setattr(H_SCANNER, "_changed_test_sources", lambda: [("synthetic.py", "", source)])
    H_SCANNER.test_14_no_test_weakening_in_the_r26r_diff()
    monkeypatch.setattr(SCANNER, "_changed_test_sources", lambda: [("synthetic.py", "", source)])
    with pytest.raises(AssertionError):
        SCANNER.test_14_no_test_weakening_in_the_r26r_diff()


def test_06_repaired_ast_helper_still_detects_real_xfail_forms():
    decorator = "import pytest\n@pytest.mark.xfail(reason='proof')\ndef test_example(): pass\n"
    call = "import pytest\ndef test_example(): pytest.xfail('proof')\n"
    assert SCANNER._executable_xfail_uses(decorator) == [("decorator", 2)]
    assert SCANNER._executable_xfail_uses(call) == [("call", 2)]


def test_07_repair_claimed_original_security_assertions_but_omitted_skip():
    repair_suite = (ROOT / "tests/test_runtime_dispatch_1r26r1_harness_repair_3w1r2b1r1_1r26r1r.py").read_text()
    assert "original_security_assertions_remain_executable_and_green" in repair_suite
    assert "pytest.mark.skip" not in repair_suite
    assert "pytest.skip" not in repair_suite


def test_08_substantive_reconciliation_guards_are_byte_identical_r_to_h():
    for rel in (FIRST_GUARD, SECOND_GUARD):
        before = _git("show", f"{R}:{rel}").encode()
        after = _git("show", f"{H}:{rel}").encode()
        assert hashlib.sha256(before).digest() == hashlib.sha256(after).digest()


def test_09_historical_blocked_record_is_preserved_at_h():
    source = _git("show", f"{H}:{BLOCKED_DOC}")
    assert "Verdict: BLOCKED" in source
    assert "`.1R.26R`: **NOT VERIFIED**" in source


def test_10_no_production_or_contract_drift_in_repair():
    assert _git("diff", "--name-only", V, H, "--", "src/pcae") == ""
    assert _git("diff", "--name-only", V, H, "--", "docs/contracts") == ""
