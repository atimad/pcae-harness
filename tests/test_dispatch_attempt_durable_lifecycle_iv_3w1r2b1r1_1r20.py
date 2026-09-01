"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.20 — Independent Verification of the
Dispatch-Attempt Durable Lifecycle (Slice B IV of the ``.1R.16`` Gate-10 plan).

**RE-DERIVE. DO NOT TRUST.** Every assertion in this module is derived
independently from the primary contracts —

* RDGO-001 v3.1 §17 (crash and recovery states) / §18 (retry contract),
  ``docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md``;
* RPAC-REQ-064..072, ``docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md``;
* the ``.1R.16`` planning document (§22.3 state model, §25.1 at-most-once,
  §31 crash determination, prerequisite table item 12 = N-16-2);

— and from current production source read line by line, **not** from the
``.1R.19`` report, its state names, helper names, test names, comments, or
``pcae runtime inspect`` output.

**Verdict of this phase: BLOCKED (Option-B style, mirroring ``.1R.18``).**
The substantive dispatch-attempt durable lifecycle, the at-most-once guard,
the crash/restart determination, the idempotency identity, the two 3S.2.1
prerequisite repairs, the item-9 runtime-inspect repair, and first-external-
effect absence are each **substantively verified / closed-worthy**. The
phase is BLOCKED on regression / verification-evidence acceptance:
``.1R.19`` introduced three undisclosed attributable failures in
pre-existing HPAC Layer-1/2 consumer-inventory guards (``r111r31`` /
``r111r32`` / ``r111r321``) that it never widened, and its finalized
fixed-SHA A/B record ("0 unexplained attributable regressions") is
inaccurate — the same defect class that BLOCKED ``.1R.18``. Referred to a
dedicated repair phase ``149O.20L.7O.3W.1R.2B.1R.1.1R.19R``.

The tests below that carry ``finding_n20_`` in their name encoded the
blocker as executable evidence for the ``.1R.19R`` repair phase. That repair
phase has since landed: N-20-1 (three guards widened by exactly the two
authorized Slice-B importer tuples, no wildcard), N-20-2 (provenance-
preserving ``.1R.19`` erratum, original text preserved), N-20-3 (both
consequential meta-guards recover transitively), and N-20-4 (concurrent
loser errors normalised to ``DispatchAttemptAlreadyStartedError``). The
``finding_n20_`` tests are now **reconciliation-aware**: each carries the
historical finding in its docstring and asserts the repaired state at HEAD.
The historical BLOCKED verdict of *this* phase (``.1R.20``) is unchanged and
is preserved in the canonical ``.1R.20`` document and git history.
"""

from __future__ import annotations

import ast
import concurrent.futures
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_attempt_lifecycle as lifecycle
from pcae.core.runtime_dispatch_attempt_lifecycle import (
    DISPATCH_ATTEMPT_TERMINAL_STATES,
    DISPATCH_ATTEMPT_TRANSITIONS,
    DISPATCH_NOT_STARTED,
    DISPATCH_UNCERTAIN,
    EFFECT_ATTEMPT_STARTED,
    PREPARED,
    RECEIPT_CAPTURED,
    DispatchAttemptAlreadyStartedError,
    DispatchAttemptDisposition,
    DispatchAttemptIntegrityError,
    DispatchAttemptLifecycleError,
    DispatchAttemptTransitionError,
    RuntimeInvocationRecord,
    RuntimeInvocationRecordBinding,
    RuntimeInvocationRecordStore,
    derive_dispatch_attempt_record_id,
    record_grants_no_effect_authority,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_attempt_lifecycle.py"
INVOCATION_PATH = REPO_ROOT / "src/pcae/core/runtime_invocation.py"
ADAPTER_PATH = REPO_ROOT / "src/pcae/core/runtime_adapter.py"
INTROSPECTION_PATH = REPO_ROOT / "src/pcae/core/runtime_introspection.py"
INSPECT_CLI_PATH = REPO_ROOT / "src/pcae/commands/runtime_inspect.py"

#: Independently confirmed: parent of the ``.1R.19`` production implementation
#: commit ``bb646972`` (``git rev-parse bb646972^`` == ``a2b679fe``, the
#: ``.1R.17R.1`` finalize head).
PRE_1R19_BASELINE = "a2b679fe"

#: The exact production files ``.1R.16`` §36.2 / §38 authorises Slice B to
#: touch, independently confirmed by ``git diff --name-only <baseline> HEAD``.
SLICE_B_PRODUCTION_FILES = frozenset(
    {
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_adapter.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/runtime_invocation.py",
        "src/pcae/commands/runtime_inspect.py",
    }
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _binding(**over: str) -> RuntimeInvocationRecordBinding:
    base = dict(
        invocation_id="inv-0000000000000000000000000000",
        attempt_id="att-0000000000000000000000000000",
        idempotency_key="idem-" + "0" * 60,
        proof_id="proof-1",
        approval_id="appr-1",
        runtime_target_id="mock-dry.no-change.v1",
        adapter_id="mock-v1",
        task_id="task-1",
        consumption_record_digest="c" * 64,
        envelope_digest="e" * 64,
    )
    base.update(over)
    return RuntimeInvocationRecordBinding(**base)


def _store(tmp_path: Path) -> RuntimeInvocationRecordStore:
    return RuntimeInvocationRecordStore(tmp_path)


def _prepared_record(tmp_path: Path, **over: str):
    store = _store(tmp_path)
    rec = store.create_record(_binding(**over), created_at="2026-01-01T00:00:00Z")
    store.prepare(rec.record_id, observed_at="2026-01-01T00:00:01Z")
    return store, rec.record_id


# ═══════════════════════════════════════════════════════════════════════
# 1. Range / scope reconstruction (phase prompt §4 / §5 / §51 / §52 / §53)
# ═══════════════════════════════════════════════════════════════════════


def test_pre_1r19_baseline_is_the_parent_of_the_impl_commit():
    assert _git("rev-parse", "--short=8", "bb646972^") == PRE_1R19_BASELINE


#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
#: narrow-eligibility policy + POL-013). Authorizedly modified after the
#: Slice-B track. Exact filenames, no wildcard.
_R122_AUTHORIZED = {
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0): the
    # sole authorized production surface for the positive Gate-7 result.
    "src/pcae/core/runtime_dispatch_gate7.py",
}


def test_slice_b_production_scope_since_baseline_is_exactly_the_authorized_set():
    changed = {
        p
        for p in _git("diff", "--name-only", PRE_1R19_BASELINE, "HEAD").splitlines()
        if p.startswith("src/")
    }
    assert changed - _R122_AUTHORIZED == set(SLICE_B_PRODUCTION_FILES), (
        (changed - _R122_AUTHORIZED) ^ set(SLICE_B_PRODUCTION_FILES)
    )


def test_slice_a_and_closed_gate_modules_are_byte_unchanged_since_baseline():
    for rel in (
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        # runtime_dispatch_gate7.py: authorizedly changed by Phase ...1R.26
        # (N-16-4 -- REPRC-001 v1.0). Gate 5 / 8 / 9 / 10 stay byte-frozen.
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_snapshot.py",
    ):
        assert _git("diff", "--stat", PRE_1R19_BASELINE, "HEAD", "--", rel) == "", rel


def test_no_normative_contract_changed_since_baseline():
    changed = set(_git("diff", "--name-only", PRE_1R19_BASELINE, "HEAD", "--", "docs/contracts/").split())
    # Phase ...1R.22 (N-16-3) authorizedly evolves the PB policy contracts
    # (PBRD-001 -> v3.0 MAJOR, PBPA-001 -> v1.1, new PBNDE-001). Exact paths.
    _r122_contracts = {
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        # Phase ...1R.26 (N-16-4): the one NEW companion contract REPRC-001 v1.0.
        "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md",
    }
    assert changed <= _r122_contracts, changed - _r122_contracts


# ═══════════════════════════════════════════════════════════════════════
# 2. RDGO §17 / §18 + RPAC-REQ-064..072 lifecycle re-derivation
#    (phase prompt §6 / §8 / §10 / §13)
# ═══════════════════════════════════════════════════════════════════════


def test_transition_matrix_is_exactly_the_contract_derived_edges():
    # RDGO §17: PRE-effect material -> attempt marker -> {captured | uncertain};
    # a proven-never-started terminal is reachable only from PREPARED.
    assert DISPATCH_ATTEMPT_TRANSITIONS == {
        None: frozenset({PREPARED}),
        PREPARED: frozenset({EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED}),
        EFFECT_ATTEMPT_STARTED: frozenset({RECEIPT_CAPTURED, DISPATCH_UNCERTAIN}),
        RECEIPT_CAPTURED: frozenset(),
        DISPATCH_UNCERTAIN: frozenset(),
        DISPATCH_NOT_STARTED: frozenset(),
    }


def test_terminal_states_have_no_successor_and_never_mutate(tmp_path):
    assert DISPATCH_ATTEMPT_TERMINAL_STATES == frozenset(
        {RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED}
    )
    store, rid = _prepared_record(tmp_path)
    store.record_dispatch_not_started(rid, observed_at="t2")
    # No edge out of a terminal state.
    for target in (EFFECT_ATTEMPT_STARTED, PREPARED, RECEIPT_CAPTURED, DISPATCH_UNCERTAIN):
        with pytest.raises(DispatchAttemptLifecycleError):
            store._append_transition(rid, target, "t3", None)


def test_no_backwards_transition_effect_started_to_prepared(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    with pytest.raises(DispatchAttemptTransitionError):
        store._append_transition(rid, PREPARED, "t3", None)


def test_prepared_means_identity_durable_but_no_effect_marker(tmp_path):
    # RPAC-REQ-068 first clause: restart before dispatch resumes validation
    # without dispatch. PREPARED must not imply an attempt was made.
    store, rid = _prepared_record(tmp_path)
    disp = store.resolve_disposition(rid)
    assert disp.durable_state == PREPARED
    assert disp.external_effect_possible is False
    assert disp.automatic_retry_permitted is False
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER


def test_effect_attempt_started_is_the_no_auto_retry_boundary_not_proof_of_effect(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    disp = store.resolve_disposition(rid)
    # RDGO §17 DISPATCH_ATTEMPTED / DISPATCH_UNCERTAIN: "None proven yet",
    # "No automatic retry".
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    assert disp.automatic_retry_permitted is False
    assert disp.external_effect_possible is True
    assert disp.fresh_human_authority_required is True


def test_no_state_permits_automatic_retry(tmp_path):
    # RDGO §18: "There is no automatic retry."
    store, rid = _prepared_record(tmp_path)
    assert store.resolve_disposition(rid).automatic_retry_permitted is False
    store.begin_effect_attempt(rid, observed_at="t2")
    assert store.resolve_disposition(rid).automatic_retry_permitted is False
    store.record_dispatch_uncertain(rid, observed_at="t3")
    assert store.resolve_disposition(rid).automatic_retry_permitted is False


def test_write_before_effect_module_contains_no_effect_call_site():
    # phase prompt §11: the durable start marker is written before any future
    # effect boundary; there is no effect call in the lifecycle module.
    tree = ast.parse(LIFECYCLE_PATH.read_text())
    banned_attr = {"dispatch", "Popen", "run", "call", "check_output", "system",
                   "popen", "spawn", "fork", "execv", "execve", "posix_spawn"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in banned_attr, ast.dump(node)
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name not in {"subprocess", "socket", "ssl"}, a.name
        if isinstance(node, ast.ImportFrom):
            assert node.module not in {"subprocess", "socket", "ssl"}, node.module


# ═══════════════════════════════════════════════════════════════════════
# 3. RuntimeInvocationRecord non-authority (phase prompt §7 / §18 / §19)
# ═══════════════════════════════════════════════════════════════════════


def test_record_has_no_authority_method_or_field(tmp_path):
    store, rid = _prepared_record(tmp_path)
    rec = store.read_record(rid)
    for banned in ("approve", "authorize", "permit", "grant", "consume"):
        assert not hasattr(rec, banned)
    for banned in ("execution_allowed", "permission", "authorized"):
        assert banned not in rec.to_reference_document()
    assert rec.GRANTS_NO_EFFECT_AUTHORITY is True


def test_copied_reconstructed_and_dict_roundtripped_record_grants_nothing(tmp_path):
    store, rid = _prepared_record(tmp_path)
    rec = store.read_record(rid)
    import copy as _copy

    assert record_grants_no_effect_authority(rec) is True
    assert record_grants_no_effect_authority(_copy.deepcopy(rec)) is True
    assert record_grants_no_effect_authority(dict(rec.to_reference_document())) is True
    assert record_grants_no_effect_authority(object()) is True  # always True


def test_a_reconstructed_record_at_a_foreign_root_is_not_consulted_for_authority(tmp_path):
    # The mirror never consults a durable record for effect authority — proven
    # structurally: no code path in the module reads a record and returns an
    # authorization. record_grants_no_effect_authority is unconditional.
    src = ast.parse(LIFECYCLE_PATH.read_text())
    returns_true_authority = [
        n for n in ast.walk(src)
        if isinstance(n, ast.FunctionDef) and n.name == "record_grants_no_effect_authority"
    ]
    assert len(returns_true_authority) == 1
    body = returns_true_authority[0].body
    assert isinstance(body[-1], ast.Return)
    assert isinstance(body[-1].value, ast.Constant) and body[-1].value.value is True


# ═══════════════════════════════════════════════════════════════════════
# 4. At-most-once + concurrency (phase prompt §12 / §14 / §26 / §27 / §61)
# ═══════════════════════════════════════════════════════════════════════


def test_second_begin_effect_attempt_fails_closed(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        store.begin_effect_attempt(rid, observed_at="t3")


def test_restart_then_begin_again_fails_closed(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = _store(tmp_path)  # no shared memory
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


@pytest.mark.parametrize("contenders", [4, 8, 16, 32])
def test_concurrent_start_has_exactly_one_durable_winner_all_losers_fail_closed(
    tmp_path, contenders
):
    store, rid = _prepared_record(tmp_path)

    def race(i: int):
        try:
            _store(tmp_path).begin_effect_attempt(rid, observed_at=f"t-{i:03d}")
            return "won"
        except DispatchAttemptLifecycleError:
            return "lost"

    with concurrent.futures.ThreadPoolExecutor(max_workers=contenders) as ex:
        outcomes = list(ex.map(race, range(contenders)))
    assert outcomes.count("won") == 1, outcomes
    assert all(o in ("won", "lost") for o in outcomes)
    started = [
        t for t in _store(tmp_path).list_transitions(rid)
        if t["state"] == EFFECT_ATTEMPT_STARTED
    ]
    assert len(started) == 1


def test_finding_n20_4_concurrent_losers_do_not_all_map_to_already_started_error(tmp_path):
    """FINDING N-20-4 — REPAIRED by ``.1R.19R``.

    HISTORICAL (at the ``.1R.20`` blocked-IV entry, ``738e8209``):
    ``begin_effect_attempt`` guaranteed the safety property (exactly one
    durable ``EFFECT_ATTEMPT_STARTED``; every loser fails closed) but NOT the
    deterministic *error type* the module docstring promises and phase-prompt
    §14 requires — a fraction of losers escaped with a raw
    ``DispatchAttemptTransitionError``
    (``invalid_transition:EFFECT_ATTEMPT_STARTED->EFFECT_ATTEMPT_STARTED``)
    raised by ``_append_transition`` in the window between the durability
    pre-check and the create-only link, which the
    ``except DispatchAttemptIntegrityError`` remap did not cover.

    REPAIR (``.1R.19R``): ``begin_effect_attempt`` now also catches
    ``DispatchAttemptTransitionError`` and normalises the
    ``EFFECT_ATTEMPT_STARTED -> EFFECT_ATTEMPT_STARTED`` edge (only that edge)
    to ``DispatchAttemptAlreadyStartedError``. Every other invalid transition
    keeps its own fail-closed semantics; the winner-selection primitive is
    unchanged. This test now REQUIRES uniform ``DispatchAttemptAlreadyStartedError``."""
    store, rid = _prepared_record(tmp_path)
    seen: list[str] = []

    def race(i: int):
        try:
            _store(tmp_path).begin_effect_attempt(rid, observed_at=f"t-{i:03d}")
            return None
        except DispatchAttemptLifecycleError as exc:
            return type(exc).__name__

    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
        for r in ex.map(race, range(24)):
            if r:
                seen.append(r)
    assert seen, "expected losing contenders"
    # Repaired: every loser maps deterministically to the duplicate-start error.
    assert set(seen) == {"DispatchAttemptAlreadyStartedError"}, seen


# ═══════════════════════════════════════════════════════════════════════
# 5. Idempotency identity (phase prompt §15 / §16 / §17)
# ═══════════════════════════════════════════════════════════════════════


def test_record_id_derives_only_from_invocation_and_attempt_id():
    a = derive_dispatch_attempt_record_id("inv-x", "att-y")
    b = derive_dispatch_attempt_record_id("inv-x", "att-y")
    assert a == b and a.startswith("dar-") and len(a) == 4 + 32


def test_record_id_ignores_clock_nonce_pid_mtime():
    tree = ast.parse(LIFECYCLE_PATH.read_text())
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "derive_dispatch_attempt_record_id"
    )
    # Strip the docstring, then scan every remaining name/attr node.
    body = fn.body[1:] if (
        fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant)
    ) else fn.body
    names: set[str] = set()
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name):
                names.add(node.id)
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
    for banned in ("time", "now", "urandom", "getpid", "uuid", "monotonic", "getmtime", "random"):
        assert banned not in names, banned


def test_restart_reconstructs_identical_id_and_transition_log(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = _store(tmp_path)
    assert (
        derive_dispatch_attempt_record_id(
            "inv-0000000000000000000000000000", "att-0000000000000000000000000000"
        )
        == rid
    )
    assert [t["state"] for t in fresh.list_transitions(rid)] == [
        PREPARED,
        EFFECT_ATTEMPT_STARTED,
    ]


def test_cross_attempt_isolation(tmp_path):
    store = _store(tmp_path)
    r1 = store.create_record(_binding(attempt_id="att-" + "1" * 28), created_at="t0")
    r2 = store.create_record(_binding(attempt_id="att-" + "2" * 28), created_at="t0")
    assert r1.record_id != r2.record_id
    store.prepare(r1.record_id, observed_at="t1")
    store.begin_effect_attempt(r1.record_id, observed_at="t2")
    assert store.latest_state(r2.record_id) is None


def test_same_id_different_bound_content_is_a_hard_collision(tmp_path):
    store = _store(tmp_path)
    store.create_record(_binding(proof_id="proof-A"), created_at="t0")
    with pytest.raises(DispatchAttemptIntegrityError):
        store.create_record(_binding(proof_id="proof-B"), created_at="t0")


def test_same_id_identical_content_resumes_without_new_write(tmp_path):
    # RPAC-REQ-066: identical canonical content returns/resumes the record.
    store = _store(tmp_path)
    a = store.create_record(_binding(), created_at="t0")
    b = store.create_record(_binding(), created_at="t0")
    assert a.record_id == b.record_id
    assert a.record_integrity_digest == b.record_integrity_digest


# ═══════════════════════════════════════════════════════════════════════
# 6. Crash / restart determination (phase prompt §18-§25)
# ═══════════════════════════════════════════════════════════════════════


def test_crash_before_prepare_is_not_started(tmp_path):
    store = _store(tmp_path)
    rec = store.create_record(_binding(), created_at="t0")
    disp = _store(tmp_path).resolve_disposition(rec.record_id)
    assert disp.disposition == DispatchAttemptDisposition.NOT_STARTED
    assert disp.external_effect_possible is False


def test_crash_after_start_is_uncertain_with_no_auto_retry(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    disp = _store(tmp_path).resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    assert disp.external_effect_possible is True
    assert disp.automatic_retry_permitted is False


def test_ambiguous_started_attempt_never_becomes_not_started(tmp_path):
    # phase prompt §21: no path reinterprets an unresolved started attempt as
    # DISPATCH_NOT_STARTED.
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    with pytest.raises(DispatchAttemptTransitionError):
        store.record_dispatch_not_started(rid, observed_at="t3")
    assert (
        _store(tmp_path).resolve_disposition(rid).disposition
        == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    )


@pytest.mark.parametrize("terminal", [DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED])
def test_terminal_state_reconstructs_stably_across_restart(tmp_path, terminal):
    store, rid = _prepared_record(tmp_path)
    if terminal == DISPATCH_UNCERTAIN:
        store.begin_effect_attempt(rid, observed_at="t2")
        store.record_dispatch_uncertain(rid, observed_at="t3")
    else:
        store.record_dispatch_not_started(rid, observed_at="t2")
    d1 = store.resolve_disposition(rid)
    d2 = _store(tmp_path).resolve_disposition(rid)
    assert d1.disposition == d2.disposition and d2.terminal is True


def test_receipt_is_evidence_not_authority(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_receipt_captured(rid, observed_at="t3", detail={"receipt": "x"})
    disp = _store(tmp_path).resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.RECEIPT_CAPTURED
    assert disp.automatic_retry_permitted is False
    assert disp.fresh_human_authority_required is True


# ═══════════════════════════════════════════════════════════════════════
# 7. Corruption battery + append-only (phase prompt §23 / §24 / §25)
# ═══════════════════════════════════════════════════════════════════════


def _transitions_dir(tmp_path: Path, rid: str) -> Path:
    return tmp_path / ".pcae" / "runtime-dispatch-attempts" / rid / "transitions"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: (d.__setitem__("state", "WAT")),
        lambda d: (d.__setitem__("sequence", 99)),
        lambda d: (d.__setitem__("digest", "deadbeef")),
        lambda d: (d.__setitem__("prior_digest", "wrong")),
    ],
    ids=["unknown_state", "sequence_gap", "digest_mismatch", "chain_mismatch"],
)
def test_corrupt_transition_fails_closed(tmp_path, mutate):
    store, rid = _prepared_record(tmp_path)
    store.begin_effect_attempt(rid, observed_at="t2")
    tdir = _transitions_dir(tmp_path, rid)
    victim = sorted(tdir.glob("*.json"))[-1]
    doc = json.loads(victim.read_text())
    mutate(doc)
    victim.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")))
    with pytest.raises(DispatchAttemptIntegrityError):
        _store(tmp_path).list_transitions(rid)


def test_extra_transition_after_terminal_fails_closed(tmp_path):
    store, rid = _prepared_record(tmp_path)
    store.record_dispatch_not_started(rid, observed_at="t2")
    tdir = _transitions_dir(tmp_path, rid)
    prior = json.loads(sorted(tdir.glob("*.json"))[-1].read_text())
    extra = {
        "sequence": 3,
        "state": RECEIPT_CAPTURED,
        "observed_at": "t3",
        "prior_digest": prior["digest"],
        "detail": {},
    }
    from pcae.core.hpac_foundation import canonical_digest

    extra["digest"] = canonical_digest(
        {k: extra[k] for k in ("sequence", "state", "observed_at", "prior_digest", "detail")}
    )
    (tdir / "0003-receipt_captured.json").write_text(
        json.dumps(extra, sort_keys=True, separators=(",", ":"))
    )
    with pytest.raises(DispatchAttemptIntegrityError):
        _store(tmp_path).list_transitions(rid)


def test_record_id_path_traversal_fails_closed(tmp_path):
    store = _store(tmp_path)
    for evil in ("../x", "..", "a/b", "/abs", "."):
        with pytest.raises(DispatchAttemptIntegrityError):
            store.read_record(evil)


def test_transition_files_are_create_only_never_overwritten(tmp_path):
    store, rid = _prepared_record(tmp_path)
    tdir = _transitions_dir(tmp_path, rid)
    first = sorted(tdir.glob("*.json"))[0]
    before = first.read_bytes()
    store.prepare(rid, observed_at="tX")  # idempotent replay, no write
    assert first.read_bytes() == before
    assert len(list(tdir.glob("*.json"))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 8. 3S.2.1 MUST-FIX #1 — malformed adapter-result fail-closed
#    (phase prompt §26-§30)
# ═══════════════════════════════════════════════════════════════════════


def test_malformed_adapter_result_reasons_rejects_non_result_and_mismatches():
    from pcae.core.runtime_adapter import malformed_adapter_result_reasons
    from pcae.core.runtime_invocation import InvocationRequest

    # A plain dict is rejected outright (the original 3S.2.1 defect: an
    # AttributeError inside the store instead of a clean fail-closed).
    reasons = malformed_adapter_result_reasons({"ok": True}, _fake_request())
    assert reasons and reasons[0].startswith("not_a_runtime_invocation_result")


def _fake_request():
    from pcae.core.runtime_invocation import InvocationRequest

    # Minimal structural stand-in — only the id/version fields are read.
    class _R:
        invocation_id = "inv-1"
        attempt_id = "att-1"
        idempotency_key = "idem-1"
        contract_version = "RPAC-001/1.0"
        runtime_target_id = "mock-dry.no-change.v1"

    return _R()


def test_malformed_result_validation_is_ordered_before_persistence_in_source():
    src = ADAPTER_PATH.read_text()
    # malformed_reasons check must appear before store.write_result in
    # simulate_invocation's body.
    body = src[src.index("def simulate_invocation") :]
    assert "malformed_adapter_result_reasons" in body
    i_check = body.index("malformed_reasons = malformed_adapter_result_reasons")
    assert "write_result" not in body[:i_check]


def test_simulation_dispatch_exception_is_caught_and_failed_closed_in_source():
    src = ADAPTER_PATH.read_text()
    assert "dispatch_raised:" in src and "collect_raised:" in src


def test_simulation_path_remains_non_effecting():
    tree = ast.parse(ADAPTER_PATH.read_text())
    # exactly one adapter.dispatch( call site (pre-existing simulation), and it
    # is the resolved *simulation* adapter — no new effect primitive.
    dispatch_calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "dispatch"
    ]
    assert len(dispatch_calls) == 1


# ═══════════════════════════════════════════════════════════════════════
# 9. 3S.2.1 MUST-FIX #2 — RuntimeInvocationStore path containment
#    (phase prompt §31-§35)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "evil",
    ["../../../../tmp/x", "..", ".", "a/b", "/etc/passwd", "a\\b"],
)
def test_runtime_invocation_store_rejects_unsafe_id_components(tmp_path, evil):
    from pcae.core.runtime_invocation import RuntimeInvocationStore, InvocationIntegrityError

    store = RuntimeInvocationStore(tmp_path)
    with pytest.raises(InvocationIntegrityError):
        store._invocation_dir(evil)
    with pytest.raises(InvocationIntegrityError):
        store._attempt_dir("inv-ok-000000000000000000000000", evil)


def test_runtime_invocation_store_has_resolved_path_containment_check():
    src = INVOCATION_PATH.read_text()
    assert "_assert_within_root" in src and "relative_to(root)" in src
    assert "path_escapes_store_root" in src


def test_canonical_generated_ids_still_pass_the_grammar():
    from pcae.core.hpac_foundation import require_safe_relative_id_component

    # production IDs like att-<32hex> / inv-<32hex> remain valid unchanged.
    require_safe_relative_id_component("att-" + "0" * 32, context="attempt_id")
    require_safe_relative_id_component("inv-" + "a" * 32, context="invocation_id")


# ═══════════════════════════════════════════════════════════════════════
# 10. item-9 runtime-inspect discoverability repair (phase prompt §36-§41)
# ═══════════════════════════════════════════════════════════════════════


def test_adapter_surfaces_are_static_non_effecting_non_authoritative():
    from pcae.core.runtime_introspection import get_adapter_surfaces

    surfaces = get_adapter_surfaces()
    assert len(surfaces) == 3
    for s in surfaces:
        assert s.effecting is False
        assert s.authoritative is False
        assert s.execution_availability == "unavailable"


def test_get_adapter_surfaces_reads_no_registry_and_mutates_nothing():
    src = INTROSPECTION_PATH.read_text()
    fn = src[src.index("def get_adapter_surfaces") : src.index("def get_state")]
    assert "RuntimeRegistry" not in fn and "return RUNTIME_ADAPTER_SURFACES" in fn


def test_runtime_inspect_json_contract_is_byte_unchanged_since_baseline():
    # phase prompt §38: --json / runtime_snapshot.py untouched.
    assert _git("diff", "--stat", PRE_1R19_BASELINE, "HEAD", "--",
                "src/pcae/core/runtime_snapshot.py") == ""
    diff = _git("diff", PRE_1R19_BASELINE, "HEAD", "--", "src/pcae/commands/runtime_inspect.py")
    # every added line lands inside _format_human (never _format_json).
    assert "_format_json" not in "\n".join(
        line for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
    )


def test_runtime_inspect_still_reports_unavailable_observed_posture():
    out = subprocess.run(
        ["pcae", "runtime", "inspect"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    combined = out.stdout + out.stderr
    assert "unavailable" in combined and "Observed" in combined


# ═══════════════════════════════════════════════════════════════════════
# 11. N-16-2 — original meaning + production-consumer inventory
#     (phase prompt §42-§44 / §68)
# ═══════════════════════════════════════════════════════════════════════


def test_n16_2_has_zero_production_consumers_infrastructure_only(tmp_path):
    """N-16-2 (``.1R.16`` prerequisite item 12): 'no Gate-5-11-wired mirror'.
    Independently adjudicated as **interpretation A** — build the durable
    mirror infrastructure, ready for the future Gate-10/11 lifecycle, with no
    effect-bearing consumer yet. Slice B's chartered scope (``.1R.16`` §36.1
    row B) is the lifecycle module itself; the ``adapter.dispatch()`` call
    site and its coordinator wiring are explicitly Slice C (row C). The
    inventory below confirms zero production creators/consumers."""
    prod_refs = subprocess.run(
        ["git", "grep", "-l", "runtime_dispatch_attempt_lifecycle", "--", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.split()
    # Only the module itself + one descriptive string literal in
    # runtime_introspection.py's surface list. No importer.
    assert set(prod_refs) <= {
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_introspection.py",
    }
    importers = subprocess.run(
        ["git", "grep", "-l",
         r"import runtime_dispatch_attempt_lifecycle\|from pcae.core.runtime_dispatch_attempt_lifecycle",
         "--", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.split()
    assert importers == []


def test_slice_c_effect_module_absent():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    # No `.dispatch(` *call* (AST, not text) in the Slice-B lifecycle module.
    tree = ast.parse(LIFECYCLE_PATH.read_text())
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "dispatch"
    ]
    assert calls == []


# ═══════════════════════════════════════════════════════════════════════
# 12. BLOCKER — undisclosed .1R.19-attributable scope-fence regressions
#     (phase prompt §45-§50 / §63)
# ═══════════════════════════════════════════════════════════════════════

_HPAC_CONSUMER_GUARDS = (
    ("tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
     "test_hpac_repair_has_zero_preexisting_production_consumers"),
    ("tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
     "test_new_hpac_modules_have_zero_preexisting_production_consumers"),
    ("tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
     "test_foundation_has_no_production_consumers_or_gate_wiring"),
)


def test_finding_n20_1_slice_b_added_two_unlisted_hpac_foundation_importers():
    """BLOCKING FINDING N-20-1. ``.1R.19`` added ``from pcae.core.hpac_foundation
    import ...`` to two production modules — ``runtime_dispatch_attempt_lifecycle.py``
    (new) and ``runtime_invocation.py`` (3S.2.1 MUST-FIX #2) — a legitimate
    reuse of the shared ``require_safe_relative_id_component`` /
    ``canonical_digest`` / ``reject_symlink`` helpers, but did NOT widen the
    HPAC Layer-1/2 consumer-inventory guard family, which freezes the exact
    set of production modules permitted to import that foundation."""
    for mod in ("runtime_dispatch_attempt_lifecycle.py", "runtime_invocation.py"):
        src = (REPO_ROOT / "src/pcae/core" / mod).read_text()
        assert "from pcae.core.hpac_foundation import" in src, mod


@pytest.mark.parametrize("path,node", _HPAC_CONSUMER_GUARDS,
                         ids=[p.split("/")[-1].split("_3w1r")[0] for p, _ in _HPAC_CONSUMER_GUARDS])
def test_finding_n20_1_hpac_consumer_guard_is_repaired_at_head(path, node):
    """FINDING N-20-1 — REPAIRED by ``.1R.19R``.

    HISTORICAL (at the ``.1R.20`` blocked-IV entry, ``738e8209``): each of
    these three pre-existing HPAC Layer-1/2 consumer-inventory guards PASSED
    at the pre-``.1R.19`` baseline ``a2b679fe`` and FAILED at that HEAD,
    attributable to and explained by ``.1R.19`` (which added
    ``from pcae.core.hpac_foundation import ...`` to
    ``runtime_dispatch_attempt_lifecycle.py`` and ``runtime_invocation.py``
    without widening or disclosing this guard family) — same defect class
    that BLOCKED ``.1R.18``. Preserved as the ``.1R.20`` blocked verdict in
    ``docs/PHASE_..._1R_20_...md`` and git history (``fdfd46e5`` / ``e05f0ea3``).

    REPAIR (``.1R.19R``): each ``AUTHORIZED_CONSUMERS`` set is widened by
    exactly the two authorized Slice-B importer tuples
    ``("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation")``
    and ``("runtime_invocation.py", "pcae.core.hpac_foundation")`` — no
    wildcard; each guard still rejects any other importer. This test now
    REQUIRES the guard green at HEAD and the widening narrow."""
    result = subprocess.run(
        ["python", "-m", "pytest", f"{path}::{node}", "-p", "no:randomly",
         "-p", "no:xdist", "-o", "addopts=", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    src = (REPO_ROOT / path).read_text()
    seg = src[src.index("def " + node):]
    seg = seg[:seg.index("\n\ndef ")]
    for tup in (
        '("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation")',
        '("runtime_invocation.py", "pcae.core.hpac_foundation")',
        '("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation")',
    ):
        assert tup in seg, (path, tup)
    authorized_literal = seg.split("AUTHORIZED_CONSUMERS")[1].split("unauthorized")[0]
    for bad in ('"*"', "'*'", "fnmatch", ".startswith(", "pcae.core.*", "src/pcae/core/*"):
        assert bad not in authorized_literal, (path, bad)


def test_finding_n20_2_1r19_ab_record_erratum_is_issued():
    """FINDING N-20-2 — ERRATUM ISSUED by ``.1R.19R`` (original preserved).

    HISTORICAL: the ``.1R.19`` finalized phase-completion report / metadata
    asserted '0 unexplained attributable regressions' and that 'every widened
    scope-fence guard keeps explicit finite enumeration and still rejects an
    unauthorized importer'. Three guards (``r111r31`` / ``r111r32`` /
    ``r111r321``) were never widened at all and failed — so the finalized A/B
    record was materially inaccurate, exactly as ``.1R.17``'s was when it
    BLOCKED ``.1R.18``.

    REPAIR (``.1R.19R``): a provenance-preserving erratum is appended to the
    ``.1R.19`` canonical doc — original text preserved verbatim, the A/B
    figure corrected to the true '5 added (all explained by ``.1R.19``, root
    cause N-20-1), 0 removed; 1 pre-existing flake disclosed'."""
    doc = (
        REPO_ROOT
        / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md"
    ).read_text()
    assert "ERRATUM" in doc.upper()
    assert ".1R.19R" in doc
    assert "The 5 added nodes:" in doc
    assert "REMOVED                                                            : 0" in doc
    # the original section is preserved, not rewritten
    assert "NEW attributable failing nodes                         : 2" in doc


def test_finding_n20_3_1r19_own_meta_guard_recovers_at_head():
    """FINDING N-20-3 — REPAIRED TRANSITIVELY by ``.1R.19R``.

    HISTORICAL: ``.1R.19`` shipped a meta-guard —
    ``tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::
    test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]``
    — that runs the ``r111r32`` guard and asserts it passes at HEAD; it did
    not, so ``.1R.19`` committed a test that contradicted its own disclosed
    guard set. ``.1R.15.3``'s ``test_v15_2_guards_pass_at_head`` failed for
    the same single root cause.

    REPAIR (``.1R.19R``): both meta-guards recover because the three
    underlying ``r111r3x`` guards are corrected — no meta-guard was weakened,
    skipped, xfailed, or broadly allowlisted."""
    for node in (
        "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py"
        "::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]",
        "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py"
        "::test_v15_2_guards_pass_at_head",
    ):
        result = subprocess.run(
            ["python", "-m", "pytest", node,
             "-p", "no:randomly", "-p", "no:xdist", "-o", "addopts=", "-q"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, node + "\n" + result.stdout[-3000:]


# ═══════════════════════════════════════════════════════════════════════
# 13. Runtime posture / POL-005 / first-effect absence (phase prompt §54-§58)
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_posture_unchanged():
    from pcae.core.runtime_introspection import (
        CURRENT_RUNTIME_STATE,
        CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        EXECUTION_AVAILABILITY,
    )

    assert CURRENT_RUNTIME_STATE == "Observed"
    assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert EXECUTION_AVAILABILITY == "unavailable"


def test_pol_005_module_byte_unchanged_since_baseline():
    # Phase ...1R.22 (N-16-3, PBRD-001 v3.0 §12a) authorizedly amends this
    # module (POL-005 one-profile carve-out + POL-013). The Slice-B track
    # (this IV) changed nothing here; POL-005's hard DENY of every ordinary
    # non-simulation request is re-asserted behaviorally instead of by bytes.
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


def test_no_first_external_effect_primitive_anywhere_in_slice_b():
    for path in (LIFECYCLE_PATH, INTROSPECTION_PATH, INSPECT_CLI_PATH):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                for n in names:
                    assert n not in {"subprocess", "socket", "ssl", "http.client"}, (path, n)
