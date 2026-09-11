"""N16-5-F-5-TB-HELPER-IV — fresh independent verification of the
privileged-helper + HPAC-PAWA-HELPER/1.0 protocol foundation implemented by
N16-5-F-5-TB-HELPER-IMPL / N16-5-F-5-TB-HELPER-IMPL.1
(``pcae.core.hpac_pawa_helper_protocol`` / ``_operations`` / ``_os``).

This file is verification-only. It does NOT modify, patch, or repair any
production module. Every test here is disposable: temp directories, temp
sockets, subprocess-isolated interpreters, in-memory fixtures. Nothing
touches a real ``<HPAC_PROTECTED_ROOT>``, no real hardware, no sudo, no real
ceremony/certification.

Scope covered by this file specifically (areas not already covered, or not
covered *cross-process*, by ``test_hpac_pawa_helper_protocol_foundation.py``):

  1. REPLAY-AFTER-RESTART — independently reproduced via two genuinely
     separate Python interpreter *processes* (not two objects in one
     process), matching phase-authorization framing. This is the
     authoritative reproduction of the blocking defect this IV phase exists
     to confirm.
  2. Response-loss cross-process: a mutation is marked consumed in process A
     (simulating a committed mutation whose response was lost), then a
     brand-new process B evaluates the identical request. Confirms process B
     does NOT see "consumed" — it sees FRESH, because no durable state
     survives the process boundary.
  3. Indeterminate-crash cross-process: process A crosses
     MUTATION_ATTEMPT_STARTED without reaching a terminal disposition
     (simulating a crash between commit and evidence-finalize), then a fresh
     process B evaluates the identical request. Confirms process B has no
     way to observe "indeterminate" — again, FRESH.
  4. Structural confirmation (source inspection, not behavioral): the
     ``ReplayLedger`` and ``ProtectedStoreFoundation`` classes perform no
     filesystem/network I/O anywhere in their bodies — i.e. "process-local
     in-memory" is a source-verifiable fact, not an inference from behavior
     alone.
  5. macOS same-file-object execution: confirms ``execute_verified`` fails
     closed on the *actual* current (unpatched) platform when it is not
     Linux, closing the gap left by the existing suite's ``monkeypatch``-only
     coverage of this path.
  6. Restart-dead-authority: a ``VerifiedExecutable`` file descriptor from
     process A is meaningless in process B (the OS reassigns fd numbers
     per-process); demonstrated structurally rather than by attempting to
     read a foreign fd (which is unsafe/undefined) — the dataclass carries a
     bare ``int`` with no serialization contract to make it portable.

All other scope areas listed in the phase authorization (process isolation,
no-ordinary-interpreter-authority-access, helper provenance, peer
credentials, configured-agent exclusion, closed dispatch, state transitions,
no-auto-retry, no-authority-export, five-role/typed-read closure,
ceremony_entry / presentation_evidence_write one-shot semantics,
deterministic-vs-real separation) are independently re-confirmed by re-running
the existing ``test_hpac_pawa_helper_protocol_foundation.py`` suite as part of
this IV's evidence (see the phase report's test tally) rather than
duplicated here line-for-line; this file adds only the areas that suite does
not already exercise.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
import textwrap

import pytest

from pcae.core.hpac_pawa_helper_os import UnsupportedPlatformProfile, execute_verified
from pcae.core.hpac_pawa_helper_protocol import (
    HelperOperation,
    ProtectedStoreFoundation,
    ReplayLedger,
    ReplayOutcome,
    build_signed_request,
)

# ---------------------------------------------------------------------------
# Shared fixed request used by the cross-process scenarios. A fixed
# request_id/nonce/session_id/operation/subject tuple lets an independent
# process reconstruct byte-identical replay-key material without any shared
# runtime state (only the JSON-serialized request travels across the
# process boundary, matching how a real launcher would resend a request).
# ---------------------------------------------------------------------------

_FIXED_REQUEST_ID = "req-restart-iv-0001"
_FIXED_NONCE = "n" * 64  # 256-bit hex-equivalent length, fixed for reproducibility
_FIXED_SESSION = "sess-restart-iv"


def _fixed_admin_request_mapping() -> dict:
    request = build_signed_request(
        operation=HelperOperation.ADMIN_MUTATION,
        session_id=_FIXED_SESSION,
        operation_params={"mutation": "enroll_principal", "transaction_id": "txn-restart-iv"},
        request_id=_FIXED_REQUEST_ID,
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-restart-iv",
        generation=1,
        nonce=_FIXED_NONCE,
    )
    return {
        "request_schema_version": request.request_schema_version,
        "protocol_version": request.protocol_version,
        "operation": request.operation,
        "operation_version": request.operation_version,
        "role": request.role,
        "session_id": request.session_id,
        "principal_id": request.principal_id,
        "credential_id": request.credential_id,
        "proof_id": request.proof_id,
        "operation_params": dict(request.operation_params),
        "request_id": request.request_id,
        "nonce": request.nonce,
        "expiry": request.expiry,
        "installation_id": request.installation_id,
        "generation": request.generation,
        "request_digest": request.request_digest,
    }


_PROCESS_A_MARK_CONSUMED = textwrap.dedent(
    """
    import json, sys
    from pcae.core.hpac_pawa_helper_protocol import HelperRequest, ReplayLedger

    data = json.loads(sys.argv[1])
    request = HelperRequest.from_mapping(data)
    ledger = ReplayLedger()
    outcome_a1 = ledger.check_and_mark_in_flight(request)
    ledger.mark_consumed(request)
    # process A now exits -- `ledger` and its process heap are destroyed.
    print(json.dumps({"process_a_first_admit_outcome": outcome_a1.value}))
    """
)

_PROCESS_A_CRASH_BEFORE_TERMINAL = textwrap.dedent(
    """
    import json, sys
    from pcae.core.hpac_pawa_helper_protocol import HelperRequest, ReplayLedger

    data = json.loads(sys.argv[1])
    request = HelperRequest.from_mapping(data)
    ledger = ReplayLedger()
    outcome_a1 = ledger.check_and_mark_in_flight(request)
    # crossed the no-retry boundary conceptually (in_flight=True) but never
    # called mark_consumed() -- simulates a crash strictly between
    # MUTATION_ATTEMPT_STARTED and a terminal (COMMITTED/INDETERMINATE)
    # durable disposition being recorded anywhere durable.
    print(json.dumps({"process_a_first_admit_outcome": outcome_a1.value}))
    """
)

_PROCESS_B_FRESH_HELPER_RE_EVALUATE = textwrap.dedent(
    """
    import json, sys
    from pcae.core.hpac_pawa_helper_protocol import HelperRequest, ReplayLedger

    data = json.loads(sys.argv[1])
    request = HelperRequest.from_mapping(data)
    # A brand-new helper process: a brand-new ReplayLedger with no
    # cross-process persistence layer feeding it (matches the current
    # production wiring exactly -- ReplayLedger() takes no durable-store
    # argument anywhere in this foundation).
    ledger = ReplayLedger()
    outcome_b = ledger.check_and_mark_in_flight(request)
    print(json.dumps({"process_b_outcome": outcome_b.value}))
    """
)


def _run_subprocess_script(script: str, request_mapping: dict) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", script, json.dumps(request_mapping)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"subprocess failed: rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 1. REPLAY-AFTER-RESTART -- the authoritative cross-process reproduction.
# ---------------------------------------------------------------------------


def test_replay_after_restart_cross_process_confirms_blocking_defect():
    """CONFIRMED BLOCKING DEFECT (REPLAY-AFTER-RESTART), reproduced across
    two genuinely separate OS processes, each with its own fresh
    ``ReplayLedger()`` and no shared/durable backing store.

    Process A admits+consumes the request and exits. Process B is started
    completely fresh (new interpreter, new heap, new ``ReplayLedger``) and
    evaluates the byte-identical request. Per HPAC-PAWA-HELPER-REQ-076 the
    request MUST NOT be treated as fresh once consumed. This test asserts
    the CURRENT (defective) behavior -- process B reports FRESH -- because
    that is what N16-5-F-5-TB-HELPER-IV exists to independently confirm, not
    to repair. A future N16-5-F-5-TB-REPLAY-REPAIR phase is expected to make
    this exact assertion fail (i.e. change the expected outcome to
    CONSUMED) as its acceptance criterion.
    """
    request_mapping = _fixed_admin_request_mapping()

    result_a = _run_subprocess_script(_PROCESS_A_MARK_CONSUMED, request_mapping)
    assert result_a["process_a_first_admit_outcome"] == ReplayOutcome.FRESH.value

    result_b = _run_subprocess_script(_PROCESS_B_FRESH_HELPER_RE_EVALUATE, request_mapping)

    # This assertion documents the CONFIRMED defect: a fresh helper process
    # cannot see that this exact (request_id, nonce) was already consumed by
    # a prior helper process's lifetime.
    assert result_b["process_b_outcome"] == ReplayOutcome.FRESH.value, (
        "if this now reads CONSUMED, the replay-after-restart defect has "
        "been repaired and this test's expected value (and its docstring) "
        "must be updated as part of that repair phase, not silently changed "
        "here"
    )


# ---------------------------------------------------------------------------
# 2. Response-loss cross-process.
# ---------------------------------------------------------------------------


def test_response_loss_cross_process_does_not_prevent_resurrection_today():
    """CONFIRMED BLOCKING DEFECT (response-loss variant of
    REPLAY-AFTER-RESTART). A mutation commits (process A calls
    ``mark_consumed``, modeling a committed mutation whose *response* to the
    caller was lost -- e.g. the one-shot channel died after commit but
    before the reply was read). A fresh helper process B later receives the
    identical resent request. The contract requires B to reconcile against
    durable state and return a consumed/completed disposition, never to
    silently re-admit as fresh. Today's foundation has no durable state for
    B to reconcile against, so it reports FRESH -- confirmed here."""
    request_mapping = _fixed_admin_request_mapping()

    _run_subprocess_script(_PROCESS_A_MARK_CONSUMED, request_mapping)  # commit, "response lost"
    result_b = _run_subprocess_script(_PROCESS_B_FRESH_HELPER_RE_EVALUATE, request_mapping)

    assert result_b["process_b_outcome"] == ReplayOutcome.FRESH.value


# ---------------------------------------------------------------------------
# 3. Indeterminate-crash cross-process.
# ---------------------------------------------------------------------------


def test_indeterminate_crash_cross_process_does_not_prevent_resurrection_today():
    """CONFIRMED BLOCKING DEFECT (indeterminate variant). Process A crosses
    the no-retry boundary (in-flight, not yet consumed) and then "crashes"
    (the harness process simply exits without calling ``mark_consumed``,
    modeling a crash between MUTATION_ATTEMPT_STARTED and any terminal
    durable disposition). A fresh process B must NOT treat this as fresh --
    contractually it should observe INDETERMINATE / reconciliation-required.
    Today's foundation has no durable in-flight marker either, so B reports
    FRESH -- confirmed here, and is in fact a strictly worse outcome than
    the "already consumed" case: an in-flight-but-uncommitted request can be
    silently re-admitted and its (possibly still-live) first attempt raced
    against."""
    request_mapping = _fixed_admin_request_mapping()

    _run_subprocess_script(_PROCESS_A_CRASH_BEFORE_TERMINAL, request_mapping)
    result_b = _run_subprocess_script(_PROCESS_B_FRESH_HELPER_RE_EVALUATE, request_mapping)

    assert result_b["process_b_outcome"] == ReplayOutcome.FRESH.value


# ---------------------------------------------------------------------------
# 4. Structural confirmation: no I/O anywhere in ReplayLedger /
#    ProtectedStoreFoundation. Source-verifiable, not merely inferred from
#    the two dynamic tests above.
# ---------------------------------------------------------------------------

_IO_MARKERS = ("open(", "os.write", "os.read", "Path(", "socket.", "connect(", "requests.", "urlopen")


def test_replay_ledger_has_no_durable_io_anywhere_in_its_source():
    source = inspect.getsource(ReplayLedger)
    for marker in _IO_MARKERS:
        assert marker not in source, (
            f"ReplayLedger unexpectedly contains {marker!r} -- if durability "
            "was added, this IV's structural finding is stale and must be "
            "re-adjudicated, not silently passed"
        )
    # __init__ constructs only an in-memory dict; the class takes no
    # constructor argument identifying a durable backing location (return
    # annotation is a forward-ref string under `from __future__ import
    # annotations`, hence comparing against the resolved annotations dict
    # rather than the raw signature repr).
    init_params = list(inspect.signature(ReplayLedger.__init__).parameters)
    assert init_params == ["self"]


def test_protected_store_foundation_has_no_durable_io_anywhere_in_its_source():
    source = inspect.getsource(ProtectedStoreFoundation)
    for marker in _IO_MARKERS:
        assert marker not in source
    init_params = list(inspect.signature(ProtectedStoreFoundation.__init__).parameters)
    assert init_params == ["self"]


# ---------------------------------------------------------------------------
# 5. macOS same-file-object execution -- real (unpatched) platform check.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    sys.platform.startswith("linux"),
    reason="this test documents the real (non-Linux) platform's fail-closed status; "
    "on Linux the supported path is covered by test_execute_verified_actually_runs_on_linux",
)
def test_execute_verified_fails_closed_on_real_current_non_linux_platform():
    """Confirms -- on the ACTUAL current platform, with no monkeypatching --
    that ``execute_verified`` still has no substitution-free exec primitive
    and fails closed. Closes a gap in the existing suite, which only proves
    this behavior after monkeypatching ``sys.platform`` to a synthetic
    value; this proves it for the real development host too (per
    phase-authorization: "verify this is still true and cleanly fail-closed,
    do not implement it")."""
    from dataclasses import replace as _dc_replace

    from pcae.core.hpac_pawa_helper_os import VerifiedExecutable

    # A syntactically well-formed VerifiedExecutable with an invalid fd is
    # sufficient: execute_verified's platform check happens before the fd is
    # dereferenced for exec on any unsupported platform.
    fake_verified = VerifiedExecutable(fd=-1, sha256="0" * 64, device=0, inode=0, owner_uid=0, mode=0o755, nlink=1)
    with pytest.raises(UnsupportedPlatformProfile):
        execute_verified(fake_verified, ["/bin/true"], {})
    # ensure the dataclass really is immutable/well-formed and not silently
    # coerced into something exec-shaped by this test's own construction.
    assert _dc_replace(fake_verified, fd=-1).fd == -1


# ---------------------------------------------------------------------------
# 6. Restart-dead-authority: an fd from process A is not portable to B.
# ---------------------------------------------------------------------------


def test_verified_executable_fd_is_process_local_not_a_portable_authority_token():
    """Structural confirmation that the one piece of "authority" the OS
    layer produces (an open, verified file descriptor) has no
    cross-process representation: the dataclass stores a bare OS-level
    ``int`` fd with no serialization/reconstruction method, so it cannot
    become a bearer token smuggled across the process boundary this IV is
    examining. This is the intended, CORRECT half of "authority dies /
    history persists" -- only the *history* (replay ledger) half is
    currently broken, confirmed above."""
    from pcae.core.hpac_pawa_helper_os import VerifiedExecutable

    field_types = {f.name: f.type for f in VerifiedExecutable.__dataclass_fields__.values()}
    assert field_types["fd"] == "int"
    assert not hasattr(VerifiedExecutable, "to_json")
    assert not hasattr(VerifiedExecutable, "serialize")
    # dataclasses provide a default __getstate__/__setstate__ in modern
    # Python (generic pickling support) -- that is not a bespoke portable
    # capability token; what matters is there is no custom cross-process
    # reconstruction method beyond stdlib pickling of a plain int field.
    assert "to_capability_token" not in dir(VerifiedExecutable)
    assert "from_wire" not in dir(VerifiedExecutable)
