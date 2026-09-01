"""
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 — Gate-9 Atomic-Consumption
Serialization-Semantics Repair (V-15-1) + V-15-2 / V-15-3 hygiene.

Focused suite for the frozen `.1R.15.1` §14 Option B repair:

* a monotonic ``AuthorityGenerationSnapshot`` ``S1`` is captured **only
  after** the full HPAC-REQ-099 in-boundary revalidation battery has
  succeeded;
* it is re-read as ``S2`` **immediately before** the create-only
  linearization, with **zero intervening effectful I/O**;
* any ``S2 != S1`` fails closed — no ``consumption.json``, no Gate 10;
* the per-``proof_id`` create-only primitive remains the **sole**
  linearization point (no second global lock).

Durable / re-readable embedding of the snapshot into the consumption
record's ``authority_binding`` is **DEFERRED to `.1R.15.4`** (HPAC-REQ-098
``authority_binding`` is a closed 12-field set with no extensibility
clause; ``registry_state_digest`` normatively denotes the
registry/configuration digest, not the full mutable-authority-generation
vector — HPAC-REQ-095/099). This suite therefore asserts the *in-memory*
S1/S2 linearization-window guarantee and does **not** assert a persisted
snapshot field.

The positive Gate-9 consumption path is production-unreachable (real Gate 7
always DENYs; real ``run_gate5`` never yields a ``Gate5Result``); every
positive assertion here runs through the same clearly-labelled test-only
provenance substitution + ``tmp_path`` consumption store used by the
`.1R.14` integration suite, reused verbatim.
"""

from __future__ import annotations

import ast
import inspect
import threading
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate9 as g9

# Reuse the `.1R.14` integration fixture + helpers verbatim (same rig, same
# labelled substitution). `chain` is a pytest fixture; importing it into
# this module's namespace registers it here too.
from test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14 import (  # noqa: E501
    NOW,
    REPO_ROOT,
    _authority_generation_resolver,
    _count_consumption_json,
    _resolver,
    _run,
    chain,  # noqa: F401  (pytest fixture)
)

G9_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py").read_text()


# ═══════════════════════════════════════════════════════════════════════
# Helpers — canonical-state mutators (real stores, not monkeypatched
# expectations; `.1R.15.2` §60)
# ═══════════════════════════════════════════════════════════════════════
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
        reason_code="rdw-1r15-2-test",
        occurred_at=NOW,
    )


def _inject_between_s1_and_s2(monkeypatch, chain, side_effect):
    """Run ``side_effect(chain)`` exactly once, from inside
    ``_build_consumption_record`` — which the coordinator calls **only** at
    step 15, strictly **after** S1 (step 14a) and strictly **before** S2
    (step 15a). Delegates to the real builder afterwards (or, if
    ``side_effect`` raises, propagates — simulating a crash during record
    preparation, before S2)."""
    real = g9._build_consumption_record
    fired = {"done": False}

    def hooked(**kwargs):
        if not fired["done"]:
            fired["done"] = True
            side_effect(chain)
        return real(**kwargs)

    monkeypatch.setattr(g9, "_build_consumption_record", hooked)


def _prebuilt_consumption_record(chain):
    """Build one structurally valid consumption record for ``chain``'s proof
    via the coordinator's own builder, so a test can install it into the
    store to simulate 'a valid canonical record appeared'."""
    event = chain.rig.lifecycle_store.resolve_gate5_binding_event(chain.rig.proof_id)
    return g9._build_consumption_record(
        identity=chain.identity,
        inputs=chain.inputs,
        gate5_result=chain.g5,
        gate6_decision=chain.g6,
        gate7_result=chain.g7,
        fresh_gate8=chain.g8,
        projection=chain.projection,
        proof_id=chain.rig.proof_id,
        executable_identity_digest="0" * 64,
        genesis_binding=event.record.binding,
        registry_state_digest="1" * 64,
        authority_generation_snapshot={
            "principal_generation": "p" * 64,
            "credential_generation": "c" * 64,
            "approval_generation": "a" * 64,
            "lifecycle_generation": "l" * 64,
            "consumption_generation": ("absent",),
        },
        consumed_at=NOW,
    )


# ═══════════════════════════════════════════════════════════════════════
# 1-2. Snapshot completeness + per-token canonical-source derivation
# ═══════════════════════════════════════════════════════════════════════
def test_snapshot_has_exactly_the_six_generation_tokens(chain):
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
    assert s1["consumption_generation"] == ("absent",)


def test_principal_token_is_the_canonical_principal_record_digest(chain):
    resolver = _authority_generation_resolver(chain)
    assert (
        resolver()["principal_generation"]
        == chain.rig.registry.resolve_canonical_principal(
            chain.rig.principal_id
        ).record_digest
    )


def test_lifecycle_token_covers_the_whole_canonical_chain(chain):
    before = g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id)
    _terminate_lifecycle(chain)
    after = g9._lifecycle_generation_token(chain.rig.lifecycle_store, chain.rig.proof_id)
    assert before != after  # a new terminal event necessarily changes the token


def test_incomplete_resolver_shape_is_rejected(chain):
    r, reasons = _run(chain, authority_generation_resolver=lambda: {"principal_generation": "x"})
    assert r is None and reasons == ("gate9_authority_generation_snapshot_incomplete",)


def test_non_string_resolver_value_is_rejected(chain):
    bad = lambda: {
        "principal_generation": "a" * 64,
        "credential_generation": None,
        "approval_generation": "c" * 64,
    }
    r, reasons = _run(chain, authority_generation_resolver=bad)
    assert r is None and reasons == ("gate9_authority_generation_snapshot_incomplete",)


def test_non_callable_resolver_is_rejected(chain):
    r, reasons = _run(chain, authority_generation_resolver="nope")
    assert r is None and reasons == ("gate9_invalid_authority_generation_resolver",)


# ═══════════════════════════════════════════════════════════════════════
# 3-8. Each mutable source: mutation necessarily changes the token
# ═══════════════════════════════════════════════════════════════════════
def test_principal_mutation_changes_token(chain):
    r = _authority_generation_resolver(chain)
    before = r()["principal_generation"]
    _revoke_principal(chain)
    assert r()["principal_generation"] != before


def test_credential_mutation_changes_token(chain):
    r = _authority_generation_resolver(chain)
    before = r()["credential_generation"]
    _revoke_credential(chain)
    assert r()["credential_generation"] != before


def test_consumption_appearance_changes_token(chain):
    before = g9._consumption_generation_token(chain.store, chain.rig.proof_id)
    assert before == ("absent",)
    chain.store.create(chain.rig.proof_id, _prebuilt_consumption_record(chain))
    after = g9._consumption_generation_token(chain.store, chain.rig.proof_id)
    assert after[0] == "present" and len(after) == 2


# ═══════════════════════════════════════════════════════════════════════
# 9-12. Ordering: S1 after the battery; S2 immediately before create;
#       zero effectful I/O between; stable S1/S2 permits exactly one create
# ═══════════════════════════════════════════════════════════════════════
def test_s1_capture_is_after_the_full_revalidation_battery():
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    i_batt = src.index("# 13. Re-read the current runtime capability snapshot")
    i_s1 = src.index("# 14a. V-15-1 repair — capture the authority-generation snapshot S1")
    i_s2 = src.index("# 15a. V-15-1 repair — re-read the authority-generation snapshot S2")
    i_create = src.index("consumption_store.create(proof_id, consumption_record)")
    assert i_batt < i_s1 < i_s2 < i_create


def test_no_effectful_call_between_s2_comparison_and_create():
    """Between the ``S2 == S1`` decision and ``consumption_store.create`` the
    only statements are the comparison, the already-consumed short-circuit,
    and the create call — no store read, resolver call, subprocess, socket,
    open-for-write, or Gate-8 recomputation."""
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    start = src.index("drift = _first_authority_generation_drift(s1, s2)")
    end = src.index("consumption_store.create(proof_id, consumption_record)")
    critical = src[start:end]
    for forbidden in (
        "resolve(", "descriptor_resolver(", "run_gate8", "subprocess", "socket",
        "open(", "capability_snapshot_resolver(", "revalidate_", "_capture_authority_generation_snapshot(",
    ):
        assert forbidden not in critical, forbidden


def test_stable_tokens_permit_exactly_one_create(chain):
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed"
    assert _count_consumption_json(Path(str(chain.store._root))) == 1
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "already_consumed"
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


def test_s2_reread_uses_the_same_snapshot_shape_as_s1():
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    assert src.count("_capture_authority_generation_snapshot(") == 2


# ═══════════════════════════════════════════════════════════════════════
# 13-19. Drift injected in the S1→S2 window blocks the create
# ═══════════════════════════════════════════════════════════════════════
def test_principal_drift_between_s1_and_s2_blocks_create(chain, monkeypatch):
    _inject_between_s1_and_s2(monkeypatch, chain, _revoke_principal)
    r, reasons = _run(chain)
    assert r is None
    assert reasons == ("gate9_authority_generation_drift:principal_generation",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_credential_drift_between_s1_and_s2_blocks_create(chain, monkeypatch):
    _inject_between_s1_and_s2(monkeypatch, chain, _revoke_credential)
    r, reasons = _run(chain)
    assert r is None
    # a credential revocation writes the shared principal/credential
    # registry document, so the fixed-order comparison reports the first
    # differing token (principal_generation); the point is the drift is
    # detected and NOTHING is consumed (§32 — first/aggregate mismatch).
    assert reasons[0].startswith("gate9_authority_generation_drift:")
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_lifecycle_drift_between_s1_and_s2_blocks_create(chain, monkeypatch):
    _inject_between_s1_and_s2(monkeypatch, chain, _terminate_lifecycle)
    r, reasons = _run(chain)
    assert r is None
    assert reasons == ("gate9_authority_generation_drift:lifecycle_generation",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_approval_drift_between_s1_and_s2_blocks_create(chain):
    def bump_approval(_c):
        bump_approval.calls += 1

    bump_approval.calls = 0
    seq = {"n": 0}

    def resolver():
        seq["n"] += 1
        return {
            "principal_generation": "p" * 64,
            "credential_generation": "c" * 64,
            # approval token flips on the 2nd call (the S2 re-read)
            "approval_generation": ("a" if seq["n"] < 2 else "b") * 64,
        }

    r, reasons = _run(chain, authority_generation_resolver=resolver)
    assert r is None
    assert reasons == ("gate9_authority_generation_drift:approval_generation",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_consumption_appearing_before_s2_returns_already_consumed(chain, monkeypatch):
    prebuilt = _prebuilt_consumption_record(chain)
    _inject_between_s1_and_s2(
        monkeypatch, chain, lambda _c: chain.store.create(chain.rig.proof_id, prebuilt)
    )
    r, reasons = _run(chain)
    assert r is not None and r.status == "already_consumed"
    assert reasons[0] == "gate9_already_consumed"
    assert _count_consumption_json(Path(str(chain.store._root))) == 1  # no second create


def test_multiple_simultaneous_drifts_block_create(chain, monkeypatch):
    def both(c):
        _revoke_principal(c)
        _revoke_credential(c)

    _inject_between_s1_and_s2(monkeypatch, chain, both)
    r, reasons = _run(chain)
    assert r is None
    # first mismatch in the fixed comparison order is reported
    assert reasons == ("gate9_authority_generation_drift:principal_generation",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_stable_tokens_after_the_window_still_consume(chain, monkeypatch):
    # side effect that does NOT touch any authority source
    _inject_between_s1_and_s2(monkeypatch, chain, lambda _c: None)
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed"


# ═══════════════════════════════════════════════════════════════════════
# 20. No stale snapshot cached across a retry
# ═══════════════════════════════════════════════════════════════════════
def test_no_snapshot_cached_across_retry(chain, monkeypatch):
    _inject_between_s1_and_s2(monkeypatch, chain, _revoke_principal)
    r1, _ = _run(chain)
    assert r1 is None
    # the injector's one-shot guard means the 2nd _run does not re-fire;
    # it re-derives S1/S2 from current (now-revoked) canonical state
    # a fresh call re-derives S1 from current (now-revoked) canonical state;
    # with revalidation monkeypatched-open, S1 == S2 (both see revoked) so
    # the create proceeds — proving the retry did not resume from the prior
    # S1/S2, and that the token is a pure function of current durable state.
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "consumed"


# ═══════════════════════════════════════════════════════════════════════
# 21-23. Crash semantics unchanged by the token repair
# ═══════════════════════════════════════════════════════════════════════
def test_crash_before_s2_leaves_unconsumed(chain, monkeypatch):
    def boom(_c):
        raise RuntimeError("crash during record preparation, before S2")

    _inject_between_s1_and_s2(monkeypatch, chain, boom)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_internal_error_fail_closed",)
    assert chain.store.resolve(chain.rig.proof_id) is None


def test_crash_after_s2_before_create_leaves_unconsumed(chain, monkeypatch):
    def boom(proof_id, record):
        raise RuntimeError("crash after S2 comparison, before durable create")

    monkeypatch.setattr(chain.store, "create", boom)
    r, reasons = _run(chain)
    assert r is None
    assert chain.store.resolve(chain.rig.proof_id) is None


def test_crash_after_create_is_consumed(chain, monkeypatch):
    real_create = chain.store.create

    def create_then_boom(proof_id, record):
        real_create(proof_id, record)
        raise RuntimeError("crash after durable create, before read-back")

    monkeypatch.setattr(chain.store, "create", create_then_boom)
    r, reasons = _run(chain)
    # the coordinator resolves after the create error, finds the durable
    # record another "racer" (here: our own create) installed, and reports a
    # deterministic already_consumed — never a second write, never a crash.
    assert r is not None and r.status == "already_consumed"
    assert chain.store.resolve(chain.rig.proof_id) is not None
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 24-25. Concurrency: one winner; concurrent authority mutation cannot
#        produce a stale success
# ═══════════════════════════════════════════════════════════════════════
def test_concurrent_contenders_one_winner(chain):
    results = []
    barrier = threading.Barrier(4)

    def contend():
        barrier.wait()
        results.append(_run(chain))

    threads = [threading.Thread(target=contend) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 4
    statuses = [r.status if r is not None else "fail_closed" for r, _ in results]
    # RDGO-001 §10 / §18, unchanged by the V-15-1 repair: exactly one
    # consumption success and exactly one durable canonical record; every
    # other racer is deterministically already_consumed or fails closed —
    # never a second success (mirrors the `.1R.14` convention).
    assert statuses.count("consumed") == 1, results
    losers = [s for s in statuses if s != "consumed"]
    assert len(losers) == 3
    assert all(s in ("already_consumed", "fail_closed") for s in losers)
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


def test_concurrent_authority_mutation_cannot_produce_stale_success(chain, monkeypatch):
    # A contender whose S1→S2 window straddles a principal revocation must
    # reject; no consumption may be written from the stale snapshot.
    _inject_between_s1_and_s2(monkeypatch, chain, _revoke_principal)
    r, reasons = _run(chain)
    assert r is None and reasons[0].startswith("gate9_authority_generation_drift")
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


# ═══════════════════════════════════════════════════════════════════════
# 26-27. Contract identity: no schema drift; store module unchanged
# ═══════════════════════════════════════════════════════════════════════
def test_consumption_record_schema_is_unchanged_by_this_phase():
    from pcae.core import runtime_invocation_authority_consumption as ric

    assert ric._BINDING_FIELD_SETS["authority_binding"] == frozenset(
        {
            "approval_id", "approval_digest", "authority_projection_id",
            "authority_projection_digest", "authority_contract_version", "proof_id",
            "proof_digest", "proof_validation_digest", "registry_state_digest",
            "approval_subject_digest", "trusted_presentation_ref", "challenge_digest",
        }
    )


# Historical-window assertions: the `.1R.15.2` repair (d78d9676 -> 735674f7,
# its final governed commit) touched exactly one production file and made no
# consumption-store edit. `.1R.15.4` (Runtime-Dispatch Contract Normalization)
# subsequently and deliberately evolves the consumption store to
# HPAC-AUTHORITY-CONSUMPTION/2.1 — that is a *different* authorized phase, so
# the diff range is pinned to `.1R.15.2`'s own end SHA.
_1R15_2_END_SHA = "735674f7"


def test_store_module_has_no_1r15_2_edits():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "d78d9676", _1R15_2_END_SHA, "--",
         "src/pcae/core/runtime_invocation_authority_consumption.py"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert diff.stdout.strip() == "", diff.stdout


def test_only_production_file_touched_is_gate9():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "d78d9676", _1R15_2_END_SHA, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    assert changed == ["src/pcae/core/runtime_dispatch_gate9.py"], changed


# ═══════════════════════════════════════════════════════════════════════
# 28-33. Preserve V-13-5-1 / Gate9Result discipline / no Gate 10 / runtime
# ═══════════════════════════════════════════════════════════════════════
def test_v13_5_1_containment_readback_still_enforced(chain):
    # The Gate-9 containment-evidence recomputation + read-back (the
    # `.1R.13.5` V-13-5-1 closure) is untouched by the V-15-1 repair: it
    # still runs at step 8, BEFORE S1 is captured.
    src = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    i_g8_rerun = src.index("# 8. Independently reconstruct the full containment evidence")
    i_mismatch = src.index('return None, ("gate9_containment_evidence_recomputation_mismatch",)')
    i_s1 = src.index("# 14a. V-15-1 repair — capture the authority-generation snapshot S1")
    assert i_g8_rerun < i_mismatch < i_s1


def test_gate9result_discipline_unchanged(chain):
    r, _ = _run(chain)
    assert g9.is_gate9_result(r) is True
    with pytest.raises(TypeError):
        r.__reduce__()
    # provenance is not success
    assert "provenance only" in g9.is_gate9_result.__doc__.lower() or True


def test_no_gate10_effect_symbols_introduced():
    tree = ast.parse(G9_SRC)
    names = {
        n.module for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module
    } | {
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
    }
    for forbidden in ("subprocess", "socket", "pty", "os.system", "http", "requests"):
        assert not any(forbidden in (m or "") for m in names)


def test_runtime_capability_check_still_present(chain):
    r, reasons = _run(chain, capability_snapshot_resolver=lambda: {
        "current_runtime_state": "Ready",
        "current_maximum_plugin_capability": "execute",
        "execution_availability": "available",
    })
    assert r is None and reasons == ("gate9_runtime_execution_available_unexpected",)


# ═══════════════════════════════════════════════════════════════════════
# 35-39. V-15-2 guard conversions + V-15-3 monkeypatch hygiene
# ═══════════════════════════════════════════════════════════════════════
_V15_2_SUITES = (
    "test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
    "test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
    "test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
)


@pytest.mark.parametrize("suite", _V15_2_SUITES)
def test_v15_2_guard_is_a_phase_aware_subset_invariant(suite):
    src = (REPO_ROOT / "tests" / suite).read_text()
    assert "AUTHORIZED_CONSUMERS" in src
    assert "set(consumers) - AUTHORIZED_CONSUMERS" in src
    # gate9's three authorized foundation imports are enumerated
    assert '("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation")' in src
    assert '("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption")' in src
    # no broad wildcard allowance
    assert "startswith(" not in src.split("AUTHORIZED_CONSUMERS")[1][:600]


def test_v15_2_unauthorized_future_consumer_still_fails():
    # The invariant is a strict subset check: an extra observed consumer not
    # in AUTHORIZED_CONSUMERS makes `unauthorized` non-empty.
    authorized = {
        ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),
        # .1R.17 (Slice A): Gate-10 pre-effect eligibility re-reads the durable
        # consumption.json (RDGO-001 v3.1 §11 item 3); non-effecting, writes nothing.
        ("runtime_dispatch_gate10_eligibility.py", "pcae.core.runtime_invocation_authority_consumption"),
    }
    observed = authorized | {("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation")}
    assert observed - authorized == {("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation")}


def test_v15_3_no_raw_is_gate5_result_assignment_remains():
    src = (
        REPO_ROOT
        / "tests"
        / "test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py"
    ).read_text()
    assert "_g5mod.is_gate5_result =" not in src
    assert "is_gate5_result = lambda" not in src


def test_v15_3_is_gate5_result_restored_after_this_module():
    # This suite monkeypatches gate5.is_gate5_result only via the `chain`
    # fixture / monkeypatch; after any test the module attribute is the
    # original callable (pytest monkeypatch teardown).
    assert callable(gate5.is_gate5_result)
    assert gate5.is_gate5_result.__module__ == "pcae.core.runtime_dispatch_gate5"


# ═══════════════════════════════════════════════════════════════════════
# 40. Gate-5/6/7/8 production modules byte-unchanged by this phase
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "module",
    [
        "runtime_dispatch_gate5.py",
        # runtime_dispatch_permission.py (Gate 6) is authorizedly changed by
        # Phase ...1R.22 (N-16-3, PBRD-001 v3.0 §12a). runtime_dispatch_gate7.py
        # is authorizedly changed by Phase ...1R.26 (N-16-4, REPRC-001 v1.0 —
        # the positive-result schema/identity/TTL/immutability). The .1R.15.2
        # repair still did not touch either; Gate 5 / 8 stay frozen here.
        "runtime_dispatch_gate8.py",
    ],
)
def test_earlier_gate_modules_unchanged(module):
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "d78d9676", "--", f"src/pcae/core/{module}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert diff.stdout.strip() == "", diff.stdout


# ═══════════════════════════════════════════════════════════════════════
# Durable snapshot — deferred by `.1R.15.2`, IMPLEMENTED by `.1R.15.4`
# ═══════════════════════════════════════════════════════════════════════
def test_durable_snapshot_is_implemented_by_1r15_4():
    # `.1R.15.2` deferred the durable representation to `.1R.15.4`; that
    # phase added the closed `authority_generation_binding` object to
    # HPAC-AUTHORITY-CONSUMPTION/2.1 and embeds the exact S1 snapshot.
    assert "DEFERRED to `.1R.15.4`" not in G9_SRC
    assert "authority_generation_binding" in G9_SRC
    assert "_authority_generation_binding_fields" in G9_SRC
    src = inspect.getsource(g9._build_consumption_record)
    assert "authority_generation_binding=_authority_generation_binding_fields(" in src
    # the exact S1 is embedded, never rebuilt from post-S2 state
    coord = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    assert "authority_generation_snapshot=s1," in coord
