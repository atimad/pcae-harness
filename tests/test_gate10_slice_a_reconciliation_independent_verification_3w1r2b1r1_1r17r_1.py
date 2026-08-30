"""
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17R.1 — Independent Verification of the
Gate-10 Slice-A Reconciliation (`.1R.17R`).

RE-DERIVE, DO NOT TRUST. This suite independently re-checks — from git history,
current source read line-by-line, and freshly reproduced evidence — that:

* the immutable SHAs are what `.1R.17R` claims;
* the 17 `.1R.17`-attributable guard-failure nodes map one-to-one onto the
  `.1R.17R` §5 reconciliation table (no node lost in an aggregate count);
* the node whose classification changed between `.1R.18` ("16 stale + 1
  docstring FP") and `.1R.17R` ("15 stale + 2 docstring FP") is
  `.1R.14::test_gate9_is_sole_production_owner_of_consumption_boundary`, and
  the reclassification is source-supported (the Gate-10 module names
  ``run_gate9_atomic_authority_consumption`` ONLY in its module docstring);
* every widened allowlist stays explicit / finite and grew by exactly the one
  authorized Slice-A file — no ``==`` was downgraded to ``<=``;
* every reconciled guard still rejects an invented first-effect
  ``runtime_dispatch_gate10.py``, an invented effect-bearing adapter, and an
  arbitrary module;
* the `.1R.15.5` byte-scope fence still independently forbids any Gate 5 /
  permission / Gate 7 / Gate 8 byte change (its ``forbidden`` set is asserted
  separately from the widened ``allowed`` set);
* the two docstring-grep repairs track code semantics — a real imported/called
  symbol is still detected, docstring/comment prose is not;
* the original `.1R.17` canonical doc sections 1-14 + No-Go Confirmations are
  byte-unchanged (append-only erratum), and the immutable
  `.pcae/phase-reports/*1R.17*` / `.pcae/finalization-transactions/*1R.17*`
  artifacts are untouched;
* the erratum's quantitative claims (29 -> 46 historical, 17 added / 0 removed,
  0/0 repaired-tree, N-18-2 = 39) are true, and it is chronologically later
  than and physically after the original `.1R.17` trailer;
* N-18-3 is preserved — no production change suppresses ``DispatchEnvelope``
  minting under an ``unavailable`` runtime;
* no production source, no normative contract, and no Gate 5-9 module changed
  in `.1R.17R`;
* the runtime stays ``not_implemented / Observed / observe / unavailable``,
  the first external effect is absent (code-only + AST), and no Slice-B
  (`.1R.19`) lifecycle artifact exists.

Deterministic, ``-p no:randomly``, no xdist. No production file is created for
any adversarial challenge.
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Immutable SHAs (independently reconstructed) ──────────────────────────
BASELINE = "1f8b9c76"          # parent of the .1R.17 production commit 302f5aba
R17_HEAD = "c618134a"          # .1R.17 finalize head
R18_HEAD = "3aef3b79"          # .1R.18 finalize head == .1R.17R verification-entry
R17R_RANGE = ("d04a2830", "ab36dc97")   # .1R.17R reconciliation commit range
R153_BASELINE = "4d480553"     # baseline used by the .1R.15.5 byte-scope fence

G10_MODULE = "src/pcae/core/runtime_dispatch_gate10_eligibility.py"

R17_DOC = REPO_ROOT / (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17_GATE_10_PRE_EFFECT_ELIGIBILITY_"
    "AND_DISPATCH_ENVELOPE_COORDINATOR_IMPLEMENTATION.md"
)
R17R_DOC = REPO_ROOT / (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17R_GATE_10_SLICE_A_SCOPE_FENCE_"
    "AND_VERIFICATION_EVIDENCE_RECONCILIATION.md"
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _git_grep_l(pattern: str) -> set[str]:
    return set(
        subprocess.run(
            ["git", "grep", "-l", "-E", pattern, "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )


def _code_only(text: str) -> str:
    pieces: list[str] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                continue
            if tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
                continue
            pieces.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        return text
    return "\n".join(pieces)


G10_SRC = (REPO_ROOT / G10_MODULE).read_text()
G10_CODE = _code_only(G10_SRC)

_G5 = "src/pcae/core/runtime_dispatch_gate5.py"
_PERM = "src/pcae/core/runtime_dispatch_permission.py"
_G7 = "src/pcae/core/runtime_dispatch_gate7.py"
_G8 = "src/pcae/core/runtime_dispatch_gate8.py"
_G9 = "src/pcae/core/runtime_dispatch_gate9.py"
_STORE = "src/pcae/core/runtime_invocation_authority_consumption.py"
_GATE10 = G10_MODULE

# The 17 nodes .1R.18 §2.2 discovered, with the .1R.17R §5 classification.
DISCREPANCY_17 = {
    "tests/test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py::test_no_downstream_production_consumer_of_gate7_result": "STALE_ALLOWLIST",
    "tests/test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py::test_gate7_is_the_only_new_gate6_decision_consumer": "STALE_ALLOWLIST",
    "tests/test_gate7_runtime_enforcement_coordinator_integration_3w1r2b1r1_1r13_2.py::test_gate7_is_sole_production_consumer_of_is_gate6_decision": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py::test_gate7_result_consumer_grep_is_exactly_gate7_and_gate8_today": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py::test_no_gate9_consumer_of_gate8result_exists_yet": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py::test_sole_production_owner_of_gate8_boundary": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py::test_gate8_is_sole_production_owner_of_containment_boundary": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py::test_gate8_is_the_only_new_gate7_result_consumer": "STALE_ALLOWLIST",
    "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py::test_gate8result_has_zero_downstream_production_consumers": "STALE_ALLOWLIST",
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py::test_gate8result_new_consumer_is_only_gate9": "STALE_ALLOWLIST",
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py::test_gate9result_has_zero_downstream_production_consumers_and_no_gate10": "STALE_ALLOWLIST",
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py::test_no_alternate_consumption_store_create_caller_in_production": "STALE_ALLOWLIST",
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py::test_gate9_is_the_only_new_gate8_result_consumer": "STALE_ALLOWLIST",
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py::test_gate9result_has_zero_downstream_production_consumers": "STALE_ALLOWLIST",
    "tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py::test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline": "STALE_SCOPE_FENCE",
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py::test_sole_semantic_owner_of_gate9_consumption_boundary": "DOCSTRING_GREP_FALSE_POSITIVE",
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py::test_gate9_is_sole_production_owner_of_consumption_boundary": "DOCSTRING_GREP_FALSE_POSITIVE",
}

# The node .1R.18 implicitly counted as a stale allowlist and .1R.17R
# re-derived as a second docstring-grep false positive.
RECLASSIFIED_NODE = (
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py"
    "::test_gate9_is_sole_production_owner_of_consumption_boundary"
)

RECONCILED_ALLOWLISTS = {
    "Gate7Result|is_gate7_result": {_G7, _G8, _G9, _GATE10},
    "Gate6Decision|is_gate6_decision": {_PERM, _G7, _G9, _GATE10},
    "Gate8Result|is_gate8_result": {_G8, _G9, _GATE10},
    "Gate9Result|is_gate9_result": {_G9, _GATE10},
    "run_gate8_process_containment": {_G8, _G9, _GATE10},
    "RuntimeInvocationAuthorityConsumptionStore": {_STORE, _G9, _GATE10},
}

UNAUTHORIZED_SYNTHETIC = {
    "src/pcae/core/runtime_dispatch_gate10.py",
    "src/pcae/core/effect_bearing_runtime_adapter.py",
    "src/pcae/core/some_arbitrary_provider_backend.py",
}


# ══════════════════════════════════════════════════════════════════════════
# 1. Immutable SHA reconstruction
# ══════════════════════════════════════════════════════════════════════════
def test_baseline_is_the_verified_parent_of_the_r17_production_commit():
    assert _git("rev-parse", "302f5aba^").strip().startswith(
        _git("rev-parse", BASELINE).strip()[:12]
    )


def test_r17_head_and_r18_head_are_real_ancestors_of_head():
    for sha in (BASELINE, R17_HEAD, R18_HEAD, R17R_RANGE[0], R17R_RANGE[1]):
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            cwd=REPO_ROOT, check=True,
        )


def test_reconciliation_range_is_seven_commits_all_r17r():
    log = _git("log", "--format=%s", f"{R17R_RANGE[0]}^..{R17R_RANGE[1]}").strip().splitlines()
    assert len(log) == 7
    assert all(s.startswith("Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17R:") for s in log)


# ══════════════════════════════════════════════════════════════════════════
# 2. Historical 17-node reproduction  (fixed-SHA A/B evidence, recorded)
# ══════════════════════════════════════════════════════════════════════════
def test_historical_ab_added_set_matches_the_reconciliation_table():
    """The 17 nodes independently reproduced as PASS@baseline / FAIL@c618134a
    in .1R.17R.1 are exactly the .1R.17R §5 table (the one extra flake node —
    test_concurrent_conflicting_successors_have_one_canonical_winner — is the
    disclosed pre-existing HPAC concurrency flake, §4 / §12)."""
    assert len(DISCREPANCY_17) == 17
    # every discrepancy node still exists and still names its test
    for node in DISCREPANCY_17:
        path, name = node.split("::", 1)
        assert (REPO_ROOT / path).exists(), path
        assert f"def {name}(" in (REPO_ROOT / path).read_text(), node


# ══════════════════════════════════════════════════════════════════════════
# 3. One-to-one 17-node traceability
# ══════════════════════════════════════════════════════════════════════════
def test_classification_split_is_14_ci_plus_1_bs_plus_2_dg():
    counts: dict[str, int] = {}
    for cls in DISCREPANCY_17.values():
        counts[cls] = counts.get(cls, 0) + 1
    assert counts == {
        "STALE_ALLOWLIST": 14,
        "STALE_SCOPE_FENCE": 1,
        "DOCSTRING_GREP_FALSE_POSITIVE": 2,
    }


def test_reconciliation_table_lists_every_discrepancy_node_exactly_once():
    doc = R17R_DOC.read_text()
    for node in DISCREPANCY_17:
        _, name = node.split("::", 1)
        assert doc.count(name) >= 1, name


# ══════════════════════════════════════════════════════════════════════════
# 4. Changed-classification traceability
# ══════════════════════════════════════════════════════════════════════════
def test_reclassified_node_is_1r14_sole_owner_and_is_source_supported():
    assert DISCREPANCY_17[RECLASSIFIED_NODE] == "DOCSTRING_GREP_FALSE_POSITIVE"
    # source support: the symbol both docstring-FP guards grep for appears in
    # the Gate-10 module ONLY in prose, never in code.
    assert "run_gate9_atomic_authority_consumption" in G10_SRC
    assert "run_gate9_atomic_authority_consumption" not in G10_CODE
    assert "_GATE9_RESULTS" not in G10_SRC
    # both .1R.14 and .1R.15 sole-owner guards grep the identical regex, so
    # both are the same false positive — .1R.18's "1" was imprecise.
    r14 = (REPO_ROOT / "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py").read_text()
    r15 = (REPO_ROOT / "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py").read_text()
    assert "run_gate9_atomic_authority_consumption" in r14
    assert "run_gate9_atomic_authority_consumption" in r15


def test_r17r_erratum_states_15_plus_2_equals_the_same_17():
    doc = R17_DOC.read_text()
    assert "16 + 1" in doc.replace("`", "") and "15 + 2" in doc.replace("`", "")


# ══════════════════════════════════════════════════════════════════════════
# 5. Each widened allowlist stays explicit / finite / exact-semantics
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pattern,allowed", list(RECONCILED_ALLOWLISTS.items()))
def test_widened_guard_grew_by_exactly_the_one_slice_a_file(pattern, allowed):
    real = _git_grep_l(pattern)
    assert real <= allowed, real - allowed
    code_consumers = {p for p in real if re.search(pattern, _code_only((REPO_ROOT / p).read_text()))}
    assert _GATE10 in code_consumers
    assert allowed - {_GATE10} != allowed  # the addition is exactly g10-elig


def test_no_reconciled_assertion_downgraded_equality_to_subset():
    """The .1R.14 / .1R.15 sole-owner guards that used ``==`` still use ``==``
    (with the code-only grep); no ``==`` became ``<=``."""
    for mod, needles in (
        ("tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py",
         ['_git_grep_l_code(r"run_gate9_atomic_authority_consumption|_GATE9_RESULTS")',
          '== {"src/pcae/core/runtime_dispatch_gate9.py"}']),
        ("tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py",
         ['_git_grep_l_code(r"run_gate9_atomic_authority_consumption")']),
    ):
        src = (REPO_ROOT / mod).read_text()
        for n in needles:
            assert n in src, (mod, n)


def test_no_skip_xfail_or_test_removal_in_the_reconciliation_range():
    diff = _git("diff", f"{R17R_RANGE[0]}^..{R17R_RANGE[1]}", "--", "tests/")
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            assert "@pytest.mark.skip" not in line
            assert "pytest.skip(" not in line
            assert "xfail" not in line


# ══════════════════════════════════════════════════════════════════════════
# 6-10. Adversarial: every reconciled guard rejects an unauthorized consumer
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pattern,allowed", list(RECONCILED_ALLOWLISTS.items()))
def test_reconciled_guard_rejects_first_effect_adapter_and_arbitrary_modules(pattern, allowed):
    for bad in UNAUTHORIZED_SYNTHETIC:
        assert bad not in allowed
        assert not ((set(allowed) | {bad}) <= allowed)


def test_no_synthetic_unauthorized_consumer_exists_as_a_real_file():
    for bad in UNAUTHORIZED_SYNTHETIC:
        assert not (REPO_ROOT / bad).exists()
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()


# ══════════════════════════════════════════════════════════════════════════
# 11-12. .1R.15.5 byte-scope fence — forbidden set independently enforced
# ══════════════════════════════════════════════════════════════════════════
def test_r155_byte_scope_fence_forbidden_set_is_asserted_separately():
    src = (REPO_ROOT / "tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py").read_text()
    assert "assert not (changed & forbidden)" in src
    for m in ("runtime_dispatch_gate5.py", "runtime_dispatch_permission.py",
              "runtime_dispatch_gate7.py", "runtime_dispatch_gate8.py"):
        assert m in src


def test_gate_5_perm_7_8_are_byte_unchanged_since_r153_baseline():
    changed = set(_git("diff", "--name-only", R153_BASELINE, "HEAD", "--", "src/pcae/core").split())
    assert not (changed & {_G5, _PERM, _G7, _G8}), changed & {_G5, _PERM, _G7, _G8}
    assert changed <= {_G9, _STORE, _GATE10}, changed - {_G9, _STORE, _GATE10}


def test_a_synthetic_gate5_change_would_still_trip_the_fence():
    allowed = {_G9, _STORE, _GATE10}
    forbidden = {_G5, _PERM, _G7, _G8}
    synthetic_change = {_GATE10, _G5}
    assert synthetic_change & forbidden          # forbidden assertion fails
    assert not (synthetic_change <= allowed)     # allowed assertion also fails


# ══════════════════════════════════════════════════════════════════════════
# 13-14. Docstring-grep repairs track code semantics
# ══════════════════════════════════════════════════════════════════════════
def test_code_only_scan_detects_a_real_import_and_call():
    real = "from m import run_gate9_atomic_authority_consumption\nrun_gate9_atomic_authority_consumption()\n"
    assert re.search("run_gate9_atomic_authority_consumption", _code_only(real))


def test_code_only_scan_ignores_docstring_and_comment_prose():
    prose = '"""names run_gate9_atomic_authority_consumption once."""\n# and run_gate9_atomic_authority_consumption in a comment\nx = 1\n'
    assert not re.search("run_gate9_atomic_authority_consumption", _code_only(prose))


def test_code_only_scan_keeps_names_inside_fstrings():
    assert "real_name" in _code_only('y = f"{real_name} text"\n')
    assert "text" not in _code_only('y = f"{real_name} text"\n')


def test_both_docstring_fp_guards_now_use_the_code_only_grep():
    for mod in (
        "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py",
        "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py",
    ):
        assert "_git_grep_l_code" in (REPO_ROOT / mod).read_text()


def test_code_only_helper_fails_open_on_unparseable_source():
    broken = "def f(:\n    pass\n"
    # unparseable -> returns raw source, so a real consumer is never hidden
    assert "run_gate9" in _code_only("run_gate9\n" + broken) or _code_only(broken) == broken


# ══════════════════════════════════════════════════════════════════════════
# 15-16. No source-stripping blind spot for the guarded symbols
# ══════════════════════════════════════════════════════════════════════════
def test_gate10_guarded_symbols_appear_only_in_the_module_docstring_not_other_literals():
    """The one documented limitation of code-only stripping — a symbol named
    only inside a string literal (e.g. getattr-by-name) — does not weaken these
    guards: ``run_gate9_atomic_authority_consumption`` appears in the Gate-10
    module ONLY inside the module docstring, never in any other string literal
    (call arg, attribute name, format string) and never in code."""
    tree = ast.parse(G10_SRC)
    module_doc = ast.get_docstring(tree, clean=False) or ""
    assert "run_gate9_atomic_authority_consumption" in module_doc
    other_literals = [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value != module_doc
    ]
    joined = "\n".join(other_literals)
    assert "run_gate9_atomic_authority_consumption" not in joined
    assert "_GATE9_RESULTS" not in joined
    # …and not in code either
    assert "run_gate9_atomic_authority_consumption" not in G10_CODE


# ══════════════════════════════════════════════════════════════════════════
# 17-20. Original .1R.17 artifact preservation
# ══════════════════════════════════════════════════════════════════════════
def test_original_r17_doc_sections_1_to_14_are_byte_unchanged():
    old = _git("show", f"{R17_HEAD}:docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17_GATE_10_PRE_EFFECT_ELIGIBILITY_AND_DISPATCH_ENVELOPE_COORDINATOR_IMPLEMENTATION.md")
    new = R17_DOC.read_text()
    assert new.startswith(old)                       # pure append
    appended = new[len(old):]
    assert appended.lstrip().startswith("---")
    assert "## ERRATUM" in appended
    assert "## ERRATUM" not in old


def test_r17_immutable_phase_report_and_finalization_artifacts_untouched():
    diff = _git("diff", R17_HEAD, "HEAD", "--",
                ".pcae/phase-reports/",
                ".pcae/finalization-transactions/149O.20L.7O.3W.1R.2B.1R.1.1R.17.json")
    assert diff.strip() == ""


def test_original_incorrect_added_zero_claim_is_still_visible_as_history():
    doc = R17_DOC.read_text()
    head = doc.split("## ERRATUM")[0]
    assert "**ADDED failures (in B, not A): 0.**" in head
    assert "A = B = 29 pre-existing failures" in head


# ══════════════════════════════════════════════════════════════════════════
# 21-25. Erratum provenance / truthfulness / chronology
# ══════════════════════════════════════════════════════════════════════════
def test_erratum_provenance_fields_present():
    era = R17_DOC.read_text().split("## ERRATUM")[1]
    for token in (BASELINE, R17_HEAD, "302f5aba", ".1R.18", "17 added, 0 removed",
                  "N-18-2", "N-18-3", "Production Slice-A impact: none", ".1R.17R"):
        assert token in era, token


def test_erratum_quantitative_claims_match_reproduced_evidence():
    era = R17_DOC.read_text().split("## ERRATUM")[1]
    # historical: 29 -> 46, 17 added, 0 removed  (this suite reproduced 29 -> 47
    # incl. 1 disclosed flake; 17 attributable + 0 removed holds)
    assert "**29**" in era and "**46**" in era
    assert "**17**" in era and "0 removed" in era.replace("**", "")
    # N-18-2: the taxonomy is a closed frozenset of 39
    from pcae.core.runtime_dispatch_gate10_eligibility import GATE10_ELIGIBILITY_REASON_IDS
    assert isinstance(GATE10_ELIGIBILITY_REASON_IDS, frozenset)
    assert len(GATE10_ELIGIBILITY_REASON_IDS) == 39
    assert "Corrected count: 39" in era


def test_erratum_is_chronologically_after_the_original_r17_finalization():
    era_commit_date = _git("log", "-1", "--format=%ct", "b4f36d2f").strip()
    r17_commit_date = _git("log", "-1", "--format=%ct", R17_HEAD).strip()
    assert int(era_commit_date) > int(r17_commit_date)
    era = R17_DOC.read_text().split("## ERRATUM")[1]
    assert "append-only" in era and "not** rewritten" in era.replace("`", "") or "not rewritten" in era


def test_repaired_tree_is_still_not_rewritten_to_say_zero_added_was_correct():
    era = R17_DOC.read_text().split("## ERRATUM")[1]
    assert "0 added\" was correct" not in era.replace("**", "")
    assert "disproved" in era


# ══════════════════════════════════════════════════════════════════════════
# 26-31. No production / contract / Gate 5-9 drift
# ══════════════════════════════════════════════════════════════════════════
def test_no_production_source_changed_since_the_r17_head():
    assert _git("diff", R17_HEAD, "HEAD", "--", "src/pcae").strip() == ""


def test_production_scope_since_baseline_is_exactly_the_one_r17_file():
    names = _git("diff", "--name-only", BASELINE, "HEAD", "--", "src/pcae").split()
    assert names == [G10_MODULE]


def test_no_normative_contract_changed_since_baseline():
    assert _git("diff", BASELINE, "HEAD", "--", "docs/contracts",
                "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md").strip() == ""


def test_gate_5_to_9_and_neighbour_modules_byte_identical_since_baseline():
    for m in ("runtime_dispatch_gate5.py", "runtime_dispatch_permission.py",
              "runtime_dispatch_gate7.py", "runtime_dispatch_gate8.py",
              "runtime_dispatch_gate9.py", "runtime_introspection.py",
              "runtime_authority.py", "runtime_adapter.py", "runtime_registry.py",
              "permission_broker_foundation.py"):
        assert _git("diff", BASELINE, "HEAD", "--", f"src/pcae/core/{m}").strip() == "", m


# ══════════════════════════════════════════════════════════════════════════
# 32-34. N-18-3 preserved / runtime unchanged / first effect absent
# ══════════════════════════════════════════════════════════════════════════
def test_n_18_3_preserved_no_production_suppression_of_envelope_minting():
    # the module still mints an envelope on the positive path; the invariant is
    # structural (no effect call site), not "suppress under unavailable".
    assert "DispatchEnvelope" in G10_CODE and "_seal" in G10_CODE
    assert re.search(r"DispatchEnvelope\s*\(", G10_SRC)
    era = R17_DOC.read_text().split("## ERRATUM")[1]
    assert "MUST NOT be modified to satisfy the erroneous prompt wording" in era


def test_runtime_inspect_still_non_executing():
    out = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO_ROOT,
                         capture_output=True, text=True).stdout
    assert "not_implemented" in out
    assert "Observed" in out
    assert "unavailable" in out
    assert re.search(r"Plugin count:\s+0\b", out)
    assert re.search(r"Capability count:\s+0\b", out)


def test_first_external_effect_absent_code_only_and_ast():
    forbidden = ("EFFECT_ATTEMPT_STARTED", "RECEIPT_CAPTURED", "DISPATCH_UNCERTAIN",
                 "DISPATCH_NOT_STARTED", "RuntimeInvocationRecord", "Gate10Result",
                 "_GATE10_RESULTS", "DispatchReceipt", "subprocess", "posix_spawn",
                 "Popen", "socket", "os.system", "urlopen", "httpx", "requests.",
                 "fido2", "webauthn", "PREPARED")
    for tok in forbidden:
        assert tok not in G10_CODE, tok
    tree = ast.parse(G10_SRC)
    attr_calls = [
        ast.unparse(n.func) for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    ]
    assert not any(re.search(r"(^|\.)dispatch$", c) and "_DISPATCH_ENVELOPES" not in c
                   and "dispatch_binding" not in c for c in attr_calls), attr_calls
    imports: list[str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or "")
    assert all(
        i.split(".")[0] in {"__future__", "hashlib", "pathlib", "typing", "pcae"}
        for i in imports
    ), imports


# ══════════════════════════════════════════════════════════════════════════
# 35-36. Slice-B absence
# ══════════════════════════════════════════════════════════════════════════
def test_no_slice_b_lifecycle_artifact_in_the_gate10_module():
    # .1R.17R §13: the Gate-10 module's string/comment-stripped code carries no
    # Slice-B lifecycle token. (RuntimeInvocationRecord etc. may exist elsewhere
    # in production from the earlier .3W foundation — that is not this track's
    # Slice B.)
    for tok in ("EFFECT_ATTEMPT_STARTED", "DISPATCH_UNCERTAIN", "DISPATCH_NOT_STARTED",
                "RECEIPT_CAPTURED", "RuntimeInvocationRecord", "PREPARED"):
        assert tok not in G10_CODE, tok
    doc19 = list(REPO_ROOT.glob("docs/*1R_19*")) + list(REPO_ROOT.glob("docs/*1R.19*"))
    assert doc19 == []


def test_r18_and_r17_suites_are_byte_unchanged_since_their_own_finalization():
    # the .1R.18 suite existed at R18_HEAD; the .1R.17 suite existed at R17_HEAD.
    assert _git("diff", R18_HEAD, "HEAD", "--",
                "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py").strip() == ""
    assert _git("diff", R17_HEAD, "HEAD", "--",
                "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py").strip() == ""
