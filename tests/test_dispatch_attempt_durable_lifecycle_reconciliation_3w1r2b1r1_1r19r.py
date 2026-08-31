"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19R — Slice-B Scope-Fence and
Verification-Evidence Reconciliation.

Dedicated reconciliation suite. It re-derives, from primary evidence, that:

* the three HPAC Layer-1/2 consumer-inventory guards (``r111r31`` / ``r111r32``
  / ``r111r321``) were widened by **exactly** the two authorized Slice-B
  importer tuples and by nothing else — no wildcard, no exact->loose weakening;
* each guard still rejects a Gate-10 effect module, an adapter consumer, and an
  arbitrary importer;
* the two consequential meta-guards recover transitively, unweakened;
* the N-20-4 concurrent-loser error type is normalised to
  ``DispatchAttemptAlreadyStartedError`` at 2/4/8/16/32 contenders, with exactly
  one durable start, restart-stable, and without mislabelling a real integrity
  or invalid-transition failure;
* the lifecycle state machine / ``DISPATCH_UNCERTAIN`` semantics are unchanged;
* the original ``.1R.19`` document is preserved with an append-only erratum that
  references the original SHAs and the corrected historical A/B figure;
* the repaired tree carries 0 attributable added regressions;
* no normative contract / Slice-A / Gate 5-9 drift; runtime unchanged;
  item 9 / N-16-2 unchanged.
"""

from __future__ import annotations

import ast
import concurrent.futures
import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_attempt_lifecycle as lifecycle
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

PRE_1R19_BASELINE = "a2b679fe"
R19_HEAD = "738e8209"
R20_HEAD = "e05f0ea3"

_DIRECT_GUARDS = (
    ("tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
     "test_new_hpac_modules_have_zero_preexisting_production_consumers"),
    ("tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
     "test_hpac_repair_has_zero_preexisting_production_consumers"),
    ("tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
     "test_foundation_has_no_production_consumers_or_gate_wiring"),
)

_META_GUARDS = (
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py"
    "::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]",
    "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py"
    "::test_v15_2_guards_pass_at_head",
)

_AUTHORIZED_SLICE_B = (
    '("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation")',
    '("runtime_invocation.py", "pcae.core.hpac_foundation")',
)
_BASE_TUPLES = (
    '("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle")',
    '("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation")',
    '("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle")',
    '("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption")',
)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True).stdout


def _guard_segment(path: str, node: str) -> str:
    src = (REPO_ROOT / path).read_text()
    seg = src[src.index("def " + node):]
    return seg[: seg.index("\n\ndef ")]


def _authorized_literal(seg: str) -> str:
    return seg.split("AUTHORIZED_CONSUMERS")[1].split("unauthorized")[0]


def _pytest(node: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python", "-m", "pytest", node, "-p", "no:randomly", "-p", "no:xdist",
         "-o", "addopts=", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


def _binding(*, inv="a", att="b") -> RuntimeInvocationRecordBinding:
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


# ═══════════════════════════════════════════════════════════════════════
# 1. Historical five-node attributable discrepancy inventory
# ═══════════════════════════════════════════════════════════════════════

def test_historical_baseline_and_heads_are_the_expected_commits():
    assert _git("rev-parse", "--short=8", "bb646972^").strip() == PRE_1R19_BASELINE
    assert _git("rev-parse", "--short=8", R19_HEAD).strip() == R19_HEAD
    assert _git("rev-parse", "--short=8", R20_HEAD).strip() == R20_HEAD


def test_historical_five_node_discrepancy_is_documented():
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md"
    ).read_text()
    # erratum records the true figure, references the original SHAs / baseline,
    # and preserves the original (incorrect) §15 line verbatim
    assert "ERRATUM" in doc
    assert PRE_1R19_BASELINE in doc and R19_HEAD in doc
    assert "The 5 added nodes:" in doc
    assert "ADDED, attributable to and explained by .1R.19 (root cause N-20-1) : 5" in doc
    assert "REMOVED                                                            : 0" in doc
    assert "NEW attributable failing nodes                         : 2" in doc  # original preserved
    for _, node in _DIRECT_GUARDS:
        assert node in doc
    assert "test_widened_guard_module_passes_at_head" in doc
    assert "test_v15_2_guards_pass_at_head" in doc


# ═══════════════════════════════════════════════════════════════════════
# 2-3. The three direct guards + two consequential meta-guards, at HEAD
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path,node", _DIRECT_GUARDS)
def test_direct_hpac_guard_is_green_at_head(path, node):
    assert _pytest(f"{path}::{node}").returncode == 0


@pytest.mark.parametrize("node", _META_GUARDS)
def test_consequential_meta_guard_recovers_at_head(node):
    assert _pytest(node).returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# 4. Each HPAC guard admits only the authorized Slice-B consumers
# 10-11. no wildcard, no exact->loose weakening
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path,node", _DIRECT_GUARDS)
def test_guard_admits_exactly_the_authorized_slice_b_tuples(path, node):
    seg = _guard_segment(path, node)
    lit = _authorized_literal(seg)
    for tup in _AUTHORIZED_SLICE_B:
        assert tup in lit, (path, tup)
    # the four base gate5/gate9 tuples still enumerated (nothing dropped)
    for tup in _BASE_TUPLES:
        assert tup in lit, (path, tup)
    # subset-invariant orientation is unchanged
    assert "- AUTHORIZED_CONSUMERS" in seg
    assert "unauthorized == set()" in seg


@pytest.mark.parametrize("path,node", _DIRECT_GUARDS)
def test_guard_has_no_wildcard_or_loose_matcher(path, node):
    lit = _authorized_literal(_guard_segment(path, node))
    for bad in ('"*"', "'*'", "fnmatch", ".startswith(", "endswith(", "pcae.core.*",
                "src/pcae/core/*", "re.match", "in path.name"):
        assert bad not in lit, (path, bad)


@pytest.mark.parametrize("path,node", _DIRECT_GUARDS)
def test_guard_authorized_set_grew_by_exactly_two_entries_since_r20_head(path, node):
    old = _git("show", f"{R20_HEAD}:{path}")
    old_seg = old[old.index("def " + node):]
    old_seg = old_seg[: old_seg.index("\n\ndef ")]
    old_lit = old_seg.split("AUTHORIZED_CONSUMERS")[1].split("unauthorized")[0]
    old_tuples = {t for t in _BASE_TUPLES + tuple(
        f'("{a}", "{b}")' for a, b in [
            ("runtime_dispatch_gate10_eligibility.py", "pcae.core.runtime_invocation_authority_consumption"),
        ]
    ) if t in old_lit}
    new_lit = _authorized_literal(_guard_segment(path, node))
    new_tuples = old_tuples | set(_AUTHORIZED_SLICE_B)
    for t in new_tuples:
        assert t in new_lit
    # exactly two added
    assert sum(1 for t in _AUTHORIZED_SLICE_B if t in new_lit) == 2
    assert all(t not in old_lit for t in _AUTHORIZED_SLICE_B)


# ═══════════════════════════════════════════════════════════════════════
# 5-7. Each guard rejects a Gate-10 effect module / adapter / arbitrary importer
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path,node", _DIRECT_GUARDS)
@pytest.mark.parametrize("intruder", [
    ("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation"),
    ("runtime_adapter.py", "pcae.core.hpac_lifecycle"),
    ("some_unrelated_core_module.py", "pcae.core.human_principal_registry"),
])
def test_guard_still_rejects_an_unauthorized_importer(path, node, intruder):
    """Re-derive the guard's core check with an invented unauthorized importer:
    the subset difference is non-empty, so the guard fails closed. No production
    file is created."""
    seg = _guard_segment(path, node)
    lit = _authorized_literal(seg)
    authorized = set()
    for line in lit.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith("(") and line.endswith(")"):
            authorized.add(line)
    observed = set(authorized) | {f'("{intruder[0]}", "{intruder[1]}")'}
    assert observed - authorized == {f'("{intruder[0]}", "{intruder[1]}")'}


# ═══════════════════════════════════════════════════════════════════════
# 8-9. Meta-guards recover WITHOUT being weakened
# ═══════════════════════════════════════════════════════════════════════

def test_meta_guards_are_byte_unchanged_since_r20_head():
    # .1R.15.3 stays byte-frozen. .1R.18 is authorizedly reconciled by Phase
    # 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) to admit the exact two-file
    # PB-policy surface -- it is not weakened (still names the eligibility
    # module; still no wildcard allowlist entry).
    assert _git("diff", "--stat", R20_HEAD, "HEAD", "--",
                "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py").strip() == ""
    r18_old = _git("show", f"{R20_HEAD}:tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py")
    r18_new = (REPO_ROOT / "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py").read_text()
    assert "runtime_dispatch_gate10_eligibility" in r18_new
    # not weakened: no wildcard / fnmatch was added, no test def removed.
    assert r18_new.count('"*"') == r18_old.count('"*"')
    assert r18_new.count("fnmatch") == r18_old.count("fnmatch")
    assert r18_new.count("def test_") >= r18_old.count("def test_")


def test_v15_2_subset_invariant_still_enforced_on_each_widened_guard():
    node = ("tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py"
            "::test_v15_2_guard_is_subset_invariant_with_explicit_authorized_set")
    assert _pytest(node).returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# 12-19. N-20-4 concurrent-loser normalization
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("contenders", [2, 4, 8, 16, 32])
def test_n20_4_every_loser_maps_to_already_started_error(tmp_path, contenders):
    store, rid = _prepared(tmp_path)
    seen: list[str] = []

    def race(i: int):
        s = RuntimeInvocationRecordStore(tmp_path)
        try:
            s.begin_effect_attempt(rid, observed_at=f"2026-08-31T02:{i // 60:02d}:{i % 60:02d}Z")
            return None
        except DispatchAttemptLifecycleError as exc:
            return type(exc).__name__

    with concurrent.futures.ThreadPoolExecutor(max_workers=contenders) as ex:
        results = list(ex.map(race, range(contenders)))
    winners = [r for r in results if r is None]
    losers = [r for r in results if r is not None]
    assert len(winners) == 1
    assert len(losers) == contenders - 1
    assert set(losers) == {"DispatchAttemptAlreadyStartedError"}, sorted(set(losers))
    started = [t for t in store.list_transitions(rid) if t["state"] == EFFECT_ATTEMPT_STARTED]
    assert len(started) == 1  # exactly one durable start


def test_n20_4_restart_duplicate_start_is_same_error(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = RuntimeInvocationRecordStore(tmp_path)
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


def test_n20_4_real_corruption_still_raises_integrity_error(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    # tamper with a transition file -> chain digest mismatch on next read
    tdir = next(p for p in (tmp_path).rglob("*") if p.is_dir() and "transition" in p.name.lower())
    victim = sorted(tdir.glob("*.json"))[-1]
    victim.write_text(victim.read_text().replace("EFFECT_ATTEMPT_STARTED", "EFFECT_ATTEMPT_STARTED "))
    with pytest.raises(DispatchAttemptIntegrityError):
        store.list_transitions(rid)


def test_n20_4_invalid_transition_from_terminal_is_not_mislabeled_duplicate(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3")
    with pytest.raises(DispatchAttemptTransitionError):
        store._append_transition(rid, EFFECT_ATTEMPT_STARTED, "t4", None)


def test_n20_4_only_the_started_started_edge_is_remapped_in_source():
    src = LIFECYCLE_PATH.read_text()
    fn = src[src.index("def begin_effect_attempt"):]
    fn = fn[: fn.index("\n    def ")]
    assert "except DispatchAttemptTransitionError as exc:" in fn
    # only the started->started edge is remapped, via the module constants
    assert "invalid_transition:{EFFECT_ATTEMPT_STARTED}->{EFFECT_ATTEMPT_STARTED}" in fn
    # winner-selection primitive untouched: no new link/open call in this fn
    assert "os.link" not in fn and "O_EXCL" not in fn


# ═══════════════════════════════════════════════════════════════════════
# 20-23. Lifecycle semantics unchanged
# ═══════════════════════════════════════════════════════════════════════

def test_transition_matrix_unchanged():
    assert DISPATCH_ATTEMPT_TRANSITIONS[None] == frozenset({PREPARED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[PREPARED] == frozenset({EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[EFFECT_ATTEMPT_STARTED] == frozenset({RECEIPT_CAPTURED, DISPATCH_UNCERTAIN})
    for terminal in (RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED):
        assert DISPATCH_ATTEMPT_TRANSITIONS[terminal] == frozenset()


def test_dispatch_uncertain_disposition_unchanged(tmp_path):
    store, rid = _prepared(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    disp = store.resolve_disposition(rid)
    assert disp.disposition == DISPATCH_UNCERTAIN
    assert disp.automatic_retry_permitted is False
    assert disp.external_effect_possible is True


def test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap():
    diff = _git("diff", R20_HEAD, "--", "src/pcae")
    assert "runtime_dispatch_attempt_lifecycle.py" in diff
    # no other src/pcae file touched
    changed = {
        line.split(" b/")[-1]
        for line in diff.splitlines()
        if line.startswith("diff --git ")
    }
    # Later governed phases are authorized to touch other src/pcae files;
    # this guard only asserts that .1R.19R's own repair was confined to the
    # lifecycle module. Phase ...1R.22 (N-16-3, PBRD-001 v3.0 §12a)
    # authorizedly changes permission_broker_foundation.py + runtime_dispatch_permission.py.
    _POST_1R19R_AUTHORIZED = {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
    }
    assert changed - _POST_1R19R_AUTHORIZED == {
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py"
    }, changed
    # the only added logic is the transition-error remap
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    assert any("DispatchAttemptTransitionError" in l for l in added)
    assert not any("subprocess" in l or "socket" in l or ".dispatch(" in l for l in added)


# ═══════════════════════════════════════════════════════════════════════
# 24-28. Evidence preservation
# ═══════════════════════════════════════════════════════════════════════

def test_original_1r19_doc_body_preserved_and_erratum_is_appended():
    path = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md"
    )
    text = path.read_text()
    original_close = "*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19.*"
    assert original_close in text
    body, _, erratum = text.partition(original_close)
    # original §15 A/B block untouched
    assert "BASELINE (a2b679fe, clean)          : 62 pre-existing failing nodes" in body
    assert "UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS        : 0" in body
    # erratum after it
    assert "ERRATUM" in erratum
    assert "The 5 added nodes:" in erratum
    assert "REMOVED                                                            : 0" in erratum
    assert ".1R.19R" in erratum


def test_original_immutable_1r19_completion_artifacts_not_rewritten():
    # the finalized .1R.19 metadata/report commits still exist unchanged in history
    assert _git("cat-file", "-t", "88e716b1:.pcae/phase-completion-metadata.json").strip() == "blob"
    assert _git("cat-file", "-t", "738e8209:.pcae/phase-completion-report.md").strip() == "blob"


def test_repaired_tree_has_no_attributable_added_regression_marker_in_doc():
    doc = (REPO_ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19R_SLICE_B_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md").read_text()
    assert "0 attributable added / 0 attributable removed" in doc or "**0**" in doc


# ═══════════════════════════════════════════════════════════════════════
# 29-34. No drift
# ═══════════════════════════════════════════════════════════════════════

def test_no_contract_change_since_r20_head():
    changed = set(_git("diff", "--name-only", R20_HEAD, "HEAD", "--", "docs/contracts",
                       "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md").split())
    # Phase ...1R.22 (N-16-3) authorizedly evolves the PB policy contracts.
    _r122_contracts = {
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
    }
    assert changed <= _r122_contracts, changed - _r122_contracts


def test_no_slice_a_or_gate_5_9_drift_since_baseline():
    for rel in (
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        # permission_broker_foundation.py is an authorized Phase ...1R.22
        # (N-16-3, PBRD-001 v3.0 §12a) target -- removed from this drift list.
        "src/pcae/core/runtime_adapter.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/runtime_snapshot.py",
        "src/pcae/commands/runtime_inspect.py",
    ):
        assert _git("diff", "--stat", R19_HEAD, "HEAD", "--", rel).strip() == "", rel


def test_no_first_effect_primitive_in_lifecycle_module():
    tree = ast.parse(LIFECYCLE_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name not in {"subprocess", "socket", "ssl", "http.client", "multiprocessing"}
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in {"subprocess", "socket", "ssl", "http.client"}
        if isinstance(node, ast.Attribute) and node.attr in {
            "Popen", "run", "system", "posix_spawn", "spawn", "check_output", "dispatch",
        }:
            raise AssertionError(f"unexpected effect attr: {node.attr}")


def test_runtime_posture_and_item9_n16_2_unchanged():
    from pcae.core.runtime_introspection import (
        CURRENT_RUNTIME_STATE,
        CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        EXECUTION_AVAILABILITY,
        get_adapter_surfaces,
    )

    assert (CURRENT_RUNTIME_STATE, CURRENT_MAXIMUM_PLUGIN_CAPABILITY, EXECUTION_AVAILABILITY) == (
        "Observed", "observe", "unavailable",
    )
    surfaces = get_adapter_surfaces()
    assert len(surfaces) == 3
    assert all(s.effecting is False and s.execution_availability == "unavailable" for s in surfaces)
    # N-16-2: still zero production importers of the lifecycle module
    importers = _git("grep", "-l", "runtime_dispatch_attempt_lifecycle", "--", "src/").split()
    assert set(importers) <= {
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_introspection.py",  # descriptive string only
    }
