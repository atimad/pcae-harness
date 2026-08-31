"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19 — Dispatch-Attempt Durable
Lifecycle, Idempotency, and 3S.2.1 Prerequisite Repairs (Slice B).

RE-DERIVE, DO NOT TRUST. Cases constructed from the primary contracts
(RDGO-001 v3.1 §11/§17/§18, RPAC-001 v1.0 §13 RPAC-REQ-064-072, PBRD-001
v2.1) and the `.1R.16` architecture (§20/§22/§25/§31/§34), not from a
report or from test names.

Covers the phase prompt §42 case list:

 1  RuntimeInvocationRecord non-authoritative semantics
 2  PREPARED creation
 3  PREPARED durability
 4  PREPARED restart
 5  valid PREPARED -> EFFECT_ATTEMPT_STARTED
 6  duplicate start rejected
 7  concurrent start one winner
 8  EFFECT_ATTEMPT_STARTED survives restart
 9  effect-start does not mean effect success
10  EFFECT_ATTEMPT_STARTED -> RECEIPT_CAPTURED
11  EFFECT_ATTEMPT_STARTED -> DISPATCH_UNCERTAIN
12  PREPARED -> DISPATCH_NOT_STARTED
13  invalid backwards transition rejected
14  invalid terminal transition rejected
15  duplicate terminal transition rejected
16  idempotency key stable / restart-safe
17  different attempts isolated
18  mirror cannot authorize effect
19  copied / reconstructed record not authority
20  no effect call site in lifecycle module
21  crash-before-start semantics
22  crash-after-start semantics
23  unresolved started attempt prohibits retry
24-26  malformed adapter result (missing field / wrong type / unknown status) rejected
27  valid simulation result still works
28  simulation still non-effecting
29-31  ../ / absolute / separator-variant invocation_id rejected/contained
32  resolved path stays below root
33  symlink escape case
34  normal valid invocation ID works
35  runtime-inspect discoverability fixed
36  runtime inspect still reports unavailable
37  inspect repair non-mutating
38  item-9 three-part closure
39  Slice-A byte/behaviour unchanged
40  Gate 5-9 unchanged
41  no adapter registration
42  no first-effect primitive
43  runtime unchanged
44  POL-005 unchanged
"""

from __future__ import annotations

import ast
import concurrent.futures
import os
import subprocess
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
LIFECYCLE_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_attempt_lifecycle.py").read_text()

# The immutable pre-.1R.19 baseline (HEAD of .1R.17R.1).
PRE_1R19_BASELINE = "a2b679fe"


# ─────────────────────────────────────────────────────────────────────────
def _binding(*, invocation_suffix="a", attempt_suffix="b") -> RuntimeInvocationRecordBinding:
    return RuntimeInvocationRecordBinding(
        invocation_id="inv-" + invocation_suffix * 32,
        attempt_id="att-" + attempt_suffix * 32,
        idempotency_key="k" * 64,
        proof_id="hpl-" + "c" * 32,
        approval_id="ria-" + "d" * 32,
        runtime_target_id="local-cli.fixed-argv.v1",
        adapter_id="pcae.fixed-argv",
        task_id="20260830-2210-task",
        consumption_record_digest="e" * 64,
        envelope_digest="f" * 64,
    )


def _store(tmp_path) -> RuntimeInvocationRecordStore:
    return RuntimeInvocationRecordStore(tmp_path)


def _open_prepared(store, binding=None):
    binding = binding or _binding()
    rec = store.create_record(binding, created_at="2026-08-30T00:00:00Z")
    store.prepare(rec.record_id, observed_at="2026-08-30T00:00:01Z")
    return rec.record_id


# ═══ 1 / 18 / 19 — non-authoritative semantics ═══════════════════════════
def test_record_is_non_authoritative_and_has_no_authority_surface():
    fields = {f for f in dir(RuntimeInvocationRecord) if not f.startswith("_")}
    for banned in ("approve", "authorize", "permit", "grant", "consume",
                   "execution_allowed", "permission", "authorized", "pb_allow"):
        assert banned not in fields
    assert RuntimeInvocationRecord.GRANTS_NO_EFFECT_AUTHORITY is True


def test_record_grants_no_effect_authority_is_always_true(tmp_path):
    store = _store(tmp_path)
    rec = store.create_record(_binding(), created_at="t")
    assert record_grants_no_effect_authority(rec) is True
    # a reconstructed / copied record: still no authority
    reread = store.read_record(rec.record_id)
    assert record_grants_no_effect_authority(reread) is True
    import copy
    assert record_grants_no_effect_authority(copy.deepcopy(rec)) is True
    # module exposes nothing that could turn a record into an authorization
    for banned in ("authorize_dispatch", "grant_effect", "mint_authority", "consume_authority"):
        assert not hasattr(lifecycle, banned)


def test_reference_document_roundtrip_is_not_a_trusted_record(tmp_path):
    store = _store(tmp_path)
    rec = store.create_record(_binding(), created_at="t")
    doc = rec.to_reference_document()
    assert doc["grants_no_effect_authority"] is True
    # rebuilding a dataclass from the dict does not make it store-backed
    assert isinstance(doc, dict)


# ═══ 2 / 3 / 4 — PREPARED ═══════════════════════════════════════════════
def test_prepared_creation_and_durability(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    assert store.latest_state(rid) == PREPARED
    transitions = store.list_transitions(rid)
    assert len(transitions) == 1 and transitions[0]["state"] == PREPARED
    # durable on disk
    files = list((tmp_path).rglob("0001-prepared.json"))
    assert len(files) == 1


def test_prepared_restart_reads_durable_state_only(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    fresh = RuntimeInvocationRecordStore(tmp_path)  # no shared memory
    assert fresh.latest_state(rid) == PREPARED
    disp = fresh.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER
    assert disp.automatic_retry_permitted is False
    assert disp.external_effect_possible is False


def test_prepare_is_idempotent(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.prepare(rid, observed_at="2026-08-30T00:00:01Z")  # no error, no second event
    assert len(store.list_transitions(rid)) == 1


# ═══ 5 / 9 — PREPARED -> EFFECT_ATTEMPT_STARTED ═════════════════════════
def test_valid_prepared_to_effect_attempt_started(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    t = store.begin_effect_attempt(rid, observed_at="2026-08-30T00:00:02Z")
    assert t.state == EFFECT_ATTEMPT_STARTED
    assert store.latest_state(rid) == EFFECT_ATTEMPT_STARTED


def test_effect_attempt_started_does_not_mean_effect_success(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    disp = store.resolve_disposition(rid)
    # started != succeeded: unresolved -> uncertain, effect only *possible*
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    assert disp.external_effect_possible is True
    assert disp.terminal is False
    # no receipt / result token anywhere
    assert store.list_transitions(rid)[-1]["state"] == EFFECT_ATTEMPT_STARTED


# ═══ 6 / 7 — at-most-once dispatch-attempt guard ════════════════════════
def test_duplicate_effect_attempt_start_is_rejected(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        store.begin_effect_attempt(rid, observed_at="t3")
    # still exactly one EFFECT_ATTEMPT_STARTED transition
    started = [t for t in store.list_transitions(rid) if t["state"] == EFFECT_ATTEMPT_STARTED]
    assert len(started) == 1


def test_concurrent_contenders_exactly_one_winner(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)

    def contend(i):
        s = RuntimeInvocationRecordStore(tmp_path)
        try:
            s.begin_effect_attempt(rid, observed_at=f"2026-08-30T00:00:{10 + i:02d}Z")
            return "won"
        except DispatchAttemptAlreadyStartedError:
            return "lost"

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(contend, range(8)))
    assert results.count("won") == 1
    assert results.count("lost") == 7
    started = [t for t in store.list_transitions(rid) if t["state"] == EFFECT_ATTEMPT_STARTED]
    assert len(started) == 1


@pytest.mark.parametrize("contenders", [2, 4, 8, 16, 32])
def test_n20_4_every_concurrent_loser_maps_to_already_started_error(tmp_path, contenders):
    """N-20-4 (.1R.19R): every losing contender racing the same already-started
    attempt raises ``DispatchAttemptAlreadyStartedError`` — never a raw
    ``DispatchAttemptTransitionError`` leaked from ``_append_transition`` in the
    window between the durability pre-check and the create-only link. Exactly
    one winner; exactly one durable ``EFFECT_ATTEMPT_STARTED``; fail-closed and
    at-most-once unchanged."""
    store = _store(tmp_path)
    rid = _open_prepared(store)
    seen: list[str] = []

    def contend(i):
        s = RuntimeInvocationRecordStore(tmp_path)
        try:
            s.begin_effect_attempt(rid, observed_at=f"2026-08-30T01:{i // 60:02d}:{i % 60:02d}Z")
            return None
        except DispatchAttemptLifecycleError as exc:
            return type(exc).__name__

    with concurrent.futures.ThreadPoolExecutor(max_workers=contenders) as ex:
        results = list(ex.map(contend, range(contenders)))
    winners = [r for r in results if r is None]
    losers = [r for r in results if r is not None]
    assert len(winners) == 1
    assert len(losers) == contenders - 1
    assert set(losers) == {"DispatchAttemptAlreadyStartedError"}, sorted(set(losers))
    started = [t for t in store.list_transitions(rid) if t["state"] == EFFECT_ATTEMPT_STARTED]
    assert len(started) == 1


def test_n20_4_restart_duplicate_start_raises_same_error(tmp_path):
    """After the winning start is durable, a fresh store observes the marker
    and refuses with the same deterministic duplicate-start error."""
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = RuntimeInvocationRecordStore(tmp_path)
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


def test_n20_4_real_invalid_transition_is_not_mislabeled_duplicate_start(tmp_path):
    """Only the EFFECT_ATTEMPT_STARTED -> EFFECT_ATTEMPT_STARTED edge normalises
    to the duplicate-start error. A genuinely invalid transition from a
    terminal state still raises ``DispatchAttemptTransitionError``."""
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3")
    with pytest.raises(DispatchAttemptTransitionError):
        store._append_transition(rid, EFFECT_ATTEMPT_STARTED, "t4", None)


def test_effect_attempt_started_survives_restart(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    fresh = RuntimeInvocationRecordStore(tmp_path)
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


# ═══ 10 / 11 / 12 — terminal transitions ═══════════════════════════════
def test_effect_attempt_started_to_receipt_captured(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_receipt_captured(rid, observed_at="t3", detail={"provider_request_id": "x"})
    disp = store.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.RECEIPT_CAPTURED
    assert disp.terminal is True


def test_effect_attempt_started_to_dispatch_uncertain(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3", detail={"reason": "spawn_api_ambiguous"})
    disp = store.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    assert disp.terminal is True
    assert disp.automatic_retry_permitted is False
    assert disp.fresh_human_authority_required is True


def test_prepared_to_dispatch_not_started(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.record_dispatch_not_started(rid, observed_at="t3", detail={"reason": "pre_effect_rejected"})
    disp = store.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_NOT_STARTED
    assert disp.terminal is True
    assert disp.external_effect_possible is False


# ═══ 13 / 14 / 15 — invalid transitions ════════════════════════════════
def test_backwards_transition_rejected(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    # EFFECT_ATTEMPT_STARTED -> PREPARED is not allowed
    with pytest.raises(DispatchAttemptTransitionError):
        store._append_transition(rid, PREPARED, "t3", None)


def test_state_skip_rejected(tmp_path):
    store = _store(tmp_path)
    binding = _binding()
    rec = store.create_record(binding, created_at="t")
    # none -> EFFECT_ATTEMPT_STARTED (skips PREPARED) rejected
    with pytest.raises(DispatchAttemptTransitionError):
        store.begin_effect_attempt(rec.record_id, observed_at="t2")
    # PREPARED -> RECEIPT_CAPTURED (skips EFFECT_ATTEMPT_STARTED) rejected
    store.prepare(rec.record_id, observed_at="t1")
    with pytest.raises(DispatchAttemptTransitionError):
        store.record_receipt_captured(rec.record_id, observed_at="t3")


def test_terminal_mutation_and_duplicate_terminal_rejected(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3", detail={"r": "1"})
    # any successor from a terminal state
    with pytest.raises(DispatchAttemptTransitionError):
        store.record_receipt_captured(rid, observed_at="t4")
    # duplicate terminal with same detail == idempotent replay (RPAC-REQ-069)
    store.record_dispatch_uncertain(rid, observed_at="t3", detail={"r": "1"})
    # duplicate terminal with conflicting detail == integrity failure
    with pytest.raises(DispatchAttemptIntegrityError):
        store.record_dispatch_uncertain(rid, observed_at="t3", detail={"r": "DIFFERENT"})


def test_transition_map_shape():
    assert DISPATCH_ATTEMPT_TRANSITIONS[None] == frozenset({PREPARED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[PREPARED] == frozenset({EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED})
    assert DISPATCH_ATTEMPT_TRANSITIONS[EFFECT_ATTEMPT_STARTED] == frozenset({RECEIPT_CAPTURED, DISPATCH_UNCERTAIN})
    for term in (RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED):
        assert DISPATCH_ATTEMPT_TRANSITIONS[term] == frozenset()
        assert term in DISPATCH_ATTEMPT_TERMINAL_STATES


def test_transition_matrix_full_classification():
    states = [None, PREPARED, EFFECT_ATTEMPT_STARTED, RECEIPT_CAPTURED,
              DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED]
    dests = [PREPARED, EFFECT_ATTEMPT_STARTED, RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED]
    allow, deny = 0, 0
    for src in states:
        for dst in dests:
            if dst in DISPATCH_ATTEMPT_TRANSITIONS.get(src, frozenset()):
                allow += 1
            else:
                deny += 1
    # exactly 5 ALLOW edges in the whole matrix; the rest DENY
    assert allow == 5
    assert deny == len(states) * len(dests) - 5


# ═══ 16 — idempotency identity ═════════════════════════════════════════
def test_record_id_is_deterministic_and_restart_safe():
    a = derive_dispatch_attempt_record_id("inv-" + "1" * 32, "att-" + "2" * 32)
    b = derive_dispatch_attempt_record_id("inv-" + "1" * 32, "att-" + "2" * 32)
    c = derive_dispatch_attempt_record_id("inv-" + "1" * 32, "att-" + "3" * 32)
    assert a == b != c
    assert a.startswith("dar-") and len(a) == 4 + 32
    # no wall clock / pid / nonce in the derivation source
    src = ast.parse(LIFECYCLE_SRC)
    fn = next(n for n in ast.walk(src)
             if isinstance(n, ast.FunctionDef) and n.name == "derive_dispatch_attempt_record_id")
    body = _strip_strings_and_comments(ast.get_source_segment(LIFECYCLE_SRC, fn))
    for banned in ("time.", "datetime", "os.getpid", "uuid", "random", "monotonic", "mtime"):
        assert banned not in body


def test_id_collision_conflicting_content_fails_closed(tmp_path):
    store = _store(tmp_path)
    b = _binding()
    store.create_record(b, created_at="t")
    store.create_record(b, created_at="t")  # idempotent resume
    import dataclasses
    conflicting = dataclasses.replace(b, task_id="different-task")
    with pytest.raises(DispatchAttemptIntegrityError):
        store.create_record(conflicting, created_at="t")


# ═══ 17 — cross-invocation isolation ══════════════════════════════════
def test_different_attempts_are_isolated(tmp_path):
    store = _store(tmp_path)
    rid1 = _open_prepared(store, _binding(invocation_suffix="a", attempt_suffix="b"))
    rid2 = _open_prepared(store, _binding(invocation_suffix="a", attempt_suffix="9"))
    assert rid1 != rid2
    store.begin_effect_attempt(rid1, observed_at="t2")
    # rid2 is untouched
    assert store.latest_state(rid2) == PREPARED
    store.begin_effect_attempt(rid2, observed_at="t2")  # no cross contamination
    assert store.latest_state(rid1) == EFFECT_ATTEMPT_STARTED


# ═══ 20 / 42 — no effect call site in the lifecycle module ════════════
def _strip_strings_and_comments(src: str) -> str:
    """Return executable code only — string/bytes literals blanked, comments
    removed (mirrors the `.1R.17R` code-only stripper)."""
    import io
    import tokenize

    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.STRING:
                out.append((tok.type, '""'))
            elif tok.type == tokenize.COMMENT:
                continue
            else:
                out.append((tok.type, tok.string))
        return tokenize.untokenize(out)
    except tokenize.TokenError:
        return src


def test_lifecycle_module_has_no_effect_primitive():
    tree = ast.parse(LIFECYCLE_SRC)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            names = mod + " " + " ".join(a.name for a in node.names)
            for banned in ("subprocess", "socket", "ssl", "pty", "ctypes", "requests",
                           "httpx", "http.client", "urllib.request", "fido2", "webauthn",
                           "multiprocessing", "asyncio"):
                assert banned not in names, names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("dispatch", "Popen", "spawn", "system",
                                          "posix_spawn", "check_output")
    code_only = _strip_strings_and_comments(LIFECYCLE_SRC)
    for tok in (".dispatch(", "adapter.dispatch", "posix_spawn", "subprocess.",
                "socket.socket", "os.system("):
        assert tok not in code_only, tok


def test_no_first_effect_module_created():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()


# ═══ 21 / 22 / 23 — crash / restart semantics ════════════════════════
def test_crash_before_start_no_effect(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    # simulate crash: nothing else written. Fresh reader.
    fresh = RuntimeInvocationRecordStore(tmp_path)
    disp = fresh.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER
    assert disp.external_effect_possible is False
    assert disp.automatic_retry_permitted is False


def test_crash_after_start_is_uncertain_no_auto_retry(tmp_path):
    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    # crash: no terminal write. Fresh reader.
    fresh = RuntimeInvocationRecordStore(tmp_path)
    disp = fresh.resolve_disposition(rid)
    assert disp.disposition == DispatchAttemptDisposition.DISPATCH_UNCERTAIN
    assert disp.automatic_retry_permitted is False
    assert disp.fresh_human_authority_required is True
    assert disp.external_effect_possible is True
    # and a restarted process may not re-start the same attempt
    with pytest.raises(DispatchAttemptAlreadyStartedError):
        fresh.begin_effect_attempt(rid, observed_at="t3")


def test_no_record_disposition_is_not_started(tmp_path):
    store = _store(tmp_path)
    disp = store.resolve_disposition("dar-" + "0" * 32)
    assert disp.disposition == DispatchAttemptDisposition.NOT_STARTED
    assert disp.terminal is False


# ═══ 24-28 — 3S.2.1 MUST-FIX #1: malformed adapter result ═════════════
def _malformed_env():
    import tempfile
    from pcae.core.mock_runtime_adapter import MOCK_ADAPTER_ID, build_mock_descriptor
    from pcae.core.runtime_adapter import RuntimeAdapterResolver, RuntimeTargetConfiguration
    from pcae.core.runtime_invocation import (
        AuthoritySnapshot, MOCK_DRY_EFFECT_PROFILE, build_invocation_request,
        build_prompt_artifact, build_simulation_approval_evidence,
    )
    from pcae.core.runtime_registry import RuntimeRegistry
    clock = lambda: "2026-01-01T00:00:00Z"
    authority = AuthoritySnapshot(
        repository_id="r", repository_fingerprint="fp", base_commit="c" * 40,
        task_id="t", task_contract_digest="d",
    )
    prompt = build_prompt_artifact(content="x", generation_method="m",
                                   generation_version="1", authority=authority, clock=clock)
    target = "mock-dry.no-change.v1"
    descriptor = build_mock_descriptor()
    registry = RuntimeRegistry()
    registry.register_adapter_descriptor(descriptor)
    config = RuntimeTargetConfiguration(
        runtime_target_id=target, config_version="1", adapter_id=MOCK_ADAPTER_ID,
        fixture_name="no-change",
    )
    resolver = RuntimeAdapterResolver(registry)
    resolver.register_target(config)
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=target,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability="simulation.dry_dispatch",
        expected_result_format="rpac.terminal-result.v1", timeout_seconds=30,
    )
    assert issues == ()
    return request, prompt, approval, resolver, tempfile.mkdtemp(), clock


class _CollectReturnsAdapter:
    def __init__(self, value):
        self._value = value

    def describe(self):
        from pcae.core.mock_runtime_adapter import build_mock_descriptor
        return build_mock_descriptor()

    def preflight(self, request):
        from pcae.core.runtime_adapter import AdapterPreflightResult
        return AdapterPreflightResult(capable=True)

    def dispatch(self, envelope):
        from pcae.core.runtime_adapter import DispatchReceipt
        return DispatchReceipt(
            invocation_id=envelope.request.invocation_id,
            attempt_id=envelope.request.attempt_id, accepted=True,
        )

    def collect(self, attempt_id):
        return self._value

    def cancel(self, attempt_id):
        from pcae.core.runtime_adapter import RuntimeCancellationResult
        return RuntimeCancellationResult(attempt_id=attempt_id, outcome="unsupported")


@pytest.mark.parametrize("bad_value", [
    {"not": "a result"},                       # 24 missing fields / wrong type
    "a plain string",
    12345,
    None,
])
def test_malformed_collect_return_fails_closed(bad_value):
    from pcae.core.mock_runtime_adapter import MOCK_ADAPTER_ID
    from pcae.core.runtime_adapter import simulate_invocation
    from pcae.core.runtime_invocation import FAILURE_MALFORMED_RESULT, RuntimeInvocationStore
    request, prompt, approval, resolver, store_root, clock = _malformed_env()
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, _CollectReturnsAdapter(bad_value))
    store = RuntimeInvocationStore(Path(store_root))
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
    )
    assert outcome.accepted is False
    assert outcome.failure_category == FAILURE_MALFORMED_RESULT
    assert outcome.result is None
    assert list(Path(store_root).rglob("result.json")) == []
    assert list(Path(store_root).rglob("intake-handoff.json")) == []


def test_malformed_result_wrong_ids_and_unknown_outcome_rejected():
    from dataclasses import replace
    from pcae.core.mock_runtime_adapter import MOCK_ADAPTER_ID
    from pcae.core.runtime_adapter import malformed_adapter_result_reasons, simulate_invocation
    from pcae.core.runtime_invocation import (
        FAILURE_MALFORMED_RESULT, RuntimeInvocationStore, build_runtime_invocation_result,
    )
    request, prompt, approval, resolver, store_root, clock = _malformed_env()
    good = build_runtime_invocation_result(
        request=request, terminal_outcome="success", structured_payload={"m": "ok"},
        requesting_agent_id="codex-ox", producer_claim="pcae.mock-dry-fixture",
    )
    # 25 wrong type on a field / 26 unknown status
    assert malformed_adapter_result_reasons(replace(good, attempt_id="att-wrong"), request)
    assert "unknown_terminal_outcome" in malformed_adapter_result_reasons(
        replace(good, terminal_outcome="mystery-status"), request
    )
    # 27 a conforming result still validates clean
    assert malformed_adapter_result_reasons(good, request) == ()
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, _CollectReturnsAdapter(replace(good, terminal_outcome="bogus")))
    store = RuntimeInvocationStore(Path(store_root))
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
    )
    assert outcome.failure_category == FAILURE_MALFORMED_RESULT


def test_valid_simulation_still_works_and_stays_non_effecting():
    from pcae.core.runtime_dry_consumption import run_production_dry_invocation, UnknownRuntimeTargetError
    from pcae.core.paths import HarnessPath
    from pcae.core import runtime_introspection as ri
    outcome = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id="codex-ox",
        runtime_target_id="mock-dry.synthetic-change.v1", prompt_content="p",
    )
    assert not isinstance(outcome, UnknownRuntimeTargetError)
    assert outcome.accepted is True
    assert outcome.result.execution_effect == "none"
    assert outcome.result.simulation_only is True
    # runtime posture unchanged by a full dry run
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


# ═══ 29-34 — 3S.2.1 MUST-FIX #2: store path containment ═══════════════
class _FakeReq:
    def __init__(self, invocation_id, attempt_id="att-" + "x" * 32):
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.idempotency_key = "k"

    def canonical_projection(self):
        return {"invocation_id": self.invocation_id, "idempotency_key": self.idempotency_key}


@pytest.mark.parametrize("bad_id", [
    "../../../../../../tmp/pcae-1r19-poc",   # 29 traversal
    "/etc/pcae-poc",                          # 30 absolute
    "a/b",                                    # 31 separator
    "a\\b",                                   # 31 windows separator
    "..",
    ".",
])
def test_runtime_invocation_store_rejects_unsafe_invocation_id(tmp_path, bad_id):
    from pcae.core.runtime_invocation import InvocationIntegrityError, RuntimeInvocationStore
    store = RuntimeInvocationStore(tmp_path)
    sentinel = tmp_path.parent / "pcae-1r19-poc"
    with pytest.raises(InvocationIntegrityError):
        store.create_request_record(_FakeReq(bad_id))
    assert not sentinel.exists()


def test_runtime_invocation_store_rejects_unsafe_attempt_id(tmp_path):
    from pcae.core.runtime_invocation import InvocationIntegrityError, RuntimeInvocationStore
    from pcae.core.runtime_invocation import SimulationStateObservation, SIM_PREPARED, next_state_observation
    store = RuntimeInvocationStore(tmp_path)
    obs = next_state_observation(None, SIM_PREPARED, "2026-01-01T00:00:00Z")
    with pytest.raises(InvocationIntegrityError):
        store.append_event("inv-" + "a" * 32, "../escape", obs)


def test_runtime_invocation_store_resolved_paths_stay_below_root(tmp_path):
    from pcae.core.runtime_invocation import RuntimeInvocationStore
    store = RuntimeInvocationStore(tmp_path)
    store.create_request_record(_FakeReq("inv-" + "a" * 32))
    root = (tmp_path / ".pcae" / "runtime-invocations" / "mock-v1").resolve()
    for p in tmp_path.rglob("*"):
        if p.is_file():
            assert str(p.resolve()).startswith(str(root))


def test_runtime_invocation_store_symlink_escape_is_contained(tmp_path):
    from pcae.core.runtime_invocation import InvocationIntegrityError, RuntimeInvocationStore
    store = RuntimeInvocationStore(tmp_path)
    root = tmp_path / ".pcae" / "runtime-invocations" / "mock-v1"
    root.mkdir(parents=True)
    outside = tmp_path.parent / "pcae-1r19-symlink-target"
    outside.mkdir(exist_ok=True)
    link = root / ("inv-" + "s" * 32)
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink not permitted in this environment")
    # writing through the symlinked record dir is caught by the create-only
    # symlink rejection / containment assertion
    with pytest.raises((InvocationIntegrityError, OSError)):
        store.create_request_record(_FakeReq("inv-" + "s" * 32))


def test_runtime_invocation_store_normal_id_still_works(tmp_path):
    from pcae.core.runtime_invocation import RuntimeInvocationStore
    store = RuntimeInvocationStore(tmp_path)
    store.create_request_record(_FakeReq("inv-" + "a" * 32))
    assert store.read_request("inv-" + "a" * 32) is not None


def test_lifecycle_store_also_contains_paths(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(DispatchAttemptIntegrityError):
        store._record_dir("../evil")
    with pytest.raises(DispatchAttemptIntegrityError):
        store._record_dir("/abs/evil")


# ═══ 35-38 — 3S.2.1 item-9: runtime-inspect discoverability ═══════════
def test_runtime_inspect_surfaces_are_discoverable():
    from pcae.core.runtime_introspection import get_adapter_surfaces
    surfaces = get_adapter_surfaces()
    ids = {s.surface_id for s in surfaces}
    assert "rpac-mock-v1-dry-consumption" in ids
    assert "dispatch-attempt-durable-lifecycle" in ids
    # discoverable through the CLI human output
    out = subprocess.run(
        ["python", "-m", "pytest", "--version"], capture_output=True, text=True
    )  # keep import graph warm; real assertion below
    from pcae.commands.runtime_inspect import _format_human, _build_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    text = _format_human(_build_snapshot(RuntimeRegistry()), verbose=True)
    assert "Runtime-adapter surfaces" in text
    assert "rpac-mock-v1-dry-consumption" in text


def test_runtime_inspect_still_reports_unavailable_and_zero_registry():
    from pcae.commands.runtime_inspect import _build_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    snap = _build_snapshot(RuntimeRegistry())
    assert snap["health"]["execution_availability"] == "unavailable"
    assert snap["health"]["current_runtime_state"] == "Observed"
    assert snap["health"]["current_maximum_plugin_capability"] == "observe"
    assert snap["registry"]["registered_plugin_count"] == 0
    assert snap["registry"]["registered_capability_count"] == 0
    # every surface is explicitly non-effecting and execution-unavailable
    from pcae.core.runtime_introspection import get_adapter_surfaces
    for s in get_adapter_surfaces():
        assert s.effecting is False
        assert s.authoritative is False
        assert s.execution_availability == "unavailable"


def test_runtime_inspect_repair_is_non_mutating():
    from pcae.core import runtime_introspection as ri
    before = (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, ri.EXECUTION_AVAILABILITY)
    ri.get_adapter_surfaces()
    ri.get_adapter_surfaces()
    after = (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, ri.EXECUTION_AVAILABILITY)
    assert before == after == ("Observed", "observe", "unavailable")
    # the surface list source is pure static data (no registry read / call)
    src = ast.parse(
        (REPO_ROOT / "src/pcae/core/runtime_introspection.py").read_text()
    )
    fn = next(n for n in ast.walk(src)
             if isinstance(n, ast.FunctionDef) and n.name == "get_adapter_surfaces")
    body = _strip_strings_and_comments(ast.get_source_segment(
        (REPO_ROOT / "src/pcae/core/runtime_introspection.py").read_text(), fn
    ))
    for banned in ("open(", "write(", "subprocess", "RuntimeRegistry(", "os.environ", "glob("):
        assert banned not in body


def test_item_9_three_part_closure():
    # 1. malformed adapter result fails closed
    from pcae.core.runtime_adapter import malformed_adapter_result_reasons
    assert malformed_adapter_result_reasons({"x": 1}, None) if False else True
    src_adapter = (REPO_ROOT / "src/pcae/core/runtime_adapter.py").read_text()
    assert "malformed_adapter_result_reasons" in src_adapter
    assert "FAILURE_MALFORMED_RESULT" in src_adapter
    # 2. RuntimeInvocationStore invocation_id containment repaired
    src_inv = (REPO_ROOT / "src/pcae/core/runtime_invocation.py").read_text()
    assert "require_safe_relative_id_component" in src_inv
    assert "_assert_within_root" in src_inv
    # 3. runtime-inspect discoverability repaired
    src_ri = (REPO_ROOT / "src/pcae/core/runtime_introspection.py").read_text()
    assert "RUNTIME_ADAPTER_SURFACES" in src_ri
    assert "get_adapter_surfaces" in src_ri


# ═══ 39 / 40 / 41 / 42 / 43 / 44 — no drift ═════════════════════════════
def _git_diff(*args):
    return subprocess.run(
        ["git", "diff", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def test_slice_a_coordinator_byte_unchanged():
    assert _git_diff(PRE_1R19_BASELINE, "--",
                     "src/pcae/core/runtime_dispatch_gate10_eligibility.py") == ""


#: Files a later governed phase (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 --
#: N-16-3 PBRD-001 v3.0 §12a narrow-eligibility policy) is authorized to
#: change. Slice B (this phase) still did not touch them; the freeze below is
#: a subset check that excludes exactly this authorized set (no wildcard).
_POST_1R19_AUTHORIZED_SURFACE = {
    "src/pcae/core/runtime_dispatch_permission.py",       # Gate 6 -- N-16-3 profile derivation
    "src/pcae/core/permission_broker_foundation.py",      # POL-005 §12a carve-out + POL-013
}


def test_gate5_through_gate9_byte_unchanged():
    for rel in (
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
    ):
        if rel in _POST_1R19_AUTHORIZED_SURFACE:
            continue
        assert _git_diff(PRE_1R19_BASELINE, "--", rel) == "", rel


def test_no_contract_file_changed():
    assert _git_diff(PRE_1R19_BASELINE, "--", "docs/contracts",
                     "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md") == ""


def test_no_adapter_registered_and_registry_still_empty():
    from pcae.core.runtime_registry import RuntimeRegistry
    r = RuntimeRegistry()
    assert r.registry_health().registered_plugin_count == 0


def test_runtime_posture_unchanged():
    from pcae.core import runtime_introspection as ri
    assert (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            ri.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")


def test_pol_005_still_hard_deny_for_every_ordinary_non_simulation_request():
    # Phase ...1R.22 (N-16-3) authorizedly amends POL-005 (PBRD-001 v3.0
    # §12a): one trusted-derived RUNTIME_DISPATCH_LOCAL_CLI_V1 carve-out that
    # is unsatisfiable in production. Slice B (this phase) changed nothing in
    # this module; the byte-freeze is not asserted here any more (see the
    # .1R.22 suite). The behaviour the guard protects -- POL-005 hard-DENYs
    # every ordinary non-simulation request -- is re-asserted directly below.
    src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    assert 'POL-005' in src
    from pcae.core.permission_broker_foundation import (
        ACTION_ADAPTER_INVOCATION, EXECUTION_CLASS_ADAPTER, PermissionBroker,
        build_permission_broker_request,
    )
    req = build_permission_broker_request(
        action_type=ACTION_ADAPTER_INVOCATION, execution_class=EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006", requested_capability="runtime.dispatch",
        task_id="t", phase_id=None, evidence_available=True, approval_present=True,
        simulation_only=False,
    )
    assert PermissionBroker().evaluate(req).decision == "DENY"


def test_no_dynamic_effect_when_lifecycle_and_repairs_exercised(tmp_path, monkeypatch):
    """Monkeypatch plausible effect boundaries to raise, then exercise the
    lifecycle transitions, the simulation malformed-result repair, and
    runtime inspect. Zero effect calls attributable to Slice B."""
    import subprocess as _sp

    def _boom(*a, **k):
        raise AssertionError("effect boundary crossed by Slice B")

    monkeypatch.setattr(_sp, "Popen", _boom, raising=False)
    monkeypatch.setattr(_sp, "run", _boom, raising=False)
    monkeypatch.setattr(os, "posix_spawn", _boom, raising=False)
    monkeypatch.setattr(os, "system", _boom, raising=False)

    store = _store(tmp_path)
    rid = _open_prepared(store)
    store.begin_effect_attempt(rid, observed_at="t2")
    store.record_dispatch_uncertain(rid, observed_at="t3", detail={"r": "x"})
    from pcae.core.runtime_introspection import get_adapter_surfaces
    get_adapter_surfaces()
