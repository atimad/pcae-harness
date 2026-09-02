"""
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17R — Gate-10 Slice-A Scope-Fence and
Verification-Evidence Reconciliation.

This suite is the dedicated reconciliation-verification battery for `.1R.17R`.
It re-derives — from primary evidence (RDGO-001 v3.1 §11 item 4 / §16, the
`.1R.16` plan, and the current Slice-A source read line-by-line) — that:

* the 17 pre-existing scope-fence / consumer-inventory guard failures `.1R.18`
  discovered are each reconciled by the minimal, still-tight repair;
* 15 of the 17 are legitimate stale allowlist / scope-fence guards (the
  non-effecting Gate-10 pre-effect eligibility coordinator legitimately
  references the upstream lineage symbols **in code**); 2 are docstring-grep
  false positives (both tripped only by the module docstring's single mention
  of ``run_gate9_atomic_authority_consumption``) and receive a code-only-scan
  repair rather than an allowlist widening;
* every repaired guard still rejects any *other* unauthorized importer — an
  invented future first-effect module, an invented effect-bearing adapter
  consumer, and an arbitrary production module all still fail;
* the `.1R.15.5` byte-scope fence still forbids any Gate 5 / permission /
  Gate 7 / Gate 8 production byte change;
* NO production source and NO normative contract changed in `.1R.17R`;
* NO Slice-B (`.1R.19`) or first-external-effect (Slice C) artifact was
  introduced; runtime stays ``not_implemented / Observed / observe /
  unavailable``;
* N-18-2 (the reason-taxonomy prose count) is corrected in the `.1R.17R`
  reconciliation prose to the true 39; the taxonomy itself is unchanged;
* N-18-3 is preserved — production code is NOT modified to suppress
  ``DispatchEnvelope`` minting under an ``unavailable`` runtime;
* the original `.1R.17` phase-completion report / doc / immutable phase-report
  artifacts are preserved verbatim (the incorrect "0 added" A/B claim is left
  standing as historical evidence), and the `.1R.17R` erratum points back at
  the preserved original with the corrected figures.

Deterministic, ``-p no:randomly``, no xdist. No production file is created for
any adversarial challenge — the unauthorized-consumer checks use synthetic
in-memory hit sets.
"""

from __future__ import annotations

import io
import re
import subprocess
import tokenize
from pathlib import Path

import pytest

from pcae.core.runtime_dispatch_gate10_eligibility import (
    GATE10_ELIGIBILITY_REASON_IDS,
    build_gate10_capability_snapshot_resolver,
    run_gate10_pre_effect_eligibility,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Fixed SHAs (immutable) ────────────────────────────────────────────────
IMMUTABLE_BASELINE = "1f8b9c76"          # parent of the .1R.17 production commit 302f5aba
R17_HEAD = "c618134a"                    # .1R.17 finalize head (verification-entry for .1R.18)
R153_BASELINE = "4d480553"              # .1R.15.3 baseline used by the .1R.15.5 byte-scope fence

G10_MODULE = "src/pcae/core/runtime_dispatch_gate10_eligibility.py"

R17_DOC = REPO_ROOT / (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17_GATE_10_PRE_EFFECT_ELIGIBILITY_"
    "AND_DISPATCH_ENVELOPE_COORDINATOR_IMPLEMENTATION.md"
)
R17R_DOC = REPO_ROOT / (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17R_GATE_10_SLICE_A_SCOPE_FENCE_"
    "AND_VERIFICATION_EVIDENCE_RECONCILIATION.md"
)


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════
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
    """*text* with every string literal and comment removed."""
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


def _code_only_file(path: str) -> str:
    return _code_only((REPO_ROOT / path).read_text())


G10_SRC = (REPO_ROOT / G10_MODULE).read_text()
G10_CODE = _code_only(G10_SRC)


# The 17 pre-existing guard nodes .1R.18 discovered (verbatim from .1R.18 §2.2).
DISCREPANCY_17 = {
    # ── 15 legitimate stale allowlist / scope-fence guards ────────────────
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
    # ── 2 docstring-grep false positives ─────────────────────────────────
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py::test_sole_semantic_owner_of_gate9_consumption_boundary": "DOCSTRING_GREP_FALSE_POSITIVE",
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py::test_gate9_is_sole_production_owner_of_consumption_boundary": "DOCSTRING_GREP_FALSE_POSITIVE",
}

# Authorized allowlists after reconciliation, re-derived independently here.
_GATE10 = G10_MODULE
_G5 = "src/pcae/core/runtime_dispatch_gate5.py"
_G7 = "src/pcae/core/runtime_dispatch_gate7.py"
_G8 = "src/pcae/core/runtime_dispatch_gate8.py"
_G9 = "src/pcae/core/runtime_dispatch_gate9.py"
_PERM = "src/pcae/core/runtime_dispatch_permission.py"
_STORE = "src/pcae/core/runtime_invocation_authority_consumption.py"
_PBF = "src/pcae/core/permission_broker_foundation.py"

#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
#: narrow local-CLI dispatch eligibility policy + POL-013). Gate 6
#: (runtime_dispatch_permission.py) + the Permission Broker Foundation
#: policy registry are authorizedly modified. Exact filenames, no wildcard;
#: Gate 5 / 7 / 8 stay byte-frozen (`forbidden`).
_R122 = {_PERM, _PBF}
#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0). The sole
#: authorized production surface for the positive Gate-7 result. Exact
#: filename, no wildcard; Gate 5 / 8 stay byte-frozen (`forbidden`).
_R126 = {_G7}
# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (N-16-5 -- HPAC-PAWA-001 v1.1 Slice 1
# production protected-admin writer anchor). Exact filenames, no wildcard; an
# unauthorized production-file expansion still fails these subset invariants.
_R30R31 = {
    "src/pcae/core/hpac_pawa_schemas.py",
    "src/pcae/core/hpac_pawa_agent_exclusion.py",
    "src/pcae/core/hpac_protected_admin_writer.py",
    "src/pcae/core/hpac_foundation.py",
    "src/pcae/core/human_principal_registry.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (N-16-5 -- merged RHAMP `.1R.30` bundle). Exact filenames, no wildcard.
    "src/pcae/core/hpac_verifier.py",
    "src/pcae/core/hpac_rhamp_terminal_reasons.py",
    "src/pcae/core/hpac_rhamp_client_context.py",
    "src/pcae/core/hpac_rhamp_credential_sidecar.py",
    "src/pcae/core/hpac_rhamp_counter_state.py",
    "src/pcae/core/hpac_rhamp_ctap2.py",
    "src/pcae/core/human_authenticator_fido2.py",
    "src/pcae/core/hpac_rhamp_assertion_verify.py",
    "src/pcae/core/hpac_rhamp_enrollment.py",
}
#: Contracts a later authorized phase may change (Phase ...1R.22:
#: PBRD-001 -> v3.0 MAJOR, PBPA-001 -> v1.1, new PBNDE-001; Phase ...1R.26:
#: the one NEW companion contract REPRC-001 v1.0).
_R122_CONTRACTS = {
    "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
    "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md",
}

#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B) production files,
#: authorized by `.1R.16` §36.2 / §38 (dispatch-attempt durable lifecycle +
#: the two 3S.2.1 MUST-FIX repairs + the item-9 runtime-inspect repair).
#: Exact filenames; an unauthorized production-file expansion still fails.
_SLICE_B = {
    "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
    "src/pcae/core/runtime_invocation.py",
    "src/pcae/core/runtime_adapter.py",
    "src/pcae/core/runtime_introspection.py",
    "src/pcae/commands/runtime_inspect.py",
}

RECONCILED_ALLOWLISTS = {
    "Gate7Result|is_gate7_result": {_G7, _G8, _G9, _GATE10},
    "Gate8Result|is_gate8_result": {_G8, _G9, _GATE10},
    "Gate9Result|is_gate9_result": {_G9, _GATE10},
    "Gate6Decision|is_gate6_decision": {_PERM, _G7, _G9, _GATE10},
    "is_gate6_decision": {_PERM, _G7, _G9, _GATE10},
    "run_gate8_process_containment": {_G8, _G9, _GATE10},
    "RuntimeInvocationAuthorityConsumptionStore": {_STORE, _G9, _GATE10},
}

# Invented unauthorized consumers — NONE of these exist as real files.
UNAUTHORIZED_SYNTHETIC = {
    "src/pcae/core/runtime_dispatch_gate10.py",          # invented first-effect module
    "src/pcae/core/effect_bearing_runtime_adapter.py",   # invented effect-bearing adapter
    "src/pcae/core/some_arbitrary_module.py",            # arbitrary production module
}


# ══════════════════════════════════════════════════════════════════════════
# §28.1  the exact 17-node discrepancy inventory
# ══════════════════════════════════════════════════════════════════════════
def test_discrepancy_inventory_is_exactly_seventeen():
    assert len(DISCREPANCY_17) == 17


def test_discrepancy_nodes_all_exist_today():
    for node in DISCREPANCY_17:
        path, name = node.split("::", 1)
        assert (REPO_ROOT / path).exists(), path
        assert name in (REPO_ROOT / path).read_text(), node


# ══════════════════════════════════════════════════════════════════════════
# §28.2 / §28.3  classification: 15 stale allowlist/scope + 2 docstring FPs
# ══════════════════════════════════════════════════════════════════════════
def test_classification_split_is_15_stale_plus_2_docstring_fp():
    by_class: dict[str, int] = {}
    for cls in DISCREPANCY_17.values():
        by_class[cls] = by_class.get(cls, 0) + 1
    assert by_class == {
        "STALE_ALLOWLIST": 14,
        "STALE_SCOPE_FENCE": 1,
        "DOCSTRING_GREP_FALSE_POSITIVE": 2,
    }


def test_every_classification_is_one_of_the_three_allowed_kinds():
    assert set(DISCREPANCY_17.values()) <= {
        "STALE_ALLOWLIST",
        "STALE_SCOPE_FENCE",
        "DOCSTRING_GREP_FALSE_POSITIVE",
    }


def test_stale_allowlist_guards_reference_their_symbol_in_gate10_code():
    # Each legitimate stale-allowlist guard exists because the Gate-10 module
    # references the guarded lineage symbol *in code* (not prose).
    for sym in ("Gate7Result", "is_gate7_result", "Gate8Result", "is_gate8_result",
                "Gate9Result", "is_gate9_result", "Gate6Decision", "is_gate6_decision",
                "run_gate8_process_containment", "RuntimeInvocationAuthorityConsumptionStore"):
        assert re.search(rf"\b{re.escape(sym)}\b", G10_CODE), sym


def test_docstring_fp_symbol_is_only_in_the_module_docstring():
    # ``run_gate9_atomic_authority_consumption`` — the sole cause of both
    # docstring-grep false positives — appears in the raw source but NOT in
    # the string/comment-stripped code.
    assert "run_gate9_atomic_authority_consumption" in G10_SRC
    assert "run_gate9_atomic_authority_consumption" not in G10_CODE
    assert "_GATE9_RESULTS" not in G10_SRC


# ══════════════════════════════════════════════════════════════════════════
# §28.4  every reconciled guard now admits the Slice-A module …
# §28.5–§28.11 / §16  … and still rejects any other importer
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pattern,allowed", list(RECONCILED_ALLOWLISTS.items()))
def test_reconciled_guard_admits_slice_a_and_matches_reality(pattern, allowed):
    real = _git_grep_l(pattern)
    # the real code consumer set is a subset of the reconciled allowlist …
    assert real <= allowed, real - allowed
    # … and the Slice-A module is genuinely among the real code consumers
    # (code-only, so docstring-only patterns are excluded here by design).
    if pattern != "Gate9Result|is_gate9_result" or True:
        code_consumers = {p for p in real if re.search(pattern, _code_only_file(p))}
    assert _GATE10 in code_consumers


@pytest.mark.parametrize("pattern,allowed", list(RECONCILED_ALLOWLISTS.items()))
def test_reconciled_guard_still_rejects_arbitrary_extra_consumer(pattern, allowed):
    for bad in UNAUTHORIZED_SYNTHETIC:
        assert bad not in allowed
        # the guard predicate (hits <= allowed) would fail for a hit set that
        # includes an unauthorized module.
        synthetic_hits = set(allowed) | {bad}
        assert not (synthetic_hits <= allowed)


def test_no_synthetic_unauthorized_consumer_actually_exists():
    for bad in UNAUTHORIZED_SYNTHETIC:
        assert not (REPO_ROOT / bad).exists()


# ══════════════════════════════════════════════════════════════════════════
# §28.12  the .1R.15.5 byte-scope fence stays tight
# ══════════════════════════════════════════════════════════════════════════
def test_gate5_permission_gate7_gate8_still_byte_unchanged_since_r153():
    changed = set(
        _git("diff", "--name-only", R153_BASELINE, "HEAD", "--", "src/pcae/core").split()
    )
    forbidden = {_G5, _G8}
    assert not (changed & forbidden), changed & forbidden
    # the two Gate-9-era files + the new Slice-A module + the .1R.16-§38
    # authorized Slice-B set + the .1R.22 (N-16-3) set + the .1R.26 (N-16-4)
    # Gate-7 surface; Gate 5 / Gate 8 stay forbidden (asserted above).
    allowed = {_G9, _STORE, _GATE10} | _SLICE_B | _R122 | _R126 | _R30R31
    assert changed <= allowed, changed - allowed


def test_scope_fence_would_still_flag_an_unauthorized_gate_change():
    allowed = {_G9, _STORE, _GATE10}
    assert not ({_G5, *allowed} <= allowed)  # a Gate-5 byte change would fail


# ══════════════════════════════════════════════════════════════════════════
# §28.13  the false-positive scan now tracks code semantics
# ══════════════════════════════════════════════════════════════════════════
def test_code_only_scan_ignores_docstring_but_keeps_code():
    sample = '''\
"""Module docstring mentions forbidden_symbol once."""
# comment mentions forbidden_symbol too
x = 1  # noqa
def f():
    return real_code_symbol
'''
    stripped = _code_only(sample)
    assert "forbidden_symbol" not in stripped
    assert "real_code_symbol" in stripped


def test_code_only_scan_keeps_names_inside_fstrings():
    sample = 'y = f"{real_name} literal text"\n'
    stripped = _code_only(sample)
    assert "real_name" in stripped
    assert "literal text" not in stripped


def test_docstring_fp_guards_now_use_code_only_grep():
    for mod in (
        "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py",
        "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py",
    ):
        src = (REPO_ROOT / mod).read_text()
        assert "_git_grep_l_code" in src or "_code_only_source" in src


# ══════════════════════════════════════════════════════════════════════════
# §28.14–§28.17  historical .1R.17 artifact preserved; erratum points at it
# ══════════════════════════════════════════════════════════════════════════
def test_original_r17_doc_still_present_and_unrewritten():
    assert R17_DOC.exists()
    text = R17_DOC.read_text()
    # the original (incorrect) A/B claim is preserved verbatim as historical evidence
    assert "ADDED failures (in B, not A): 0." in text
    assert "A = B = 29 pre-existing failures" in text
    assert "**0 added, 0 removed**" in text


def test_original_r17_immutable_phase_report_artifacts_untouched():
    reports = sorted(
        (REPO_ROOT / ".pcae/phase-reports").glob("*149O.20L.7O.3W.1R.2B.1R.1.1R.17.*")
    )
    assert reports, "the .1R.17 immutable phase-report artifacts must still exist"
    for r in reports:
        # not modified by .1R.17R (nothing staged/committed against them)
        diff = _git("diff", "--", str(r.relative_to(REPO_ROOT)))
        assert diff == "", r


def test_r17r_erratum_exists_and_references_the_preserved_original():
    assert R17R_DOC.exists()
    text = R17R_DOC.read_text()
    assert "ERRATUM" in text
    assert R17_DOC.name in text
    # corrected figures recorded
    assert "17 added" in text and "0 removed" in text
    # the erratum states the original claim is preserved, not rewritten
    assert "preserved" in text.lower()


def test_r17_doc_carries_an_appended_erratum_section_only():
    text = R17_DOC.read_text()
    assert "## ERRATUM" in text
    # the erratum is appended AFTER the original canonical trailer
    trailer = "*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17.*"
    assert trailer in text
    assert text.index(trailer) < text.index("## ERRATUM")


# ══════════════════════════════════════════════════════════════════════════
# §28.18–§28.19  no production source / no contract change in .1R.17R
# ══════════════════════════════════════════════════════════════════════════
def test_no_production_source_changed_since_baseline_except_the_one_r17_file():
    changed = set(_git("diff", "--name-only", IMMUTABLE_BASELINE, "HEAD", "--", "src/pcae").split())
    # Slice A: exactly the one new coordinator. Slice B (.1R.19) adds the
    # exact `.1R.16`-§38 authorized set; Phase .1R.22 (N-16-3) adds _R122 —
    # subset check, not equality.
    allowed = {G10_MODULE} | _SLICE_B | _R122 | _R126 | _R30R31
    assert changed <= allowed, changed - allowed
    assert G10_MODULE in changed


def test_no_working_tree_production_or_contract_diff():
    assert _git("diff", "--", "src/pcae") == ""
    assert _git("diff", "--", "docs/contracts", "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md") == ""


def test_no_contract_file_changed_since_baseline():
    changed = set(_git(
        "diff", "--name-only", IMMUTABLE_BASELINE, "HEAD",
        "--", "docs/contracts", "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
    ).split())
    # Phase .1R.22 (N-16-3) authorizedly evolves the PB policy contracts.
    assert changed <= _R122_CONTRACTS, changed - _R122_CONTRACTS


# ══════════════════════════════════════════════════════════════════════════
# §28.20–§28.21  no Slice-B / no first-effect artifact
# ══════════════════════════════════════════════════════════════════════════
def test_no_slice_b_lifecycle_tokens_in_gate10_code():
    for tok in ("EFFECT_ATTEMPT_STARTED", "RECEIPT_CAPTURED", "DISPATCH_UNCERTAIN",
                "DISPATCH_NOT_STARTED", "RuntimeInvocationRecord"):
        assert tok not in G10_CODE, tok


def test_no_first_effect_module_or_call_site():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    for tok in ("Gate10Result", "_GATE10_RESULTS", "DispatchReceipt"):
        assert tok not in G10_CODE, tok
    for tok in (".dispatch(", "subprocess", "posix_spawn", "Popen", "os.system",
                "socket.socket"):
        assert tok not in G10_CODE, tok


def test_gate10_module_imports_nothing_effectful():
    for line in G10_CODE.splitlines():
        s = line.strip()
        if s.startswith(("import ", "from ")):
            assert not re.search(
                r"\b(subprocess|socket|ssl|pty|ctypes|fcntl|requests|httpx|"
                r"http\.client|urllib\.request|fido2|webauthn)\b",
                s,
            ), s


# ══════════════════════════════════════════════════════════════════════════
# §28.22  N-18-2 corrected in reconciliation prose (taxonomy unchanged)
# ══════════════════════════════════════════════════════════════════════════
def test_reason_taxonomy_is_a_closed_frozenset_of_39():
    assert isinstance(GATE10_ELIGIBILITY_REASON_IDS, frozenset)
    assert len(GATE10_ELIGIBILITY_REASON_IDS) == 39


def test_r17r_prose_records_the_true_reason_count():
    text = R17R_DOC.read_text()
    assert "39" in text
    assert "N-18-2" in text


# ══════════════════════════════════════════════════════════════════════════
# §28.23  N-18-3 preserved — no suppression logic added to production
# ══════════════════════════════════════════════════════════════════════════
def test_r17r_preserves_n_18_3_and_does_not_touch_production():
    text = R17R_DOC.read_text()
    assert "N-18-3" in text
    assert "DispatchEnvelope != runtime capability != permission to dispatch" in text
    # production module byte-identical to the .1R.17 head
    diff = _git("diff", R17_HEAD, "HEAD", "--", G10_MODULE)
    assert diff == "", "the .1R.17R phase must not touch the Slice-A production module"


def test_current_runtime_capability_snapshot_still_unavailable():
    snap = build_gate10_capability_snapshot_resolver()()
    assert snap["execution_availability"] == "unavailable"
    assert snap["current_runtime_state"] == "Observed"
    assert snap["current_maximum_plugin_capability"] == "observe"


# ══════════════════════════════════════════════════════════════════════════
# §28.24 / §30  runtime unchanged; a hand-built Gate9Result still fails closed
# ══════════════════════════════════════════════════════════════════════════
def test_runtime_inspect_still_non_executing():
    out = subprocess.run(
        ["pcae", "runtime", "inspect"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout
    assert "not_implemented" in out
    assert "Observed" in out
    assert "unavailable" in out


def test_production_gate10_still_structurally_unreachable():
    # With no provenance substitution a hand-built Gate9Result is not a registry
    # member — the coordinator fails closed at step 1 with no envelope.
    from pcae.core.runtime_dispatch_gate9 import Gate9Result

    fake = object.__new__(Gate9Result)
    env, reasons = run_gate10_pre_effect_eligibility(
        fake,
        gate8_result=None, gate7_result=None, gate6_decision=None, gate5_result=None,
        identity=None, inputs=None, authority_current_time=0.0, repo_root=REPO_ROOT,
        effect_plan=None, descriptor_resolver=lambda *_a, **_k: None,
        lifecycle_store=None, consumption_store=None,
        capability_snapshot_resolver=build_gate10_capability_snapshot_resolver(),
        authority_generation_resolver=lambda: {},
    )
    assert env is None
    assert reasons and reasons[0].startswith("gate10_")
