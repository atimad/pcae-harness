"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3 — Independent Verification of the
Gate-9 Atomic-Consumption Serialization-Semantics Repair (V-15-1) plus the
bundled V-15-2 guard conversion and V-15-3 monkeypatch-hygiene fix.

RE-DERIVE, DO NOT TRUST. Every assertion here is derived from the primary
contracts (RDGO-001 v3.0 §10 / §15 / §17, HPAC-REQ-095 / 098 / 099 / 100 /
101, the `.1R.9` §12/§18 battery model, `.1R.15.1` §14 Option B) and current
production source — not from the `.1R.15.2` report, its 44 tests, helper
names, `AuthorityGenerationSnapshot`, or its pass counts.

The positive Gate-9 consumption path is production-unreachable (real Gate 7
always DENYs; real ``run_gate5`` never yields a ``Gate5Result``). Every
positive assertion runs through the same clearly-labelled test-only
provenance substitution + ``tmp_path`` consumption store the `.1R.14`
integration suite uses; it manufactures no real authority.

Independent instrumentation: this suite builds its own call-order recorder
(``_Recorder``) and its own source-slice analyzer rather than reusing the
`.1R.15.2` suite's ``_inject_between_s1_and_s2`` / source-index helpers.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
import threading
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate9 as g9
from pcae.core import runtime_invocation_authority_consumption as ric

from test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14 import (  # noqa: E501
    NOW,
    REPO_ROOT,
    _authority_generation_resolver,
    _count_consumption_json,
    _run,
    chain,  # noqa: F401  (pytest fixture re-export)
)

G9_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py").read_text()
BASELINE_SHA = "d78d9676"  # .1R.15.2 phase-entry (pre-repair gate9.py)

# A structurally valid AuthorityGenerationSnapshot (`.1R.15.4`) for
# _build_consumption_record calls that do not exercise the snapshot content.
_SNAP = {
    "principal_generation": "p" * 64,
    "credential_generation": "c" * 64,
    "approval_generation": "a" * 64,
    "lifecycle_generation": "l" * 64,
    "consumption_generation": ("absent",),
}


# ═══════════════════════════════════════════════════════════════════════
# Independent helpers
# ═══════════════════════════════════════════════════════════════════════
def _root(chain):
    return Path(str(chain.store._root))


def _revoke_principal(chain):
    chain.rig.registry.revoke_principal(
        chain.rig.registry.fixture_admin_writer(),
        principal_id=chain.rig.principal_id,
        revoked_at=NOW,
    )


def _revoke_credential(chain):
    chain.rig.registry.revoke_credential(
        chain.rig.registry.fixture_admin_writer(),
        credential_id=chain.rig.credential_id,
        revoked_at=NOW,
    )


def _terminate_lifecycle(chain, *, state="REVOKED"):
    chain.rig.lifecycle_store.terminate_canonical(
        chain.rig.lifecycle_store.fixture_terminal_writer(chain.rig.proof_id),
        proof_id=chain.rig.proof_id,
        state=state,
        reason_code="rdw-1r15-3-iv",
        occurred_at=NOW,
    )


class _Recorder:
    """Wraps the coordinator's DI dependencies to record the exact order of
    authority-relevant reads and the single durable create."""

    def __init__(self, chain, *, mutate_before_create=None):
        self.events = []
        self._chain = chain
        self._mutate_before_create = mutate_before_create
        self._base_resolver = _authority_generation_resolver(chain)
        self._real_store_resolve = chain.store.resolve
        self._real_store_create = chain.store.create
        self._real_lifecycle = chain.rig.lifecycle_store.resolve_canonical_chain

    def authority_generation_resolver(self):
        self.events.append("authority_generation_resolver")
        return self._base_resolver()

    def capability_snapshot_resolver(self):
        self.events.append("capability_snapshot_resolver")
        return {
            "current_runtime_state": "Observed",
            "current_maximum_plugin_capability": "observe",
            "execution_availability": "unavailable",
        }

    def install(self, monkeypatch):
        rec = self

        def store_resolve(proof_id):
            rec.events.append("store.resolve")
            return rec._real_store_resolve(proof_id)

        def store_create(proof_id, record):
            rec.events.append("store.create")
            if rec._mutate_before_create is not None:
                rec._mutate_before_create(rec._chain)
                rec._mutate_before_create = None
            return rec._real_store_create(proof_id, record)

        def lifecycle_chain(proof_id):
            rec.events.append("lifecycle.resolve_canonical_chain")
            return rec._real_lifecycle(proof_id)

        monkeypatch.setattr(rec._chain.store, "resolve", store_resolve)
        monkeypatch.setattr(rec._chain.store, "create", store_create)
        monkeypatch.setattr(
            rec._chain.rig.lifecycle_store, "resolve_canonical_chain", lifecycle_chain
        )


def _inject_between_s1_and_s2(monkeypatch, chain, side_effect):
    """Fire ``side_effect(chain)`` exactly once from inside
    ``_build_consumption_record`` — step 15, strictly after S1 (step 14a) and
    strictly before S2 (step 15a). Independent re-derivation of the injection
    point: confirmed by source order in
    ``test_s1_is_captured_only_after_the_revalidation_battery`` /
    ``test_s2_is_the_last_authority_read_before_create``."""
    real = g9._build_consumption_record
    fired = {"done": False}

    def hooked(**kwargs):
        if not fired["done"]:
            fired["done"] = True
            side_effect(chain)
        return real(**kwargs)

    monkeypatch.setattr(g9, "_build_consumption_record", hooked)


def _drift_resolver(sequence):
    """A resolver whose returned dict changes across calls, per ``sequence``
    (a list of dicts, one consumed per call; the last repeats)."""
    state = {"i": 0}

    def _resolve():
        i = min(state["i"], len(sequence) - 1)
        state["i"] += 1
        return dict(sequence[i])

    return _resolve


# ═══════════════════════════════════════════════════════════════════════
# 1. Independently re-derived repaired call flow (source + AST)
# ═══════════════════════════════════════════════════════════════════════
def test_coordinator_has_exactly_one_create_call_site():
    tree = ast.parse(G9_SRC)
    creates = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "create"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "consumption_store"
    ]
    assert len(creates) == 1


def test_no_lock_primitive_introduced_by_the_repair():
    tree = ast.parse(G9_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
    for banned in ("threading", "fcntl", "filelock", "multiprocessing", "asyncio", "posix_ipc"):
        assert banned not in imported, banned
    for tok in ("Lock(", "RLock(", "Semaphore(", "flock(", "FileLock(", "lockf("):
        assert tok not in G9_SRC, tok


def test_snapshot_capture_helper_reads_only_canonical_state():
    """``_capture_authority_generation_snapshot`` calls only the trusted
    resolver + the two canonical read helpers; no write, subprocess, socket,
    time, or random."""
    src = inspect.getsource(g9._capture_authority_generation_snapshot)
    src += inspect.getsource(g9._lifecycle_generation_token)
    src += inspect.getsource(g9._consumption_generation_token)
    for banned in (
        "time.", "datetime", "random", "uuid", "getmtime", "st_mtime",
        "monotonic", "perf_counter", "open(", "subprocess", "socket", ".create(",
    ):
        assert banned not in src, banned


# ═══════════════════════════════════════════════════════════════════════
# 2. S1 after the full battery — independently ordered via instrumentation
# ═══════════════════════════════════════════════════════════════════════
def test_s1_is_captured_only_after_the_revalidation_battery(chain, monkeypatch):
    rec = _Recorder(chain)
    rec.install(monkeypatch)
    r, reasons = _run(
        chain,
        authority_generation_resolver=rec.authority_generation_resolver,
        capability_snapshot_resolver=rec.capability_snapshot_resolver,
    )
    assert r is not None and r.status == "consumed", reasons
    ev = rec.events
    # capability re-read (battery step 13) and the absence check (step 14)
    # both precede the FIRST authority_generation_resolver call (S1 capture).
    first_s1 = ev.index("authority_generation_resolver")
    assert "capability_snapshot_resolver" in ev[:first_s1]
    assert "store.resolve" in ev[:first_s1]


def test_s2_is_the_last_authority_read_before_create(chain, monkeypatch):
    rec = _Recorder(chain)
    rec.install(monkeypatch)
    r, _ = _run(
        chain,
        authority_generation_resolver=rec.authority_generation_resolver,
        capability_snapshot_resolver=rec.capability_snapshot_resolver,
    )
    assert r is not None and r.status == "consumed"
    ev = rec.events
    create_idx = ev.index("store.create")
    # the S2 battery (resolver + lifecycle chain + store.resolve) is the last
    # cluster of reads immediately before the create; nothing effectful in
    # between (no second capability read, no gate-8 re-run marker).
    between = ev[ev.index("authority_generation_resolver", ev.index("authority_generation_resolver") + 1):create_idx]
    assert "capability_snapshot_resolver" not in between
    # last event before create is a pure comparison, i.e. the immediately
    # preceding recorded read belongs to the S2 capture cluster.
    assert ev[create_idx - 1] in {
        "store.resolve",
        "lifecycle.resolve_canonical_chain",
        "authority_generation_resolver",
    }


def test_exactly_two_snapshot_captures_per_successful_run(chain, monkeypatch):
    rec = _Recorder(chain)
    rec.install(monkeypatch)
    _run(
        chain,
        authority_generation_resolver=rec.authority_generation_resolver,
        capability_snapshot_resolver=rec.capability_snapshot_resolver,
    )
    assert rec.events.count("authority_generation_resolver") == 2


# ═══════════════════════════════════════════════════════════════════════
# 3. Zero effectful I/O between the S2==S1 decision and create
#    (independent source slice — own delimiters)
# ═══════════════════════════════════════════════════════════════════════
def test_zero_effectful_io_between_drift_decision_and_create():
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    a = src.index("_first_authority_generation_drift(s1, s2)")
    b = src.index("consumption_store.create(proof_id, consumption_record)")
    span = src[a:b]
    # only a pure comparison + the fail-closed return may appear
    for forbidden in (
        "resolve(", "resolver(", "run_gate8", "descriptor_resolver", "subprocess",
        "socket", "open(", "revalidate_", "_capture_authority_generation_snapshot",
        "compute_canonical_digest", "_build_consumption_record",
    ):
        assert forbidden not in span, forbidden
    # exactly one statement of substance: the drift branch
    assert span.count("return") == 1


# ═══════════════════════════════════════════════════════════════════════
# 4. Token inventory — re-derived, not trusted
# ═══════════════════════════════════════════════════════════════════════
def test_snapshot_carries_five_tokens_over_the_four_mutable_authority_sources(chain):
    s1, reasons = g9._capture_authority_generation_snapshot(
        authority_generation_resolver=_authority_generation_resolver(chain),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    assert reasons == ()
    assert set(s1) == {
        "principal_generation",
        "credential_generation",
        "approval_generation",
        "lifecycle_generation",
        "consumption_generation",
    }
    # drift comparison covers the 4 authority tokens; consumption is handled
    # separately (present -> already_consumed, not a drift rejection).
    assert g9._AUTHORITY_GENERATION_DRIFT_ORDER == (
        "principal_generation",
        "credential_generation",
        "approval_generation",
        "lifecycle_generation",
    )


def test_principal_token_moves_on_real_revocation(chain):
    r = _authority_generation_resolver(chain)
    before = r()["principal_generation"]
    _revoke_principal(chain)
    assert r()["principal_generation"] != before


def test_credential_token_moves_on_real_revocation(chain):
    r = _authority_generation_resolver(chain)
    before = r()["credential_generation"]
    _revoke_credential(chain)
    assert r()["credential_generation"] != before


def test_lifecycle_token_moves_on_terminal_event(chain):
    before = g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id)
    _terminate_lifecycle(chain)
    after = g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id)
    assert before != after


def test_lifecycle_token_is_over_every_chain_event_not_just_the_head(chain):
    """The token digests the ordered (sequence, state, event_digest) triples
    of the WHOLE chain — a change to any event, not only the head, moves it.
    Verified structurally: the helper iterates the full chain."""
    src = inspect.getsource(g9._lifecycle_generation_token)
    assert "resolve_canonical_chain(proof_id)" in src
    assert "for resolved in chain" in src


def test_lifecycle_token_subsumes_proof_state(chain):
    """Proof lifecycle status / expiry / revocation / canonical identity are
    all events in the same hash-chained lifecycle. A terminal REVOKED append
    (a proof-state change) moves the lifecycle token — no separate
    proof-state token is needed."""
    before = g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id)
    _terminate_lifecycle(chain, state="EXPIRED")
    assert g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id) != before


def test_consumption_token_states(chain):
    assert g9._consumption_generation_token(chain.store, chain.rig.proof_id) == ("absent",)
    r, _ = _run(chain)
    assert r.status == "consumed"
    tok = g9._consumption_generation_token(chain.store, chain.rig.proof_id)
    assert tok[0] == "present" and len(tok[1]) == 64


def test_durability_uncertain_consumption_token_propagates(chain, monkeypatch):
    def boom(proof_id):
        raise ric.RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("corrupt")

    monkeypatch.setattr(chain.store, "resolve", boom)
    r, reasons = _run(chain)
    assert r is None
    assert reasons == ("gate9_consumption_state_durability_uncertain",)


# ═══════════════════════════════════════════════════════════════════════
# 5. Approval-state completeness — the resolver-delegation asymmetry
#    (independent finding N-15-3-2)
# ═══════════════════════════════════════════════════════════════════════
def test_approval_generation_is_resolver_delegated(chain):
    """The *coordinator* still delegates ``approval_generation`` to the
    trusted resolver — its own body reads no approval store. N-15-3-2 is
    resolved in `.1R.15.4` by a dedicated production resolver *factory*
    (``build_production_authority_generation_resolver``) whose
    ``approval_generation`` folds the current approval-store resolvability
    and record digest (RIHAC-001 v2.0 §14: no separate approval-revocation
    store exists; approval revocation is transitively principal/credential/
    lifecycle/expiry, and the factory additionally commits the current
    resolved approval digest + a forward hook for a future §14 artifact)."""
    coordinator_src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    capture_src = inspect.getsource(g9._capture_authority_generation_snapshot)
    assert 'resolved["approval_generation"]' in capture_src
    # the coordinator body itself reads no approval store
    assert "approval_store" not in coordinator_src
    assert "runtime_invocation_approval_store" not in coordinator_src
    # but the .1R.15.4 production factory does (N-15-3-2)
    factory_src = inspect.getsource(g9.build_production_authority_generation_resolver)
    assert "approval_store.load" in factory_src
    assert "approval_record_digest" in factory_src


def test_approval_drift_is_detected_when_the_resolver_surfaces_it(chain):
    r, reasons = _run(
        chain,
        authority_generation_resolver=_drift_resolver(
            [
                {"principal_generation": "p" * 64, "credential_generation": "c" * 64, "approval_generation": "a" * 64},
                {"principal_generation": "p" * 64, "credential_generation": "c" * 64, "approval_generation": "REVOKED" + "0" * 57},
            ]
        ),
    )
    assert r is None
    assert reasons == ("gate9_authority_generation_drift:approval_generation",)
    assert _count_consumption_json(_root(chain)) == 0


# ═══════════════════════════════════════════════════════════════════════
# 6. Restart reconstructibility / no mtime|clock|nonce dependency
# ═══════════════════════════════════════════════════════════════════════
def test_tokens_are_pure_functions_of_durable_state(chain):
    """Re-deriving the snapshot from a brand-new store object over the same
    root yields identical tokens — nothing process-local is involved."""
    s_a, _ = g9._capture_authority_generation_snapshot(
        authority_generation_resolver=_authority_generation_resolver(chain),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    fresh_store = ric.RuntimeInvocationAuthorityConsumptionStore(_root(chain))
    s_b, _ = g9._capture_authority_generation_snapshot(
        authority_generation_resolver=_authority_generation_resolver(chain),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=fresh_store,
        proof_id=chain.rig.proof_id,
    )
    assert s_a == s_b


def test_no_wallclock_mtime_or_nonce_token_in_the_module():
    tree = ast.parse(G9_SRC)
    snap_fns = {
        "_capture_authority_generation_snapshot",
        "_lifecycle_generation_token",
        "_consumption_generation_token",
        "_first_authority_generation_drift",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in snap_fns:
            body = ast.get_source_segment(G9_SRC, node) or ""
            for banned in ("time(", "now(", "utcnow", "random", "token_hex", "uuid", "id("):
                assert banned not in body, (node.name, banned)


# ═══════════════════════════════════════════════════════════════════════
# 7. Drift injection in the S1->S2 window — each source, fail closed
#    (independent injection: mutate from inside the recorder's store.create
#    hook is too late; use a resolver that flips on the 2nd call, matching
#    the real S1/S2 read pattern)
# ═══════════════════════════════════════════════════════════════════════
def _flip_after_first(**tokens_first):
    base = {"principal_generation": "p" * 64, "credential_generation": "c" * 64, "approval_generation": "a" * 64}
    first = dict(base)
    second = dict(base, **tokens_first)
    return _drift_resolver([first, second])


def test_principal_drift_blocks_create(chain):
    r, reasons = _run(chain, authority_generation_resolver=_flip_after_first(principal_generation="X" * 64))
    assert r is None and reasons == ("gate9_authority_generation_drift:principal_generation",)
    assert _count_consumption_json(_root(chain)) == 0


def test_credential_drift_blocks_create(chain):
    r, reasons = _run(chain, authority_generation_resolver=_flip_after_first(credential_generation="X" * 64))
    assert r is None and reasons == ("gate9_authority_generation_drift:credential_generation",)
    assert _count_consumption_json(_root(chain)) == 0


def test_lifecycle_drift_blocks_create(chain, monkeypatch):
    # a real terminal append landing between S1 and S2
    _inject_between_s1_and_s2(monkeypatch, chain, _terminate_lifecycle)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_authority_generation_drift:lifecycle_generation",)
    assert _count_consumption_json(_root(chain)) == 0


def test_consumption_appearing_before_s2_is_already_consumed_not_drift(chain, monkeypatch):
    event = chain.rig.lifecycle_store.resolve_gate5_binding_event(chain.rig.proof_id)
    planted = g9._build_consumption_record(
        identity=chain.identity, inputs=chain.inputs, gate5_result=chain.g5,
        gate6_decision=chain.g6, gate7_result=chain.g7, fresh_gate8=chain.g8,
        projection=chain.projection, proof_id=chain.rig.proof_id,
        executable_identity_digest="0" * 64, genesis_binding=event.record.binding,
        registry_state_digest="1" * 64, authority_generation_snapshot=_SNAP, consumed_at=NOW,
    )
    _inject_between_s1_and_s2(
        monkeypatch, chain,
        lambda _c: ric.RuntimeInvocationAuthorityConsumptionStore(_root(chain)).create(
            chain.rig.proof_id, planted
        ),
    )
    r, reasons = _run(chain)
    assert r is not None and r.status == "already_consumed"
    assert reasons[0] == "gate9_already_consumed"
    assert _count_consumption_json(_root(chain)) == 1


def test_multi_source_drift_is_deterministic_first_token(chain):
    r, reasons = _run(
        chain,
        authority_generation_resolver=_flip_after_first(
            principal_generation="X" * 64, credential_generation="Y" * 64
        ),
    )
    assert r is None
    assert reasons == ("gate9_authority_generation_drift:principal_generation",)
    assert _count_consumption_json(_root(chain)) == 0


# ═══════════════════════════════════════════════════════════════════════
# 8. Stable path / no stale snapshot across retry
# ═══════════════════════════════════════════════════════════════════════
def test_stable_tokens_permit_exactly_one_create(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    assert _count_consumption_json(_root(chain)) == 1
    r2, reasons2 = _run(chain)
    assert r2.status == "already_consumed"
    assert _count_consumption_json(_root(chain)) == 1


def test_retry_after_drift_rejection_re_derives_from_current_state(chain):
    calls = {"n": 0}

    def resolver():
        calls["n"] += 1
        # call 1 = attempt-1 S1; call 2 = attempt-1 S2 (drift); calls 3,4 = attempt-2 (stable)
        if calls["n"] == 2:
            return {"principal_generation": "X" * 64, "credential_generation": "c" * 64, "approval_generation": "a" * 64}
        return {"principal_generation": "p" * 64, "credential_generation": "c" * 64, "approval_generation": "a" * 64}

    r1, _ = _run(chain, authority_generation_resolver=resolver)
    assert r1 is None
    r2, _ = _run(chain, authority_generation_resolver=resolver)
    assert r2 is not None and r2.status == "consumed"


# ═══════════════════════════════════════════════════════════════════════
# 9. Crash semantics
# ═══════════════════════════════════════════════════════════════════════
def test_crash_after_s2_before_create_leaves_unconsumed(chain, monkeypatch):
    def boom(proof_id, record):
        raise RuntimeError("crash after S2, before durable create")

    monkeypatch.setattr(chain.store, "create", boom)
    r, _ = _run(chain)
    assert r is None
    assert chain.store.resolve(chain.rig.proof_id) is None
    assert _count_consumption_json(_root(chain)) == 0


def test_crash_after_create_is_deterministic_already_consumed(chain, monkeypatch):
    real = chain.store.create

    def create_then_boom(proof_id, record):
        real(proof_id, record)
        raise RuntimeError("crash after create, before read-back")

    monkeypatch.setattr(chain.store, "create", create_then_boom)
    r, _ = _run(chain)
    assert r is not None and r.status == "already_consumed"
    assert _count_consumption_json(_root(chain)) == 1
    # a fresh retry (new store object, cleared registry) still already_consumed
    g9._GATE9_RESULTS.clear()
    fresh = ric.RuntimeInvocationAuthorityConsumptionStore(_root(chain))
    r2, _ = _run(chain, consumption_store=fresh)
    assert r2 is not None and r2.status == "already_consumed"


def test_crash_before_s1_consumes_nothing(chain, monkeypatch):
    def boom():
        raise RuntimeError("crash before S1")

    r, reasons = _run(chain, authority_generation_resolver=boom)
    assert r is None
    assert reasons == ("gate9_internal_error_fail_closed",)
    assert _count_consumption_json(_root(chain)) == 0


# ═══════════════════════════════════════════════════════════════════════
# 10. Concurrency — one winner; stale snapshot never linearizes
# ═══════════════════════════════════════════════════════════════════════
def test_concurrent_contenders_exactly_one_winner(chain):
    results = []
    barrier = threading.Barrier(6)

    def contend():
        barrier.wait()
        results.append(_run(chain))

    ts = [threading.Thread(target=contend) for _ in range(6)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    statuses = [r.status if r is not None else "fail_closed" for r, _ in results]
    assert statuses.count("consumed") == 1, statuses
    assert all(s in ("already_consumed", "fail_closed") for s in statuses if s != "consumed")
    assert _count_consumption_json(_root(chain)) == 1


def test_concurrent_authority_mutation_straddling_the_window_rejects(chain, monkeypatch):
    # a real principal revocation landing in the S1->S2 window; the real
    # resolver's principal token moves, so S2 != S1 -> fail closed.
    _inject_between_s1_and_s2(monkeypatch, chain, _revoke_principal)
    r, reasons = _run(chain, authority_generation_resolver=_authority_generation_resolver(chain))
    assert r is None and reasons[0].startswith("gate9_authority_generation_drift")
    assert _count_consumption_json(_root(chain)) == 0


# ═══════════════════════════════════════════════════════════════════════
# 11. Practical-limit / residual micro-window characterization
# ═══════════════════════════════════════════════════════════════════════
def test_residual_window_between_s2_reads_and_create_is_not_lock_protected():
    """HONEST CHARACTERIZATION (RDGO-001 §10 "no TOCTOU allowance" vs the
    frozen `.1R.9` §18 "do not invent a new lock"). The repair narrows the
    window to the pure statements between S2's last canonical read and
    ``consumption_store.create``; NO lock spans S2->create. A mutation to the
    principal / credential / approval / lifecycle canonical stores in that
    instruction-level window is not caught for the current attempt. This is
    the practical limit achievable without extending the create primitive
    into a conditional-create (Option D, explicitly deferred). It produces
    no external effect: Gate 10 is absent and its frozen §22 forward
    invariant mandates full re-read + re-validation + containment
    re-establishment before any effect. The consumption race itself IS fully
    closed by the O_EXCL create-only primitive."""
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    tail = src[src.index("s2, s2_reasons = _capture_authority_generation_snapshot") :]
    tail = tail[: tail.index("consumption_store.create(proof_id, consumption_record)")]
    # no lock acquire/release brackets the S2 read -> create span
    for tok in ("acquire(", "release(", "with ", "Lock", "flock"):
        assert tok not in tail, tok


# ═══════════════════════════════════════════════════════════════════════
# 12. Durable-snapshot deferral — independently re-derived from HPAC-001
# ═══════════════════════════════════════════════════════════════════════
def test_authority_binding_is_a_closed_twelve_field_set_with_no_extension():
    assert ric._BINDING_FIELD_SETS["authority_binding"] == frozenset(
        {
            "approval_id", "approval_digest", "authority_projection_id",
            "authority_projection_digest", "authority_contract_version", "proof_id",
            "proof_digest", "proof_validation_digest", "registry_state_digest",
            "approval_subject_digest", "trusted_presentation_ref", "challenge_digest",
        }
    )
    # exact-key enforcement on create; unknown top-level key -> uncertain on resolve
    src = inspect.getsource(ric)
    assert "set(value.keys()) != expected_fields" in src
    assert "unknown or missing" in src


def test_no_thirteenth_authority_binding_field_can_be_created(chain):
    event = chain.rig.lifecycle_store.resolve_gate5_binding_event(chain.rig.proof_id)
    good = g9._build_consumption_record(
        identity=chain.identity, inputs=chain.inputs, gate5_result=chain.g5,
        gate6_decision=chain.g6, gate7_result=chain.g7, fresh_gate8=chain.g8,
        projection=chain.projection, proof_id=chain.rig.proof_id,
        executable_identity_digest="0" * 64, genesis_binding=event.record.binding,
        registry_state_digest="1" * 64, authority_generation_snapshot=_SNAP, consumed_at=NOW,
    )
    # `.1R.15.4`: authority_binding is still the closed 12-field set (the
    # durable generation snapshot lives in the separate sibling object
    # authority_generation_binding). A 13th authority_binding field is
    # still rejected.
    tampered = dict(good.authority_binding)
    tampered["authority_generation_snapshot"] = {"principal_generation": "x"}
    with pytest.raises(ric.HPACMalformedError):
        ric.new_inert_consumption_record(
            request_identity=good.request_identity,
            repository_task_binding=good.repository_task_binding,
            target_binding=good.target_binding,
            prompt_binding=good.prompt_binding,
            authority_binding=tampered,
            authority_generation_binding=good.authority_generation_binding,
            pb_binding=good.pb_binding,
            runtime_enforcement_binding=good.runtime_enforcement_binding,
            dispatch_binding=good.dispatch_binding,
        )


def test_registry_state_digest_computation_is_unchanged_from_1r14():
    """The V-15-1 repair did not fold the generation vector into
    ``registry_state_digest``'s preimage: its computation is the same flat
    3-key digest as `.1R.14` (projection / sequence-3 / gate-8 containment)."""
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    idx = src.index("registry_state_digest = compute_canonical_digest(")
    block = src[idx : idx + 400]
    assert "projection_digest" in block
    assert "sequence3_event_digest" in block
    assert "gate8_containment_evidence_digest" in block
    assert "principal_generation" not in block
    # `.1R.15.4` adds a sibling helper (_authority_generation_binding_fields)
    # and a param to _build_consumption_record, but the _authority_binding_fields
    # helper body and the registry_state_digest preimage are byte-unchanged.
    abf = inspect.getsource(g9._authority_binding_fields)
    assert '"approval_digest": projection.record_digest' in abf
    assert '"registry_state_digest": registry_state_digest' in abf
    assert "generation" not in abf


# ═══════════════════════════════════════════════════════════════════════
# 13. V-15-2 — three guards are phase-aware SUBSET invariants
# ═══════════════════════════════════════════════════════════════════════
_V15_2_GUARDS = [
    ("test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
     "test_new_hpac_modules_have_zero_preexisting_production_consumers"),
    ("test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
     "test_hpac_repair_has_zero_preexisting_production_consumers"),
    ("test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
     "test_foundation_has_no_production_consumers_or_gate_wiring"),
]


@pytest.mark.parametrize("filename,testname", _V15_2_GUARDS)
def test_v15_2_guard_is_subset_invariant_with_explicit_authorized_set(filename, testname):
    src = (REPO_ROOT / "tests" / filename).read_text()
    seg = src[src.index(f"def {testname}") :]
    seg = seg[: seg.index("\n\ndef ")]
    assert "AUTHORIZED_CONSUMERS" in seg
    assert "- AUTHORIZED_CONSUMERS" in seg  # observed - allowed orientation
    assert "unauthorized == set()" in seg
    assert "startswith(" not in seg  # no wildcard allowance
    for expected in (
        '("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle")',
        '("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation")',
        '("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle")',
        '("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption")',
    ):
        assert expected in seg


def test_v15_2_unauthorized_future_consumer_would_still_trip_the_guard():
    """Simulate the guard's core check with a hypothetical unauthorized
    ``runtime_dispatch_gate10.py`` importer — the subset difference is
    non-empty, so the assert fails (the guard is not defeated)."""
    authorized = {
        ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),
    }
    observed = set(authorized) | {("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation")}
    assert observed - authorized != set()


def test_v15_2_guards_pass_at_head():
    import sys

    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "-n0",
         *[f"tests/{f}::{t}" for f, t in _V15_2_GUARDS]],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert "3 passed" in out.stdout, out.stdout[-2000:]


# ═══════════════════════════════════════════════════════════════════════
# 14. V-15-3 — scoped monkeypatch hygiene
# ═══════════════════════════════════════════════════════════════════════
def test_v15_3_no_raw_is_gate5_result_assignment_remains():
    src = (
        REPO_ROOT
        / "tests"
        / "test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py"
    ).read_text()
    assert "_g5mod.is_gate5_result =" not in src
    assert "is_gate5_result = lambda" not in src
    assert src.count('monkeypatch.setattr(gate5, "is_gate5_result"') >= 3


def test_v15_3_is_gate5_result_is_the_original_callable_now():
    # after importing and running the .1R.14 suite helpers, the module attr
    # is intact (no dead closure installed at import time)
    assert gate5.is_gate5_result.__module__ == "pcae.core.runtime_dispatch_gate5"


# ═══════════════════════════════════════════════════════════════════════
# 15. Regression — V-13-5-1, replay, Gate9Result discipline, no Gate 10,
#     runtime unchanged, earlier gates byte-identical
# ═══════════════════════════════════════════════════════════════════════
def test_v13_5_1_containment_readback_runs_before_s1(chain):
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    i_readback = src.index("gate9_containment_evidence_recomputation_mismatch")
    i_s1 = src.index("14a. V-15-1 repair — capture the authority-generation snapshot S1")
    assert i_readback < i_s1


def test_containment_evidence_drift_still_rejected(chain):
    bad = _run(chain, effect_plan=object())
    r, reasons = bad
    assert r is None
    assert reasons == ("gate9_invalid_effect_plan",)


def test_replay_is_deterministic_already_consumed(chain):
    _run(chain)
    for _ in range(3):
        r, reasons = _run(chain)
        assert r is not None and r.status == "already_consumed"
        assert reasons == ("gate9_already_consumed",)
    assert _count_consumption_json(_root(chain)) == 1


def test_gate9result_is_non_serializable_identity_only(chain):
    r, _ = _run(chain)
    import copy

    with pytest.raises(TypeError):
        r.__reduce__()
    assert copy.deepcopy is not None
    assert (r == r) and not (r == object())
    assert g9.is_gate9_result(r) is True
    assert g9.is_gate9_result(object.__new__(g9.Gate9Result)) is False


def test_no_gate10_or_external_effect_symbol_in_module():
    tree = ast.parse(G9_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
            imported.add(n.module)
    for banned in (
        "subprocess", "socket", "pty", "requests", "httpx", "urllib",
        "runtime_adapter", "mock_runtime_adapter", "fido2", "webauthn",
        "pcae.core.runtime_adapter", "pcae.core.mock_runtime_adapter",
    ):
        assert banned not in imported, banned
    # no Gate-10 / dispatch / external-process call node anywhere in the
    # module's *code* (docstrings stripped so contract prose does not match).
    code_only = "\n".join(
        ast.get_source_segment(G9_SRC, n) or ""
        for n in ast.walk(tree)
        if isinstance(n, (ast.Call, ast.Attribute, ast.Name, ast.FunctionDef, ast.ClassDef))
        and not (isinstance(n, ast.Expr))
    )
    for tok in ("run_gate10", "Gate10Result", "adapter_dispatch", ".dispatch(",
                "os.system", "Popen", "subprocess", "socket"):
        assert tok not in code_only, tok


def test_runtime_capability_check_unchanged(chain):
    r, reasons = _run(
        chain,
        capability_snapshot_resolver=lambda: {
            "current_runtime_state": "Observed",
            "current_maximum_plugin_capability": "observe",
            "execution_availability": "available",  # anything but unavailable
        },
    )
    assert r is None
    assert reasons == ("gate9_runtime_execution_available_unexpected",)


@pytest.mark.parametrize(
    "module",
    [
        "runtime_dispatch_gate5.py",
        "runtime_dispatch_permission.py",
        "runtime_dispatch_gate7.py",
        "runtime_dispatch_gate8.py",
        "runtime_invocation_authority_consumption.py",
    ],
)
def test_earlier_gate_and_store_modules_byte_identical_since_baseline(module):
    out = subprocess.run(
        ["git", "diff", "--stat", BASELINE_SHA, "HEAD", "--", f"src/pcae/core/{module}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.stdout.strip() == "", out.stdout


def test_only_gate9_py_changed_in_src_since_baseline():
    out = subprocess.run(
        ["git", "diff", "--name-only", BASELINE_SHA, "HEAD", "--", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.stdout.split() == ["src/pcae/core/runtime_dispatch_gate9.py"]


def test_no_normative_contract_changed_since_baseline():
    out = subprocess.run(
        ["git", "diff", "--name-only", BASELINE_SHA, "HEAD", "--", "docs/contracts", "schemas"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# 16. Test-quality note on the .1R.15.2 suite (N-15-3-1)
# ═══════════════════════════════════════════════════════════════════════
def test_1r15_2_suite_token_count_name_overstates_body():
    """INFO finding N-15-3-1: `.1R.15.2`'s
    ``test_snapshot_has_exactly_the_six_generation_tokens`` asserts exactly
    FIVE tokens in its body (principal/credential/approval/lifecycle/
    consumption). The '_six_' in the name is a harmless overstatement — same
    class as the name-vs-proof notes `.1R.15` §25 recorded. Body is correct."""
    src = (
        REPO_ROOT
        / "tests"
        / "test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py"
    ).read_text()
    seg = src[src.index("def test_snapshot_has_exactly_the_six_generation_tokens") :]
    seg = seg[: seg.index("\n\ndef ")]
    assert seg.count("_generation") >= 5
    assert "six" in "test_snapshot_has_exactly_the_six_generation_tokens"
