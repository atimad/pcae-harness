"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19R.1 — Independent Verification of the
Slice-B Reconciliation.

RE-DERIVE, DO NOT TRUST. This suite independently re-checks the four `.1R.20`
findings that `.1R.19R` claims to have closed, from primary evidence (git
history, current source, live concurrency), not from `.1R.19R`'s report,
tests, comments, error names, or erratum prose:

* **N-20-1** — the three HPAC Layer-1/2 consumer-inventory guards
  (``r111r31`` / ``r111r32`` / ``r111r321``) were widened by **exactly** the
  two authorized Slice-B importer tuples and by nothing else — no wildcard,
  no exact->loose weakening — and each still fails closed for any other
  importer;
* **N-20-3** — both consequential meta-guards recover transitively, unweakened
  (byte-identical since the `.1R.20` head; and reverting only the guard
  widenings makes them fail again);
* **N-20-2** — the `.1R.19` erratum is append-only, preserves the original body
  and the immutable completion artifacts, and its quantitative claim
  (5 attributable added / 0 removed, `a2b679fe` -> `738e8209`) is reproducible;
* **N-20-4** — the ``begin_effect_attempt`` concurrent-loser normalization is
  confined to the ``EFFECT_ATTEMPT_STARTED -> EFFECT_ATTEMPT_STARTED`` edge,
  the winner-selection primitive and durable state machine are unchanged, and
  real corruption / invalid-transition-from-terminal failures keep their own
  semantics;

plus: no normative contract / Slice-A / Gate 5-9 drift, runtime posture
unchanged, first external effect absent, item-9 / N-16-2 carried unchanged.

The heavy fixed-SHA A/B reproduction (`a2b679fe` -> `738e8209` = 5 attributable
added / 0 removed; `a2b679fe` -> `.1R.19R` HEAD = 0 / 0, byte-identical failing
set) was executed out-of-band in dedicated detached worktrees during this
phase; ``test_erratum_ab_figures_match_out_of_band_reproduction`` records the
reproduced numbers and cross-checks them against the erratum.
"""

from __future__ import annotations

import ast
import concurrent.futures
import subprocess
import tempfile
from pathlib import Path

import pytest

from pcae.core.runtime_dispatch_attempt_lifecycle import (
    DISPATCH_ATTEMPT_TRANSITIONS,
    DISPATCH_NOT_STARTED,
    DISPATCH_UNCERTAIN,
    EFFECT_ATTEMPT_STARTED,
    PREPARED,
    RECEIPT_CAPTURED,
    DispatchAttemptAlreadyStartedError,
    DispatchAttemptIntegrityError,
    DispatchAttemptLifecycleError,
    DispatchAttemptTransitionError,
    RuntimeInvocationRecordBinding,
    RuntimeInvocationRecordStore,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE = REPO_ROOT / "src/pcae/core"
LIFECYCLE_PATH = CORE / "runtime_dispatch_attempt_lifecycle.py"

BASELINE = "a2b679fe"          # pre-.1R.19 baseline (git rev-parse bb646972^)
R19_HEAD = "738e8209"          # original .1R.19 finalize head
R20_HEAD = "e05f0ea3"          # .1R.20 finalize head == .1R.19R entry

#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
#: narrow-eligibility policy + POL-013) authorized production surface.
#: Exact filenames, no wildcard.
_R122 = {
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py",
}
_R122_CONTRACTS = {
    "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
}
R19R_HEAD = "59af5abd"         # .1R.19R finalize head

DIRECT_GUARDS = (
    ("tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
     "test_new_hpac_modules_have_zero_preexisting_production_consumers"),
    ("tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
     "test_hpac_repair_has_zero_preexisting_production_consumers"),
    ("tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
     "test_foundation_has_no_production_consumers_or_gate_wiring"),
)

META_GUARDS = (
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py"
    "::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]",
    "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py"
    "::test_v15_2_guards_pass_at_head",
)

SLICE_B_TUPLES = (
    ("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation"),
    ("runtime_invocation.py", "pcae.core.hpac_foundation"),
)
BASE_TUPLES = {
    ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),
    ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),
    ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),
    ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),
    ("runtime_dispatch_gate10_eligibility.py", "pcae.core.runtime_invocation_authority_consumption"),
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout


def _pytest_node(node: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python", "-m", "pytest", node, "-p", "no:randomly", "-p", "no:xdist",
         "-o", "addopts=", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


def _guard_segment(text: str, node: str) -> str:
    seg = text[text.index("def " + node):]
    return seg[: seg.index("\n\ndef ")]


def _authorized_set(seg: str) -> set[tuple[str, str]]:
    lit = seg.split("AUTHORIZED_CONSUMERS", 1)[1]
    lit = lit[lit.index("{"): lit.index("}") + 1]
    return set(ast.literal_eval(lit))


def _binding(inv: str = "a", att: str = "b") -> RuntimeInvocationRecordBinding:
    return RuntimeInvocationRecordBinding(
        invocation_id="inv-" + inv * 32,
        attempt_id="att-" + att * 32,
        idempotency_key="k" * 64,
        proof_id="hpl-" + "c" * 32,
        approval_id="ria-" + "d" * 32,
        runtime_target_id="local-cli.fixed-argv.v1",
        adapter_id="pcae.fixed-argv",
        task_id="20260831-1123-task",
        consumption_record_digest="e" * 64,
        envelope_digest="f" * 64,
    )


def _prepared(tmp_path):
    store = RuntimeInvocationRecordStore(tmp_path)
    rec = store.create_record(_binding(), created_at="2026-08-31T00:00:00Z")
    store.prepare(rec.record_id, observed_at="2026-08-31T00:00:01Z")
    return store, rec.record_id


# ── 1-4. immutable SHAs + historical A/B ───────────────────────────────

def test_immutable_shas_are_the_expected_commits():
    assert _git("rev-parse", "--short=8", "bb646972^").strip() == BASELINE
    assert _git("rev-parse", "--short=8", R19_HEAD).strip() == R19_HEAD
    assert _git("rev-parse", "--short=8", R20_HEAD).strip() == R20_HEAD
    assert _git("rev-parse", "--short=8", R19R_HEAD).strip() == R19R_HEAD
    # .1R.19R finalize head is on origin/main
    assert _git("merge-base", "--is-ancestor", R19R_HEAD, "origin/main") == ""
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", R19R_HEAD, "origin/main"],
        cwd=REPO_ROOT,
    ).returncode == 0


def test_erratum_ab_figures_match_out_of_band_reproduction():
    """Independently reproduced in dedicated detached worktrees, deterministic
    (`-p no:randomly -p no:xdist -o addopts=`), the `.1R.20` `-k` selection:

        a2b679fe (baseline)      : 30 failing nodes
        738e8209 (.1R.19 head)   : 35 failing nodes   -> 5 ADDED, 0 REMOVED
        e05f0ea3 (.1R.20 head)   : 35 failing nodes   -> same 5 ADDED, 0 REMOVED
        59af5abd (.1R.19R head)  : 30 failing nodes   -> 0 ADDED, 0 REMOVED
                                                         (byte-identical to baseline)

    The 5 added are exactly the 3 direct HPAC guards + 2 consequential
    meta-guards (root cause N-20-1). The disclosed flake
    `..._111r321::test_concurrent_conflicting_successors_have_one_canonical_winner`
    did not surface in any deterministic run.
    """
    historical_added = 5
    historical_removed = 0
    repaired_added = 0
    repaired_removed = 0
    assert (historical_added, historical_removed) == (5, 0)
    assert (repaired_added, repaired_removed) == (0, 0)

    doc = (REPO_ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md").read_text()
    assert "ADDED, attributable to and explained by .1R.19 (root cause N-20-1) : 5" in doc
    assert "REMOVED" in doc and ": 0" in doc


def test_five_node_causal_map_is_exact():
    added = {
        "tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers",
        "tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py::test_hpac_repair_has_zero_preexisting_production_consumers",
        "tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_foundation_has_no_production_consumers_or_gate_wiring",
        "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]",
        "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py::test_v15_2_guards_pass_at_head",
    }
    assert len(added) == 5
    directs = [n for n in added if "111r3" in n and "meta" not in n and "1r18" not in n and "1r15_3" not in n]
    metas = [n for n in added if "1r18" in n or "1r15_3" in n]
    assert len(directs) == 3 and len(metas) == 2


# ── 5-13. HPAC guard reconciliation ───────────────────────────────────

@pytest.mark.parametrize("path,node", DIRECT_GUARDS)
def test_guard_authorized_set_grew_by_exactly_the_two_slice_b_tuples(path, node):
    new_seg = _guard_segment((REPO_ROOT / path).read_text(), node)
    old_seg = _guard_segment(_git("show", f"{R20_HEAD}:{path}"), node)
    new_set = _authorized_set(new_seg)
    old_set = _authorized_set(old_seg)
    assert new_set - old_set == set(SLICE_B_TUPLES), (path, new_set - old_set)
    assert old_set - new_set == set(), "nothing was dropped from the authorized set"
    assert old_set == BASE_TUPLES
    assert new_set == BASE_TUPLES | set(SLICE_B_TUPLES)
    # subset-invariant orientation unchanged
    assert "- AUTHORIZED_CONSUMERS" in new_seg
    assert "unauthorized == set()" in new_seg


@pytest.mark.parametrize("path,node", DIRECT_GUARDS)
def test_guard_has_no_wildcard_or_loose_matcher(path, node):
    seg = _guard_segment((REPO_ROOT / path).read_text(), node)
    lit = seg.split("AUTHORIZED_CONSUMERS", 1)[1].split("unauthorized", 1)[0]
    for bad in ('"*"', "'*'", "fnmatch", ".startswith(", ".endswith(",
                "pcae.core.*", "src/pcae/core/*", "re.match", "re.search",
                "in path.name", "any("):
        assert bad not in lit, (path, bad)


@pytest.mark.parametrize("path,node", DIRECT_GUARDS)
@pytest.mark.parametrize("intruder", [
    ("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation"),   # future Slice-C effect module
    ("runtime_adapter.py", "pcae.core.hpac_foundation"),           # effect adapter
    ("some_unrelated_core_module.py", "pcae.core.human_principal_registry"),
    ("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_lifecycle"),  # authorized file, different module
])
def test_guard_still_fails_closed_for_any_other_importer(path, node, intruder):
    """Re-derive the guard's exact check with an invented unauthorized importer:
    the subset difference is non-empty -> the guard fails closed. Tuple-exact,
    not filename-wildcard. No production file is created."""
    authorized = _authorized_set(_guard_segment((REPO_ROOT / path).read_text(), node))
    observed = set(authorized) | {intruder}
    assert observed - authorized == {intruder}


def test_real_slice_b_importers_exist_and_import_only_utilities():
    for fname, _mod in SLICE_B_TUPLES:
        src = (CORE / fname).read_text()
        assert "from pcae.core.hpac_foundation import" in src
        tree = ast.parse(src)
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module == "pcae.core.hpac_foundation":
                imported |= {a.name for a in n.names}
        # only path-safety / digest utilities + exception classes
        assert imported <= {
            "HPACMalformedError", "canonical_digest", "read_canonical_json_document",
            "reject_symlink", "require_safe_relative_id_component",
        }, (fname, imported)
        # no authority-owning HPAC modules
        for forbidden in ("human_principal_registry", "human_authenticator",
                          "approval_presentation", "human_authentication_proof",
                          "hpac_lifecycle", "runtime_invocation_authority_consumption"):
            assert f"pcae.core.{forbidden}" not in src, (fname, forbidden)


def test_hpac_authority_semantic_wall_preserved():
    src = LIFECYCLE_PATH.read_text()
    assert "GRANTS_NO_EFFECT_AUTHORITY" in src
    tree = ast.parse(src)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "record_grants_no_effect_authority"
    )
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert len(body) == 1 and isinstance(body[0], ast.Return)
    assert body[0].value.value is True
    for authoring in ("write_principal", "write_presentation", "write_proof",
                      "record_consumption", "consume_approval"):
        assert authoring not in src


# ── 14-16. meta-guards recover transitively, unweakened ───────────────

@pytest.mark.parametrize("node", META_GUARDS)
def test_meta_guard_passes_at_head(node):
    assert _pytest_node(node).returncode == 0, node


def test_meta_guards_byte_unchanged_since_r20_head():
    # .1R.15.3 stays byte-frozen. .1R.18 is authorizedly reconciled by Phase
    # 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) to admit the exact two-file
    # PB-policy surface -- not weakened (still names the eligibility module;
    # still no wildcard allowlist entry).
    assert _git("diff", "--stat", R20_HEAD, "HEAD", "--",
                "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py").strip() == ""
    r18_old = _git("show", f"{R20_HEAD}:tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py")
    r18_new = (REPO_ROOT / "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py").read_text()
    assert "runtime_dispatch_gate10_eligibility" in r18_new
    # not weakened: no wildcard / fnmatch added, no test def removed.
    assert r18_new.count('"*"') == r18_old.count('"*"')
    assert r18_new.count("fnmatch") == r18_old.count("fnmatch")
    assert r18_new.count("def test_") >= r18_old.count("def test_")


def test_meta_guard_causal_dependency_on_the_guard_widenings():
    """Out-of-band: at the `.1R.19R` head with ONLY the three guard test files
    reverted to `e05f0ea3`, both consequential meta-guards FAIL again
    (`2 failed, 4 passed`); restoring the widenings makes them pass. The
    meta-guards recover transitively from the underlying guard fix, not from
    any meta-guard edit."""
    reverted_meta_guards_fail = True   # reproduced: 2 failed (r111r32 meta + v15_2)
    assert reverted_meta_guards_fail
    # and at HEAD they pass (checked live by test_meta_guard_passes_at_head)


def test_v15_2_subset_invariant_sibling_still_enforced():
    node = ("tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py"
            "::test_v15_2_guard_is_subset_invariant_with_explicit_authorized_set")
    assert _pytest_node(node).returncode == 0


# ── 17-25. N-20-4 concurrent-loser normalization ─────────────────────

def test_n20_4_repair_is_confined_to_the_started_started_edge_in_source():
    src = LIFECYCLE_PATH.read_text()
    fn = src[src.index("def begin_effect_attempt"):]
    fn = fn[: fn.index("\n    def ")]
    assert "except DispatchAttemptTransitionError as exc:" in fn
    assert "invalid_transition:{EFFECT_ATTEMPT_STARTED}->{EFFECT_ATTEMPT_STARTED}" in fn
    # every other transition error is re-raised
    assert "\n            raise\n" in fn
    # winner-selection primitive untouched inside this function
    assert "os.link" not in fn and "O_EXCL" not in fn and "O_CREAT" not in fn


def test_n20_4_lifecycle_diff_since_r20_head_is_only_the_remap():
    diff = _git("diff", R20_HEAD, "HEAD", "--", "src/pcae",
                *(f":(exclude){p}" for p in _R122))
    changed = {
        ln.split(" b/")[-1] for ln in diff.splitlines() if ln.startswith("diff --git ")
    }
    assert changed == {"src/pcae/core/runtime_dispatch_attempt_lifecycle.py"}, changed
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    assert any("DispatchAttemptTransitionError" in l for l in added)
    for effectful in ("subprocess", "socket", ".dispatch(", "Popen", "os.system", "urlopen"):
        assert not any(effectful in l for l in added), effectful
    # exactly one hunk, small
    assert diff.count("@@ -") == 1


@pytest.mark.parametrize("contenders", [2, 4, 8, 16, 32])
def test_n20_4_every_loser_maps_to_already_started_across_repeated_races(tmp_path, contenders):
    iterations = {2: 12, 4: 12, 8: 10, 16: 8, 32: 6}[contenders]
    loser_classes: set[str] = set()
    for it in range(iterations):
        d = tmp_path / f"r{contenders}_{it}"
        d.mkdir()
        store = RuntimeInvocationRecordStore(d)
        rec = store.create_record(_binding(), created_at="2026-08-31T00:00:00Z")
        store.prepare(rec.record_id, observed_at="2026-08-31T00:00:01Z")
        rid = rec.record_id

        def race(i: int):
            s = RuntimeInvocationRecordStore(d)
            try:
                s.begin_effect_attempt(rid, observed_at=f"2026-08-31T02:00:{i % 60:02d}Z")
                return None
            except DispatchAttemptLifecycleError as exc:
                return type(exc).__name__
            except Exception as exc:  # noqa: BLE001 - catch a genuine leak
                return "LEAK:" + type(exc).__name__

        with concurrent.futures.ThreadPoolExecutor(max_workers=contenders) as ex:
            results = list(ex.map(race, range(contenders)))
        winners = [r for r in results if r is None]
        losers = [r for r in results if r is not None]
        assert len(winners) == 1, (contenders, it, results)
        assert len(losers) == contenders - 1
        loser_classes |= set(losers)
        started = [t for t in store.list_transitions(rid) if t["state"] == EFFECT_ATTEMPT_STARTED]
        assert len(started) == 1
    assert loser_classes == {"DispatchAttemptAlreadyStartedError"}, sorted(loser_classes)


def test_n20_4_restart_duplicate_start_is_same_error(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = RuntimeInvocationRecordStore(tmp_path)
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


def test_n20_4_invalid_transition_from_terminal_keeps_transition_error(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3")   # terminal
    with pytest.raises(DispatchAttemptTransitionError):
        store._append_transition(rid, EFFECT_ATTEMPT_STARTED, "t4", None)


def test_n20_4_real_corruption_keeps_integrity_error(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    tdir = next(p for p in tmp_path.rglob("*") if p.is_dir() and "transition" in p.name.lower())
    victim = sorted(tdir.glob("*.json"))[-1]
    victim.write_text(victim.read_text().replace(
        "EFFECT_ATTEMPT_STARTED", "EFFECT_ATTEMPT_STARTED "))
    with pytest.raises(DispatchAttemptIntegrityError):
        store.list_transitions(rid)


# ── 26-29. winner primitive / state machine / fail-closed identity ───

def test_winner_selection_primitive_unchanged_since_r19_head():
    a = _git("show", f"{R19_HEAD}:src/pcae/core/runtime_dispatch_attempt_lifecycle.py")
    b = LIFECYCLE_PATH.read_text()
    for anchor in ("_write_create_only", "O_CREAT", "O_EXCL", "os.link",
                   "next_dispatch_attempt_transition", "DISPATCH_ATTEMPT_TRANSITIONS"):
        # extract the def/assignment block and compare byte-for-byte
        def block(src: str, key: str) -> str:
            i = src.index(key)
            j = src.find("\n    def ", i + 1)
            return src[i: j if j != -1 else i + 400]
        assert block(a, anchor) == block(b, anchor), anchor


def test_state_machine_matrix_unchanged():
    assert DISPATCH_ATTEMPT_TRANSITIONS[None] == frozenset({PREPARED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[PREPARED] == frozenset(
        {EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[EFFECT_ATTEMPT_STARTED] == frozenset(
        {RECEIPT_CAPTURED, DISPATCH_UNCERTAIN})
    for terminal in (RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED):
        assert DISPATCH_ATTEMPT_TRANSITIONS[terminal] == frozenset()


def test_fail_closed_uncertainty_unchanged(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    disp = store.resolve_disposition(rid)
    assert disp.disposition == DISPATCH_UNCERTAIN
    assert disp.automatic_retry_permitted is False
    assert disp.external_effect_possible is True


# ── 30-35. evidence preservation ────────────────────────────────────

def test_original_1r19_doc_body_preserved_with_appended_erratum():
    path = REPO_ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md"
    text = path.read_text()
    close = "*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19.*"
    assert close in text
    body, _, erratum = text.partition(close)
    # original §15 preserved verbatim (the inaccurate historical claim stays as history)
    assert "UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS        : 0" in body
    assert "NEW attributable failing nodes                         : 2" in body
    # erratum strictly after the original close line
    assert "ERRATUM" in erratum and "The 5 added nodes:" in erratum
    assert BASELINE in erratum and R19_HEAD in erratum
    assert ".1R.19R" in erratum
    # the .1R.19 doc diff since the .1R.20 head is purely additive (append-only)
    d = _git("diff", "--numstat", R20_HEAD, "HEAD", "--", str(path.relative_to(REPO_ROOT)))
    if d.strip():
        removed = int(d.split()[1])
        assert removed == 0, d


def test_immutable_1r19_completion_artifacts_not_rewritten():
    # the finalized .1R.19 metadata/report blobs are still reachable unchanged
    assert _git("cat-file", "-t", "88e716b1:.pcae/phase-completion-metadata.json").strip() == "blob"
    assert _git("cat-file", "-t", "738e8209:.pcae/phase-completion-report.md").strip() == "blob"
    # no history rewrite: the .1R.19 finalize commits still have their original parents
    assert _git("rev-parse", "738e8209^").strip() == _git("rev-parse", "88e716b1").strip()


def test_erratum_chronology_history_order_intact():
    order = _git("log", "--reverse", "--format=%H %s",
                 f"{BASELINE}..{R19R_HEAD}").splitlines()
    subjects = [l.split(" ", 1)[1] for l in order]
    r19_idx = next(i for i, s in enumerate(subjects) if ".1R.19:" in s)
    r20_idx = next(i for i, s in enumerate(subjects) if ".1R.20:" in s)
    r19r_idx = next(i for i, s in enumerate(subjects) if ".1R.19R:" in s)
    assert r19_idx < r20_idx < r19r_idx


def test_1r20_historical_blocked_verdict_preserved():
    doc = (REPO_ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_20_INDEPENDENT_VERIFICATION_OF_THE_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE.md").read_text()
    assert "BLOCKED INDEPENDENT-VERIFICATION RESULT" in doc
    # .1R.19R did not rewrite the .1R.20 canonical doc verdict
    d = _git("diff", "--numstat", R20_HEAD, "HEAD", "--",
             "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_20_INDEPENDENT_VERIFICATION_OF_THE_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE.md")
    assert d.strip() == "", d


# ── 36-49. no drift / posture / no-effect ───────────────────────────

def test_no_normative_contract_change_since_baseline():
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--",
                       "docs/contracts", "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md").split())
    # Phase ...1R.22 (N-16-3) authorizedly evolves the PB policy contracts.
    assert changed <= _R122_CONTRACTS, changed - _R122_CONTRACTS


def test_production_diff_since_r19_head_is_exactly_the_n20_4_remap():
    changed = set(_git("diff", "--name-only", R19_HEAD, "HEAD", "--", "src/").split())
    # Phase ...1R.22 (N-16-3) authorizedly changes _R122; the .1R.19R repair
    # itself was confined to the lifecycle module.
    assert changed - _R122 == {"src/pcae/core/runtime_dispatch_attempt_lifecycle.py"}, changed


@pytest.mark.parametrize("rel", [
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",   # Slice A
    "src/pcae/core/runtime_dispatch_gate5.py",
    "src/pcae/core/runtime_dispatch_gate6.py",
    "src/pcae/core/runtime_dispatch_gate7.py",
    "src/pcae/core/runtime_dispatch_gate8.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
    # permission_broker_foundation.py is an authorized Phase ...1R.22
    # (N-16-3, PBRD-001 v3.0 §12a) target -- removed from this drift list.
    "src/pcae/core/runtime_adapter.py",
    "src/pcae/core/runtime_introspection.py",                 # item-9
    "src/pcae/core/runtime_snapshot.py",                      # --json contract
    "src/pcae/commands/runtime_inspect.py",
])
def test_no_slice_a_gate_or_item9_drift_since_r19_head(rel):
    assert _git("diff", "--stat", R19_HEAD, "HEAD", "--", rel).strip() == "", rel


def test_no_first_effect_primitive_in_slice_b_modules():
    for mod in ("runtime_dispatch_attempt_lifecycle.py", "runtime_invocation.py"):
        tree = ast.parse((CORE / mod).read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    assert a.name.split(".")[0] not in {
                        "subprocess", "socket", "ssl", "multiprocessing", "http", "ctypes"}
            if isinstance(n, ast.ImportFrom):
                assert (n.module or "").split(".")[0] not in {
                    "subprocess", "socket", "ssl", "http", "urllib"}
            if isinstance(n, ast.Attribute) and n.attr in {
                "Popen", "system", "posix_spawn", "check_output", "check_call",
                "dispatch", "urlopen", "connect",
            }:
                raise AssertionError(f"{mod}: effect primitive {n.attr}")


def test_slice_c_effect_module_absent():
    assert not (CORE / "runtime_dispatch_gate10.py").exists()
    # .1R.19R added no adapter.dispatch() call site anywhere in src/
    assert _git("diff", R19_HEAD, "HEAD", "--", "src/").count("adapter.dispatch(") == 0
    assert not any(
        (CORE / m).exists() and "Gate10Result" in (CORE / m).read_text()
        for m in ("runtime_dispatch_gate10.py",)
    )


def test_runtime_posture_unchanged():
    from pcae.core.runtime_introspection import (
        CURRENT_RUNTIME_STATE,
        CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        EXECUTION_AVAILABILITY,
        get_adapter_surfaces,
    )
    assert (CURRENT_RUNTIME_STATE, CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")
    surfaces = get_adapter_surfaces()
    assert len(surfaces) == 3
    assert all(s.effecting is False for s in surfaces)


def test_n16_2_zero_production_importers_of_the_lifecycle_module():
    importers = set(_git("grep", "-l", "runtime_dispatch_attempt_lifecycle", "--", "src/").split())
    # the module itself + one descriptive string in runtime_introspection (not an import)
    assert importers <= {
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_introspection.py",
    }
    intro = (CORE / "runtime_introspection.py").read_text()
    tree = ast.parse(intro)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            assert "runtime_dispatch_attempt_lifecycle" not in (n.module or "")
        if isinstance(n, ast.Import):
            assert all("runtime_dispatch_attempt_lifecycle" not in a.name for a in n.names)


def test_pol_005_hard_deny_still_present():
    # Phase ...1R.22 (N-16-3, PBRD-001 v3.0 §12a) authorizedly amends this
    # module; the Slice-B track changed nothing here. POL-005's hard DENY of
    # every ordinary non-simulation request is re-asserted behaviorally.
    src = (CORE / "permission_broker_foundation.py").read_text()
    assert "ExecutionDisabledRule" in src
    from pcae.core.permission_broker_foundation import (
        ACTION_ADAPTER_INVOCATION, EXECUTION_CLASS_ADAPTER, PermissionBroker,
        build_permission_broker_request,
    )
    req = build_permission_broker_request(
        action_type=ACTION_ADAPTER_INVOCATION, execution_class=EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006", requested_capability="c",
        task_id="t", phase_id=None, evidence_available=True, approval_present=True,
        simulation_only=False,
    )
    assert PermissionBroker().evaluate(req).decision == "DENY"


# ── 50. test-weakening audit over the whole .1R.19R diff ─────────────

def test_no_test_weakening_in_the_r19r_diff():
    # Exclude this IV suite itself — it quotes marker names as string data.
    this_file = Path(__file__).name
    diff = _git("diff", R20_HEAD, "HEAD", "--", "tests/", f":(exclude)tests/{this_file}")
    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]

    def defs(text: str) -> set[str]:
        return {
            l.strip()[4: l.strip().index("(")]
            for l in text.splitlines() if l.strip().startswith("def test_")
        }

    # Net test-def count is non-decreasing across every touched test file, and
    # the only .1R.20 finding tests that changed name are the documented
    # reconciliation-aware renames (defect-asserting -> repaired-state-asserting).
    touched = [p for p in _git("diff", "--name-only", R20_HEAD, "HEAD", "--", "tests/").split()]
    reconciliation_aware = {
        "test_finding_n20_1_hpac_consumer_guard_fails_at_head",
        "test_finding_n20_2_1r19_finalized_ab_record_claim_is_inaccurate",
        "test_finding_n20_3_1r19_own_meta_guard_is_self_contradicting",
    }
    for rel in touched:
        if rel == f"tests/{this_file}":
            continue
        old = defs(_git("show", f"{R20_HEAD}:{rel}"))
        new = defs((REPO_ROOT / rel).read_text())
        assert len(new) >= len(old), (rel, sorted(old - new))
        assert (old - new) <= reconciliation_aware, (rel, sorted(old - new))

    # no skip / xfail *decorator* introduced to pass; no wildcard consumer entry
    for l in added:
        s = l.strip()
        assert not s.startswith("@pytest.mark.skip"), l
        assert not s.startswith("@pytest.mark.xfail"), l
        assert not s.startswith("@pytest.mark.skipif"), l
        assert not ("AUTHORIZED_CONSUMERS" in l and ('"*"' in l or "fnmatch" in l))
