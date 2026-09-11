"""N16-5-F-5-TB-REPLAY-REPAIR — durable cross-process one-shot replay state.

These tests prove the repair against the *actual* defect N16-5-F-5-TB-HELPER-IV
confirmed: spent ``(request_id, nonce)`` state that lived only in one Python
process. Proving that requires genuine OS process separation, so the scenarios
below run real ``subprocess`` helpers (one process per simulated helper exec)
and, where the scenario is a crash, really ``SIGKILL`` them. Two objects inside
one interpreter would not be evidence of anything here.

Everything is disposable: each test gets its own ``tmp_path`` protected root.
No real ``<HPAC_PROTECTED_ROOT>``, no ceremony, no FIDO2/YubiKey, no sudo, no
production principal, no live protected-host mutation.
"""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_OPERATIONS,
    Decision,
    EvidenceStager,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    ProtectedStoreFoundation,
    ReplayLedger,
    ReplayOutcome,
    build_signed_request,
    dispatch,
)
from pcae.core.hpac_pawa_helper_replay_state import (
    DurableReplayState,
    DurableReplayStore,
    ReplayStateCorruption,
    compute_replay_key,
    open_durable_replay_ledger,
    record_exports_no_authority,
)

FAR_FUTURE = "2999-01-01T00:00:00.000000Z"
INSTALLATION_ID = "inst-replay-1"
GENERATION = 7


# ---------------------------------------------------------------------------
# Real-subprocess helper harness.
#
# ``_WORKER`` is written to the test's tmp_path and executed by a fresh
# interpreter, so every invocation is a genuinely separate OS process with its
# own address space — the only way to falsify or confirm a process-local
# ledger claim.
# ---------------------------------------------------------------------------

_WORKER = r'''
import json, os, signal, sys, time

from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_OPERATIONS, EvidenceStager, HelperContext, HelperOperation,
    ProtectedStoreFoundation, build_signed_request, dispatch,
)
from pcae.core.hpac_pawa_helper_replay_state import (
    DurableReplayState, DurableReplayStore, open_durable_replay_ledger,
)

spec = json.loads(sys.argv[1])


def make_request():
    return build_signed_request(
        operation=HelperOperation(spec["operation"]),
        session_id=spec["session_id"],
        operation_params=spec.get("operation_params", {}),
        request_id=spec["request_id"],
        nonce=spec["nonce"],
        expiry=spec["expiry"],
        installation_id=spec["installation_id"],
        generation=spec["generation"],
        principal_id=spec.get("principal_id"),
    )


def make_store():
    return DurableReplayStore(
        protected_root=spec["protected_root"],
        installation_id=spec["installation_id"],
        generation=spec["generation"],
    )


def emit(payload):
    sys.stdout.write("RESULT " + json.dumps(payload) + "\n")
    sys.stdout.flush()


def wait_for_go():
    go = spec.get("go_file")
    if not go:
        return
    while not os.path.exists(go):
        time.sleep(0.002)


action = spec["action"]
request = make_request()

if action == "dispatch":
    wait_for_go()
    ledger = open_durable_replay_ledger(
        protected_root=spec["protected_root"],
        installation_id=spec["installation_id"],
        generation=spec["generation"],
    )
    ctx = HelperContext(
        replay_ledger=ledger,
        evidence_stager=EvidenceStager(fail_finalization=spec.get("fail_finalization", False)),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    try:
        response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
        if response.decision == "PERFORMED" and spec.get("effect_dir"):
            # Record the real protected-store effect in a shared place, so the
            # test can count how many mutations actually happened across all
            # processes rather than trusting the decisions alone.
            assert ctx.store.records or ctx.store.presentation_evidence or ctx.store.ceremonies_started
            os.makedirs(spec["effect_dir"], exist_ok=True)
            with open(os.path.join(spec["effect_dir"], "effect-%d" % os.getpid()), "w") as fh:
                fh.write(response.evidence_ref or "")
        emit({"decision": response.decision, "terminal_code": response.terminal_code,
              "state_reached": response.state_reached})
    except Exception as exc:
        emit({"decision": "RAISED", "terminal_code": getattr(exc, "code", None),
              "error": type(exc).__name__})

elif action == "reserve_only":
    wait_for_go()
    store = make_store()
    emit({"outcome": store.check_and_reserve(request).value})

elif action == "reserve_then_hard_kill":
    # Reserve, durably cross the spend boundary, then die without any
    # cleanup at all (SIGKILL to self: no atexit, no finally, no flush).
    store = make_store()
    outcome = store.check_and_reserve(request)
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    sys.stdout.write("RESULT " + json.dumps({"outcome": outcome.value}) + "\n")
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGKILL)

elif action == "reserve_then_kill_before_boundary":
    store = make_store()
    outcome = store.check_and_reserve(request)
    sys.stdout.write("RESULT " + json.dumps({"outcome": outcome.value}) + "\n")
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGKILL)

elif action == "read_record":
    store = make_store()
    record = store.read_record(request)
    emit({"record": None if record is None else record.to_mapping()})

else:
    raise SystemExit("unknown action " + action)
'''


def _worker_path(tmp_path: Path) -> Path:
    path = tmp_path / "replay_worker.py"
    if not path.exists():
        path.write_text(_WORKER)
    return path


def _spec(protected_root: Path, **overrides) -> dict:
    spec = {
        "protected_root": str(protected_root),
        "installation_id": INSTALLATION_ID,
        "generation": GENERATION,
        "operation": HelperOperation.ADMIN_MUTATION.value,
        "session_id": "sess-1",
        "operation_params": {"mutation": "enroll_principal", "transaction_id": "txn-1"},
        "request_id": "req-1",
        "nonce": "a" * 64,
        "expiry": FAR_FUTURE,
        "action": "dispatch",
    }
    spec.update(overrides)
    return spec


def _env() -> dict:
    env = os.environ.copy()
    repo_src = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = repo_src + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_worker(tmp_path: Path, spec: dict, *, timeout: float = 60.0):
    """Run one simulated helper process. Returns (parsed RESULT dict|None, completed)."""
    completed = subprocess.run(
        [sys.executable, str(_worker_path(tmp_path)), json.dumps(spec)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
    )
    payload = None
    for line in completed.stdout.splitlines():
        if line.startswith("RESULT "):
            payload = json.loads(line[len("RESULT "):])
    return payload, completed


def _start_worker(tmp_path: Path, spec: dict):
    return subprocess.Popen(
        [sys.executable, str(_worker_path(tmp_path)), json.dumps(spec)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_env(),
    )


@pytest.fixture()
def protected_root(tmp_path):
    """A disposable stand-in protected root: 0700, owned by this uid."""
    root = tmp_path / "protected-root"
    root.mkdir(mode=0o700)
    return root


def _local_request(**overrides):
    defaults = dict(
        operation=HelperOperation.ADMIN_MUTATION,
        session_id="sess-1",
        operation_params={"mutation": "enroll_principal", "transaction_id": "txn-1"},
        request_id="req-1",
        nonce="a" * 64,
        expiry=FAR_FUTURE,
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    defaults.update(overrides)
    return build_signed_request(**defaults)


def _store(protected_root: Path, **overrides) -> DurableReplayStore:
    kwargs = dict(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    kwargs.update(overrides)
    return DurableReplayStore(**kwargs)


# ---------------------------------------------------------------------------
# 1. The regression itself: clean restart, real process separation.
# ---------------------------------------------------------------------------


def test_clean_restart_consumed_request_is_not_fresh_in_a_new_process(tmp_path, protected_root):
    """The N16-5-F-5-TB-HELPER-IV defect, directly: helper process A admits and
    consumes a request; a brand-new helper process B must DENY it."""
    spec = _spec(protected_root)

    first, _ = _run_worker(tmp_path, spec)
    assert first == {
        "decision": Decision.PERFORMED.value,
        "terminal_code": None,
        "state_reached": "EVIDENCE_WRITTEN",
    }

    second, _ = _run_worker(tmp_path, spec)
    assert second["decision"] == Decision.REJECTED.value
    assert second["terminal_code"] == "capability_stale"


def test_clean_restart_many_times_never_re_admits(tmp_path, protected_root):
    spec = _spec(protected_root, request_id="req-many", nonce="b" * 64)
    first, _ = _run_worker(tmp_path, spec)
    assert first["decision"] == Decision.PERFORMED.value
    for _ in range(4):
        again, _ = _run_worker(tmp_path, spec)
        assert again["decision"] == Decision.REJECTED.value
        assert again["terminal_code"] == "capability_stale"


def test_in_memory_ledger_still_exhibits_the_defect_so_the_repair_is_attributable(protected_root):
    """Control: the unrepaired in-memory backing is still process-local. This
    keeps the repair honest — it shows the new tests fail for the right reason
    and that the durable backing, not some incidental change, is what fixes
    them."""
    request = _local_request(request_id="req-control", nonce="c" * 64)

    def fresh_context():
        return HelperContext(
            replay_ledger=ReplayLedger(),  # in-memory: a new "process"
            evidence_stager=EvidenceStager(),
            supported_operations=CLOSED_OPERATIONS,
            store=ProtectedStoreFoundation(),
        )

    assert dispatch(request, fresh_context(), CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value
    # A second *fresh* in-memory ledger re-admits it — the defect.
    assert dispatch(request, fresh_context(), CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value
    assert ReplayLedger().is_durable is False


def test_durable_ledger_reports_itself_durable(protected_root):
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    assert ledger.is_durable is True


# ---------------------------------------------------------------------------
# 2. Concurrent duplicate: real race between separate OS processes.
# ---------------------------------------------------------------------------


def test_concurrent_duplicate_race_admits_exactly_one_process(tmp_path, protected_root):
    """§19 'at most one helper process may admit a given (request_id, nonce)'.

    Eight real processes are started, all blocked on a barrier file, then
    released together. Exactly one must see FRESH; every other must be denied.
    """
    go_file = tmp_path / "go"
    spec = _spec(
        protected_root,
        action="reserve_only",
        request_id="req-race",
        nonce="d" * 64,
        go_file=str(go_file),
    )

    procs = [_start_worker(tmp_path, spec) for _ in range(8)]
    time.sleep(0.75)  # let every interpreter finish importing and reach the barrier
    go_file.write_text("go")

    outcomes = []
    for proc in procs:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
        payload = [json.loads(l[len("RESULT "):]) for l in out.splitlines() if l.startswith("RESULT ")]
        assert payload, err
        outcomes.append(payload[-1]["outcome"])

    assert outcomes.count(ReplayOutcome.FRESH.value) == 1, outcomes
    assert set(outcomes) <= {
        ReplayOutcome.FRESH.value,
        ReplayOutcome.DUPLICATE_IN_FLIGHT.value,
    }, outcomes


def test_concurrent_dispatch_race_performs_exactly_one_mutation(tmp_path, protected_root):
    """The same race through the full dispatch path: exactly one PERFORMED."""
    go_file = tmp_path / "go-dispatch"
    effect_dir = tmp_path / "effects"
    spec = _spec(
        protected_root,
        request_id="req-race-dispatch",
        nonce="e" * 64,
        go_file=str(go_file),
        effect_dir=str(effect_dir),
    )

    procs = [_start_worker(tmp_path, spec) for _ in range(6)]
    time.sleep(0.75)
    go_file.write_text("go")

    decisions = []
    for proc in procs:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
        payload = [json.loads(l[len("RESULT "):]) for l in out.splitlines() if l.startswith("RESULT ")]
        assert payload, err
        decisions.append(payload[-1]["decision"])

    assert decisions.count(Decision.PERFORMED.value) == 1, decisions
    assert all(d in (Decision.PERFORMED.value, Decision.REJECTED.value) for d in decisions)
    # The decisive assertion: the *effect* happened exactly once, counted from
    # the processes that actually mutated their store (spec §31).
    assert effect_dir.is_dir()
    assert len(list(effect_dir.iterdir())) == 1, sorted(p.name for p in effect_dir.iterdir())


def test_reservation_is_atomic_not_check_then_create(protected_root):
    """The reservation point is a single O_EXCL create: a second attempt on an
    already-claimed slot cannot succeed, with no interleaving window."""
    store = _store(protected_root)
    request = _local_request(request_id="req-excl", nonce="f" * 64)
    key = compute_replay_key(
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
        request_id=request.request_id,
        nonce=request.nonce,
    )
    assert store.check_and_reserve(request) is ReplayOutcome.FRESH
    # The slot now exists; _write_new must report the collision rather than
    # truncating or re-creating.
    assert store._write_new(key, store.read_record(request).to_mapping()) is False


# ---------------------------------------------------------------------------
# 3. Response loss after commit.
# ---------------------------------------------------------------------------


def test_response_loss_after_commit_does_not_free_the_request(tmp_path, protected_root):
    """§19/REQ-077: 'a lost response does not make the original request unused'.

    Process A completes the mutation; its response is simply discarded (the
    caller never sees it). Process B re-presenting the identical request must
    still be denied.
    """
    spec = _spec(protected_root, request_id="req-lost", nonce="1" * 64)
    first, _ = _run_worker(tmp_path, spec)
    assert first["decision"] == Decision.PERFORMED.value
    del first  # the caller "loses" the response entirely

    resent, _ = _run_worker(tmp_path, spec)
    assert resent["decision"] == Decision.REJECTED.value
    assert resent["terminal_code"] == "capability_stale"

    # And the durable record explains why, for reconciliation (§21/§84).
    record, _ = _run_worker(tmp_path, _spec(protected_root, action="read_record",
                                            request_id="req-lost", nonce="1" * 64))
    assert record["record"]["durable_state"] == DurableReplayState.RESPONSE_EMITTED.value
    assert record["record"]["committed_digest"]


# ---------------------------------------------------------------------------
# 4. Crash / indeterminate.
# ---------------------------------------------------------------------------


def test_crash_after_mutation_attempt_started_leaves_request_spent(tmp_path, protected_root):
    """§21: crash after MUTATION_ATTEMPT_STARTED — the (request_id, nonce) is
    spent, whether or not anything committed. The process is really SIGKILLed,
    so no ``finally``, ``atexit``, or buffered flush can help it."""
    spec = _spec(
        protected_root, action="reserve_then_hard_kill",
        request_id="req-crash", nonce="2" * 64,
    )
    payload, completed = _run_worker(tmp_path, spec)
    assert payload["outcome"] == ReplayOutcome.FRESH.value
    assert completed.returncode == -signal.SIGKILL  # genuinely killed, not a clean exit

    after, _ = _run_worker(tmp_path, _spec(protected_root, request_id="req-crash", nonce="2" * 64))
    assert after["decision"] == Decision.REJECTED.value
    assert after["terminal_code"] == "capability_stale"


def test_crash_before_attempt_boundary_does_not_silently_re_admit(tmp_path, protected_root):
    """§21: crash after OPERATION_ADMITTED but before MUTATION_ATTEMPT_STARTED
    leaves no protected-root mutation. The reservation of a now-dead process
    is *not* treated as free: a resend is denied (fail closed) and the caller's
    forward path is a fresh request id + nonce, exactly as REQ-083 directs."""
    spec = _spec(
        protected_root, action="reserve_then_kill_before_boundary",
        request_id="req-crash-early", nonce="3" * 64,
    )
    payload, completed = _run_worker(tmp_path, spec)
    assert payload["outcome"] == ReplayOutcome.FRESH.value
    assert completed.returncode == -signal.SIGKILL

    resend, _ = _run_worker(
        tmp_path, _spec(protected_root, request_id="req-crash-early", nonce="3" * 64)
    )
    assert resend["decision"] == Decision.REJECTED.value
    assert resend["terminal_code"] == "capability_stale"

    # A genuinely fresh request (new id + nonce) is admitted normally.
    fresh, _ = _run_worker(
        tmp_path, _spec(protected_root, request_id="req-crash-early-2", nonce="4" * 64)
    )
    assert fresh["decision"] == Decision.PERFORMED.value


def test_commit_finalize_gap_records_reconciliation_required(tmp_path, protected_root):
    """§21/§22: committed but evidence not finalized is INDETERMINATE —
    recorded durably as RECONCILIATION_REQUIRED, never reported as success,
    and the request stays spent."""
    spec = _spec(
        protected_root, request_id="req-indet", nonce="5" * 64, fail_finalization=True,
    )
    payload, _ = _run_worker(tmp_path, spec)
    assert payload["decision"] == "RAISED"  # not REJECTED, not PERFORMED
    assert payload["terminal_code"] == "internal_fail_closed"

    record, _ = _run_worker(
        tmp_path, _spec(protected_root, action="read_record", request_id="req-indet", nonce="5" * 64)
    )
    assert record["record"]["durable_state"] == DurableReplayState.RECONCILIATION_REQUIRED.value

    resend, _ = _run_worker(tmp_path, _spec(protected_root, request_id="req-indet", nonce="5" * 64))
    assert resend["decision"] == Decision.REJECTED.value
    assert resend["terminal_code"] == "capability_stale"


def test_evidence_ref_is_bound_into_the_durable_record(protected_root):
    """Evidence-staging integration: the durable replay record carries the
    staged evidence reference, so reconciliation reaches the §22 record from
    the replay state without a second index."""
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    ctx = HelperContext(
        replay_ledger=ledger, evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=ProtectedStoreFoundation(),
    )
    request = _local_request(request_id="req-evref", nonce="6" * 64)
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.PERFORMED.value

    record = _store(protected_root).read_record(request)
    assert record.evidence_ref == response.evidence_ref
    assert record.durable_state == DurableReplayState.RESPONSE_EMITTED.value


# ---------------------------------------------------------------------------
# 5. Conflicting replay.
# ---------------------------------------------------------------------------


def test_conflicting_replay_across_processes_denied(tmp_path, protected_root):
    """§19 conflicting replay: same (request_id, nonce), different binding."""
    first, _ = _run_worker(
        tmp_path, _spec(protected_root, request_id="req-conflict", nonce="7" * 64)
    )
    assert first["decision"] == Decision.PERFORMED.value

    conflicting, _ = _run_worker(
        tmp_path,
        _spec(
            protected_root,
            request_id="req-conflict",
            nonce="7" * 64,
            session_id="a-different-session",
            operation_params={"mutation": "revoke_principal", "transaction_id": "txn-2"},
        ),
    )
    assert conflicting["decision"] == Decision.REJECTED.value
    assert conflicting["terminal_code"] == "target_scope_invalid"


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", "other-session"),
        ("operation", HelperOperation.CERTIFICATION_WRITE.value),
        ("principal_id", "other-principal"),
    ],
)
def test_conflicting_replay_each_bound_field_detected(protected_root, field, value):
    store = _store(protected_root)
    base = dict(request_id=f"req-cf-{field}", nonce="8" * 64, principal_id="principal-a")
    original = _local_request(**base)
    assert store.check_and_reserve(original) is ReplayOutcome.FRESH

    variant = dict(base)
    if field == "operation":
        variant["operation"] = HelperOperation.CERTIFICATION_WRITE
        variant["operation_params"] = {}
    else:
        variant[field] = value
    assert store.check_and_reserve(_local_request(**variant)) is ReplayOutcome.CONFLICTING


def test_conflicting_replay_leaves_the_original_durable_state_unchanged(protected_root):
    """§35: a conflicting replay attempt must not perturb the record it
    collided with."""
    store = _store(protected_root)
    original = _local_request(request_id="req-cf-immutable", nonce="0" * 64)
    assert store.check_and_reserve(original) is ReplayOutcome.FRESH
    store.transition(original, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    before = store.read_record(original).to_mapping()

    for variant in (
        dict(session_id="other"),
        dict(operation_params={"mutation": "revoke_principal", "transaction_id": "t"}),
        dict(principal_id="someone-else"),
    ):
        attempt = _local_request(request_id="req-cf-immutable", nonce="0" * 64, **variant)
        assert store.check_and_reserve(attempt) is ReplayOutcome.CONFLICTING

    assert _store(protected_root).read_record(original).to_mapping() == before


def test_certification_write_conflicting_role_detected(protected_root):
    """§10/§35: the role binding is part of the replay identity, so the same
    (request_id, nonce) replayed under a different certification role is a
    conflicting replay."""
    from pcae.core.hpac_pawa_helper_protocol import CertificationRole

    store = _store(protected_root)
    common = dict(
        operation=HelperOperation.CERTIFICATION_WRITE,
        session_id="sess-role",
        proof_id="proof-1",
        operation_params={},
        request_id="req-role-conflict",
        nonce="0" * 64,
    )
    first = _local_request(role=CertificationRole.HPAC_CHALLENGE_COORDINATOR, **common)
    assert store.check_and_reserve(first) is ReplayOutcome.FRESH
    second = _local_request(role=CertificationRole.HPAC_GATE5_BINDER, **common)
    assert store.check_and_reserve(second) is ReplayOutcome.CONFLICTING


def test_request_digest_change_alone_is_conflicting(protected_root):
    """Even a change the coarse (operation, session, subject) triple would miss
    is caught, because the whole request digest is bound."""
    store = _store(protected_root)
    base = dict(request_id="req-digest", nonce="9" * 64)
    assert store.check_and_reserve(_local_request(**base)) is ReplayOutcome.FRESH
    tweaked = _local_request(
        operation_params={"mutation": "enroll_principal", "transaction_id": "DIFFERENT"}, **base
    )
    assert store.check_and_reserve(tweaked) is ReplayOutcome.CONFLICTING


# ---------------------------------------------------------------------------
# 6. Malformed durable state — every variant fails closed, none is "absent".
# ---------------------------------------------------------------------------


def _slot(protected_root: Path, request) -> Path:
    key = compute_replay_key(
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
        request_id=request.request_id,
        nonce=request.nonce,
    )
    return protected_root / "pawa-helper" / "replay" / f"g{GENERATION}" / f"{key}.json"


def _reserved(protected_root: Path, request):
    store = _store(protected_root)
    assert store.check_and_reserve(request) is ReplayOutcome.FRESH
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    return store


@pytest.mark.parametrize(
    "variant",
    [
        "not_json",
        "not_an_object",
        "unknown_field",
        "missing_field",
        "wrong_schema_version",
        "unknown_state",
        "tampered_digest",
        "tampered_state_only",
        "relocated_record",
        "truncated",
    ],
)
def test_malformed_durable_state_fails_closed(protected_root, variant):
    """A record that cannot be trusted is **corruption**, never 'absent'.

    Treating any of these as absent would re-open the exact replay hole this
    phase closes, so every variant must raise rather than return FRESH.
    """
    request = _local_request(request_id=f"req-mal-{variant}", nonce="0" * 64)
    _reserved(protected_root, request)
    path = _slot(protected_root, request)
    original = json.loads(path.read_text())

    if variant == "not_json":
        path.write_text("{{{ not json at all")
    elif variant == "not_an_object":
        path.write_text(json.dumps([1, 2, 3]))
    elif variant == "unknown_field":
        original["injected_field"] = "x"
        path.write_text(json.dumps(original))
    elif variant == "missing_field":
        original.pop("owner_pid")
        path.write_text(json.dumps(original))
    elif variant == "wrong_schema_version":
        original["record_schema_version"] = "HPAC-PAWA-HELPER-REPLAY-STATE/9.9"
        path.write_text(json.dumps(original))
    elif variant == "unknown_state":
        original["durable_state"] = "TOTALLY_MADE_UP"
        path.write_text(json.dumps(original))
    elif variant == "tampered_digest":
        original["record_digest"] = "0" * 64
        path.write_text(json.dumps(original))
    elif variant == "tampered_state_only":
        # The interesting one: flip the spent state back to a reservation and
        # leave everything else intact. The digest no longer matches.
        original["durable_state"] = DurableReplayState.REQUEST_RECEIVED.value
        path.write_text(json.dumps(original))
    elif variant == "relocated_record":
        # A structurally perfect, correctly digested record — but for a
        # different request, dropped into this slot.
        other = _local_request(request_id="some-other-request", nonce="0" * 64)
        other_store = _store(protected_root)
        assert other_store.check_and_reserve(other) is ReplayOutcome.FRESH
        path.write_text(_slot(protected_root, other).read_text())
    elif variant == "truncated":
        blob = path.read_text()
        path.write_text(blob[: len(blob) // 2])

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root).check_and_reserve(request)


def test_malformed_record_never_reports_fresh_through_dispatch(protected_root):
    """End to end: corruption surfaces as a fail-closed rejection, never as an
    admitted mutation."""
    request = _local_request(request_id="req-mal-dispatch", nonce="0" * 64)
    _reserved(protected_root, request)
    path = _slot(protected_root, request)
    path.write_text("not json")

    ctx = HelperContext(
        replay_ledger=open_durable_replay_ledger(
            protected_root=str(protected_root),
            installation_id=INSTALLATION_ID,
            generation=GENERATION,
        ),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "internal_fail_closed"
    assert not ctx.store.records  # nothing was mutated


def test_symlinked_record_slot_refused(protected_root):
    request = _local_request(request_id="req-symlink", nonce="0" * 64)
    _reserved(protected_root, request)
    path = _slot(protected_root, request)
    elsewhere = protected_root / "decoy.json"
    elsewhere.write_text(path.read_text())
    path.unlink()
    path.symlink_to(elsewhere)

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root).check_and_reserve(request)


def test_symlinked_replay_namespace_refused(tmp_path, protected_root):
    """No symlink traversal anywhere in the namespace chain."""
    (protected_root / "pawa-helper").mkdir(mode=0o700)
    outside = tmp_path / "outside-replay"
    outside.mkdir(mode=0o700)
    (protected_root / "pawa-helper" / "replay").symlink_to(outside)

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root)


def test_group_or_other_writable_namespace_refused(protected_root):
    store = _store(protected_root)
    store.close()
    gen_dir = protected_root / "pawa-helper" / "replay" / f"g{GENERATION}"
    gen_dir.chmod(0o777)
    with pytest.raises(ReplayStateCorruption):
        _store(protected_root)


def test_record_filenames_are_never_caller_chosen(protected_root):
    """Caller-supplied request_id / nonce are hashed, never used as a path."""
    hostile = _local_request(
        request_id="../../../../etc/passwd",
        nonce="/absolute/../../escape" + "z" * 40,
    )
    store = _store(protected_root)
    assert store.check_and_reserve(hostile) is ReplayOutcome.FRESH

    gen_dir = protected_root / "pawa-helper" / "replay" / f"g{GENERATION}"
    names = [p.name for p in gen_dir.iterdir()]
    assert len(names) == 1
    stem = names[0][: -len(".json")]
    assert len(stem) == 64 and all(c in "0123456789abcdef" for c in stem)
    # nothing escaped the namespace
    assert not (protected_root / "pawa-helper" / "replay" / "etc").exists()


def test_unexpected_file_type_in_record_slot_refused(protected_root):
    """§36 'unexpected file type': a directory (or anything non-regular) where
    a record belongs is corruption, not an empty slot."""
    request = _local_request(request_id="req-filetype", nonce="0" * 64)
    _reserved(protected_root, request)
    path = _slot(protected_root, request)
    path.unlink()
    path.mkdir(mode=0o700)

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root).check_and_reserve(request)


def test_world_writable_record_file_refused(protected_root):
    """§36 'wrong owner/mode': a record anyone could have rewritten is not
    trusted state."""
    request = _local_request(request_id="req-filemode", nonce="0" * 64)
    _reserved(protected_root, request)
    _slot(protected_root, request).chmod(0o666)

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root).check_and_reserve(request)


def test_duplicate_conflicting_records_cannot_mask_each_other(protected_root):
    """§36 'duplicate/conflicting records': a second, structurally perfect
    record for a *different* request cannot be planted under this request's
    content-addressed name — the name is derived from the bindings, so the
    forgery is detected as a slot-binding failure."""
    victim = _local_request(request_id="req-dup-victim", nonce="0" * 64)
    _reserved(protected_root, victim)

    decoy = _local_request(request_id="req-dup-decoy", nonce="0" * 64)
    decoy_store = _store(protected_root)
    assert decoy_store.check_and_reserve(decoy) is ReplayOutcome.FRESH

    # Plant the (valid, freshly reserved) decoy record over the victim's slot,
    # trying to downgrade the victim from spent back to reserved.
    _slot(protected_root, victim).write_text(_slot(protected_root, decoy).read_text())

    with pytest.raises(ReplayStateCorruption):
        _store(protected_root).check_and_reserve(victim)
    # the decoy's own slot is untouched and still readable
    assert _store(protected_root).read_record(decoy) is not None


def test_no_temporary_files_are_left_behind(protected_root):
    """§37: the staged-then-published write sequence cleans up after itself, so
    a later ``iter_records`` cannot trip over debris."""
    store = _store(protected_root)
    for i in range(5):
        request = _local_request(request_id=f"req-tmp-{i}", nonce="0" * 64)
        store.check_and_reserve(request)
        store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)

    gen_dir = protected_root / "pawa-helper" / "replay" / f"g{GENERATION}"
    names = sorted(p.name for p in gen_dir.iterdir())
    assert len(names) == 5
    assert all(n.endswith(".json") and not n.startswith(".") for n in names), names
    assert len(store.iter_records()) == 5


def test_record_is_complete_the_moment_its_name_is_visible(protected_root):
    """§37 crash-window: because the record is published by ``link`` after
    being fully written, there is no observable state in which the slot exists
    but holds a partial record."""
    store = _store(protected_root)
    request = _local_request(request_id="req-atomic", nonce="0" * 64)
    key = compute_replay_key(
        installation_id=INSTALLATION_ID, generation=GENERATION,
        request_id=request.request_id, nonce=request.nonce,
    )
    record = store._write_temp(
        {"record_schema_version": "x"}  # any payload; we only inspect visibility
    )
    gen_dir = protected_root / "pawa-helper" / "replay" / f"g{GENERATION}"
    # The staged file is hidden (dot-prefixed) and skipped by iter_records,
    # so it can never be mistaken for a published record.
    assert record.startswith(".")
    assert store.iter_records() == []
    (gen_dir / record).unlink()

    assert store.check_and_reserve(request) is ReplayOutcome.FRESH
    published = gen_dir / f"{key}.json"
    assert json.loads(published.read_text())["replay_key"] == key


def test_stored_files_are_owner_only(protected_root):
    request = _local_request(request_id="req-mode", nonce="0" * 64)
    _store(protected_root).check_and_reserve(request)
    path = _slot(protected_root, request)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    gen_dir = path.parent
    assert stat.S_IMODE(gen_dir.stat().st_mode) == 0o700


# ---------------------------------------------------------------------------
# 7. Restart: dead authority vs persistent history.
# ---------------------------------------------------------------------------


def test_persistent_history_contains_no_authority(protected_root):
    """PAWAH-INV-10: helper restart does not revive spent authority. What
    survives is a *negative* fact, containing no capability/seal/authority
    object and nothing from which one could be reconstructed."""
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    ctx = HelperContext(
        replay_ledger=ledger, evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=ProtectedStoreFoundation(),
    )
    request = _local_request(request_id="req-history", nonce="0" * 64)
    assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value

    store = _store(protected_root)
    records = store.iter_records()
    assert records
    for record in records:
        assert record_exports_no_authority(record)

    # And the raw bytes on disk, independently of the accessor.
    blob = _slot(protected_root, request).read_text().lower()
    for token in ("_seal", "capability", "authority", "bearer_token", "private_key"):
        assert token not in blob, token


def test_restart_yields_only_denial_never_a_replayed_success(tmp_path, protected_root):
    """The durable state can only produce a DENY on restart — it can never
    re-emit the original PERFORMED response or its evidence digest."""
    spec = _spec(protected_root, request_id="req-restart", nonce="0" * 64)
    first, _ = _run_worker(tmp_path, spec)
    assert first["decision"] == Decision.PERFORMED.value

    for _ in range(3):
        again, _ = _run_worker(tmp_path, spec)
        assert again["decision"] == Decision.REJECTED.value
        assert again["state_reached"] == "OPERATION_ADMITTED"  # never reached a mutation
        assert again["terminal_code"] == "capability_stale"


def test_durable_store_grants_no_new_generic_privilege(protected_root):
    """The store's whole public surface is replay bookkeeping: it exposes no
    read, write, enumerate, or path-taking operation over anything else in the
    protected root."""
    store = _store(protected_root)
    public = {name for name in dir(store) if not name.startswith("_")}
    assert public == {
        "check_and_reserve",
        "transition",
        "release_reservation",
        "read_record",
        "iter_records",
        "prune_expired",
        "close",
        "protected_root",
        "installation_id",
        "generation",
    }


# ---------------------------------------------------------------------------
# 8. Ordinary caller cannot reset replay state.
# ---------------------------------------------------------------------------


def test_no_closed_operation_can_reset_replay_state(protected_root):
    """None of the five closed operations reaches a reset/prune/delete path,
    with any operation_params shape."""
    request = _local_request(request_id="req-noreset", nonce="0" * 64)
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    ctx = HelperContext(
        replay_ledger=ledger, evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=ProtectedStoreFoundation(),
    )
    assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value

    hostile_params = [
        {"mutation": "enroll_principal", "transaction_id": "t", "replay_key": "x"},
        {"mutation": "enroll_principal", "transaction_id": "t", "reset_replay": True},
        {"mutation": "enroll_principal", "transaction_id": "t", "prune": True},
        {"mutation": "enroll_principal", "transaction_id": "t", "durable_state": "REQUEST_RECEIVED"},
    ]
    for params in hostile_params:
        attempt = _local_request(
            request_id="req-noreset", nonce="0" * 64, operation_params=params
        )
        response = dispatch(attempt, ctx, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.REJECTED.value
        # and the original record is untouched and still spent
        assert _store(protected_root).read_record(request).is_spent

    assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.REJECTED.value


def test_release_reservation_cannot_clear_a_spent_record(protected_root):
    store = _store(protected_root)
    request = _local_request(request_id="req-release-spent", nonce="0" * 64)
    assert store.check_and_reserve(request) is ReplayOutcome.FRESH
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    assert store.release_reservation(request) is False
    assert store.read_record(request).is_spent
    assert store.check_and_reserve(request) is ReplayOutcome.CONSUMED


def test_release_reservation_cannot_clear_another_processes_reservation(tmp_path, protected_root):
    """A reservation held by a (now dead) other process is not clearable by
    this one, so nothing can be freed out from under an in-flight helper."""
    spec = _spec(
        protected_root, action="reserve_then_kill_before_boundary",
        request_id="req-foreign", nonce="0" * 64,
    )
    payload, _ = _run_worker(tmp_path, spec)
    assert payload["outcome"] == ReplayOutcome.FRESH.value

    store = _store(protected_root)
    request = _local_request(request_id="req-foreign", nonce="0" * 64)
    assert store.release_reservation(request) is False
    assert store.check_and_reserve(request) is ReplayOutcome.DUPLICATE_IN_FLIGHT


def test_illegal_durable_transition_refused(protected_root):
    """Durable history is forward-only: it cannot be rewound."""
    store = _store(protected_root)
    request = _local_request(request_id="req-rewind", nonce="0" * 64)
    store.check_and_reserve(request)
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    with pytest.raises(ReplayStateCorruption):
        store.transition(request, DurableReplayState.REQUEST_RECEIVED)
    with pytest.raises(ReplayStateCorruption):
        store.transition(request, DurableReplayState.EVIDENCE_WRITTEN)  # skips COMMITTED


def test_transition_on_unreserved_request_refused(protected_root):
    store = _store(protected_root)
    request = _local_request(request_id="req-never", nonce="0" * 64)
    with pytest.raises(ReplayStateCorruption):
        store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)


# ---------------------------------------------------------------------------
# 9. Read vs mutation semantics, per operation.
# ---------------------------------------------------------------------------


def test_certification_read_is_idempotent_and_never_replay_tracked(protected_root):
    """REQ-078: repeated reads are not 'consumed' and leave no replay record."""
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    store = ProtectedStoreFoundation()
    store.put_record("principal_record", "p-1", {"principal_id": "p-1"})
    ctx = HelperContext(
        replay_ledger=ledger, evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=store,
    )
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="sess-read",
        operation_params={"record_type": "principal_record", "record_key": "p-1"},
        request_id="req-read", nonce="0" * 64, expiry=FAR_FUTURE,
        installation_id=INSTALLATION_ID, generation=GENERATION,
    )
    for _ in range(3):
        assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value

    assert _store(protected_root).iter_records() == []


@pytest.mark.parametrize(
    "operation",
    [
        HelperOperation.ADMIN_MUTATION,
        HelperOperation.CERTIFICATION_WRITE,
        HelperOperation.PRESENTATION_EVIDENCE_WRITE,
        HelperOperation.CEREMONY_ENTRY,
    ],
)
def test_every_one_shot_operation_is_durably_spent(protected_root, operation):
    """All four one-shot operations (the three mutating ones plus the
    non-mutating-but-single-use ceremony_entry) end durably spent, so none of
    them can be replayed after a restart."""
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    store = ProtectedStoreFoundation()
    store.ceremonies_started["sess-pev"] = "deadbeef"
    ctx = HelperContext(
        replay_ledger=ledger, evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=store,
    )
    kwargs = dict(
        request_id=f"req-{operation.value}", nonce="0" * 64, expiry=FAR_FUTURE,
        installation_id=INSTALLATION_ID, generation=GENERATION,
    )
    if operation is HelperOperation.ADMIN_MUTATION:
        request = build_signed_request(
            operation=operation, session_id="sess-am",
            operation_params={"mutation": "enroll_principal", "transaction_id": "t"}, **kwargs
        )
    elif operation is HelperOperation.CERTIFICATION_WRITE:
        from pcae.core.hpac_pawa_helper_protocol import CertificationRole

        request = build_signed_request(
            operation=operation, role=CertificationRole.HPAC_CHALLENGE_COORDINATOR,
            session_id="sess-cw", proof_id="proof-1", operation_params={}, **kwargs
        )
    elif operation is HelperOperation.PRESENTATION_EVIDENCE_WRITE:
        request = build_signed_request(
            operation=operation, session_id="sess-pev",
            operation_params={"ceremony_approve_ref": "approve-1"}, **kwargs
        )
    else:
        request = build_signed_request(
            operation=operation, session_id="sess-ce",
            operation_params={"ceremony_request_digest": "abc"}, **kwargs
        )

    assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.PERFORMED.value
    record = _store(protected_root).read_record(request)
    assert record is not None and record.is_spent, record
    assert dispatch(request, ctx, CLOSED_DISPATCH_TABLE).decision == Decision.REJECTED.value


@pytest.mark.parametrize(
    "role_name",
    [
        "hpac_challenge_coordinator",
        "hpac_assertion_recorder",
        "human_authentication_proof_verifier",
        "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    ],
)
def test_certification_write_each_role_not_fresh_after_restart(protected_root, role_name):
    """§21: for each of the exact five roles, a one-shot certification write
    cannot become fresh after the helper process is gone. Role closure itself
    is unchanged — these are exactly the contract's five, no more."""
    from pcae.core.hpac_pawa_helper_protocol import (
        CLOSED_CERTIFICATION_ROLES,
        CertificationRole,
    )

    assert role_name in CLOSED_CERTIFICATION_ROLES
    role = CertificationRole(role_name)
    subject_field = (
        "credential_id" if role_name == "hpac_rhamp_counter_state_verifier" else "proof_id"
    )
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_WRITE,
        role=role,
        session_id=f"sess-{role_name}",
        operation_params={},
        request_id=f"req-{role_name}",
        nonce="0" * 64,
        expiry=FAR_FUTURE,
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
        **{subject_field: f"subject-{role_name}"},
    )

    def one_helper_process():
        """A fresh ledger + fresh in-memory store == a new helper exec."""
        return HelperContext(
            replay_ledger=open_durable_replay_ledger(
                protected_root=str(protected_root),
                installation_id=INSTALLATION_ID,
                generation=GENERATION,
            ),
            evidence_stager=EvidenceStager(),
            supported_operations=CLOSED_OPERATIONS,
            store=ProtectedStoreFoundation(),
        )

    assert dispatch(request, one_helper_process(), CLOSED_DISPATCH_TABLE).decision == (
        Decision.PERFORMED.value
    )
    second = one_helper_process()
    response = dispatch(request, second, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "capability_stale"
    assert not second.store.records  # no second certification write


def test_pre_boundary_rejection_releases_the_reservation(protected_root):
    """A request rejected before MUTATION_ATTEMPT_STARTED leaves no durable
    effect (REQ-083), so a corrected request with the same id is admissible —
    the reservation is not a booby trap."""
    ledger = open_durable_replay_ledger(
        protected_root=str(protected_root),
        installation_id=INSTALLATION_ID,
        generation=GENERATION,
    )
    ctx = HelperContext(
        replay_ledger=ledger,
        evidence_stager=EvidenceStager(fail_staging=True),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    request = _local_request(request_id="req-prebound", nonce="0" * 64)
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "internal_fail_closed"
    assert _store(protected_root).read_record(request) is None


# ---------------------------------------------------------------------------
# 10. Expiry, retention, generation / rotation.
# ---------------------------------------------------------------------------


def test_expired_request_denied_before_the_store_is_touched(protected_root):
    store = _store(protected_root)
    request = _local_request(
        request_id="req-expired", nonce="0" * 64, expiry="2000-01-01T00:00:00.000000Z"
    )
    assert store.check_and_reserve(request) is ReplayOutcome.EXPIRED
    assert store.iter_records() == []


def test_unparseable_expiry_is_treated_as_expired(protected_root):
    store = _store(protected_root)
    request = _local_request(request_id="req-badexp", nonce="0" * 64, expiry="whenever")
    assert store.check_and_reserve(request) is ReplayOutcome.EXPIRED


def test_retention_keeps_records_until_well_past_expiry(protected_root):
    store = _store(protected_root)
    soon = datetime.now(timezone.utc) + timedelta(seconds=30)
    request = _local_request(
        request_id="req-retain", nonce="0" * 64,
        expiry=soon.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    )
    store.check_and_reserve(request)
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)

    pruned, retained = store.prune_expired(
        retention=timedelta(days=30), now=soon + timedelta(days=1)
    )
    assert (pruned, retained) == (0, 1)
    assert store.read_record(request).is_spent

    pruned, retained = store.prune_expired(
        retention=timedelta(days=30), now=soon + timedelta(days=31)
    )
    assert (pruned, retained) == (1, 0)
    # Safe: at any time at which pruning was legitimate, the request is past
    # expiry, so it is denied as EXPIRED whether or not a record survives.
    assert (
        store.check_and_reserve(request, now=soon + timedelta(days=31))
        is ReplayOutcome.EXPIRED
    )


def test_reconciliation_required_records_are_never_pruned(protected_root):
    store = _store(protected_root)
    soon = datetime.now(timezone.utc) + timedelta(seconds=1)
    request = _local_request(
        request_id="req-never-prune", nonce="0" * 64,
        expiry=soon.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    )
    store.check_and_reserve(request)
    store.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)
    store.transition(request, DurableReplayState.RECONCILIATION_REQUIRED)

    pruned, retained = store.prune_expired(
        retention=timedelta(days=1), now=soon + timedelta(days=3650)
    )
    assert (pruned, retained) == (0, 1)


def test_generation_rotation_does_not_resurrect_a_spent_request(protected_root):
    """§26: a rotation G -> G+1 must not make a request spent under G fresh.

    The failure mode this guards is precise: replay state is namespaced per
    generation, so a G-bound request presented to a G+1 helper would find an
    empty namespace. That must fail closed as a conflicting replay, never as
    FRESH — the caller's forward path is a *new* request bound to G+1.
    """
    request = _local_request(request_id="req-gen", nonce="0" * 64)
    old = _store(protected_root)
    assert old.check_and_reserve(request) is ReplayOutcome.FRESH
    old.transition(request, DurableReplayState.MUTATION_ATTEMPT_STARTED)

    rotated = _store(protected_root, generation=GENERATION + 1)
    assert rotated.check_and_reserve(request) is ReplayOutcome.CONFLICTING
    assert rotated.iter_records() == []

    # The old generation's spent history survives the rotation intact.
    assert _store(protected_root).check_and_reserve(request) is ReplayOutcome.CONSUMED
    assert len(_store(protected_root).iter_records()) == 1


def test_installation_mismatch_fails_closed(protected_root):
    request = _local_request(request_id="req-inst", nonce="0" * 64)
    other = _store(protected_root, installation_id="a-different-installation")
    assert other.check_and_reserve(request) is ReplayOutcome.CONFLICTING
    assert other.iter_records() == []


def test_replay_key_is_bound_to_installation_and_generation():
    base = dict(installation_id="i", generation=1, request_id="r", nonce="n")
    key = compute_replay_key(**base)
    assert key != compute_replay_key(**{**base, "installation_id": "i2"})
    assert key != compute_replay_key(**{**base, "generation": 2})
    assert key != compute_replay_key(**{**base, "request_id": "r2"})
    assert key != compute_replay_key(**{**base, "nonce": "n2"})
    assert len(key) == 64


def test_replay_key_has_no_concatenation_collisions():
    """Length-prefixed parts: ('ab','c') must not collide with ('a','bc')."""
    a = compute_replay_key(installation_id="ab", generation=1, request_id="c", nonce="n")
    b = compute_replay_key(installation_id="a", generation=1, request_id="bc", nonce="n")
    assert a != b


# ---------------------------------------------------------------------------
# 11. Contract-vocabulary containment.
# ---------------------------------------------------------------------------


def test_repair_adds_no_new_failure_code():
    from pcae.core.hpac_pawa_helper_protocol import PAWA_FAILURE_CODES

    err = ReplayStateCorruption("x")
    assert err.code in PAWA_FAILURE_CODES
    assert err.code == "internal_fail_closed"
    assert isinstance(err, HelperProtocolError)


def test_replay_state_module_does_not_import_forbidden_legacy_module():
    src = Path(
        sys.modules["pcae.core.hpac_pawa_helper_replay_state"].__file__
    ).read_text()
    assert "import pcae.core.hpac_protected_admin_writer" not in src
    assert "from pcae.core.hpac_protected_admin_writer" not in src
