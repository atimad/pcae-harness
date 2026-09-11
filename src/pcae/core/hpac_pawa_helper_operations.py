"""HPAC-PAWA-HELPER-001 v1.0 — bounded per-operation foundations (§14-§17).

Each function implements the *shape* and the *bounded* semantics of exactly
one closed-vocabulary operation against the injected
:class:`~pcae.core.hpac_pawa_helper_protocol.ProtectedStoreFoundation`
(NON_REAL). No function here accepts a free path, expression, shell command,
module name, or JSON-patch blob (§25 generic-broker prohibition); every
input is the operation's own closed typed ``operation_params`` shape.

None of these functions perform a real store mutation, a real ceremony, or a
real presentation-evidence write — that wiring is explicitly out of scope
for this phase (phase-authorization §2/§40/§41).
"""

from __future__ import annotations

from typing import Mapping

from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_ADMIN_MUTATIONS,
    CLOSED_CERTIFICATION_ROLES,
    CLOSED_READ_RECORD_TYPES,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    HelperRequest,
    HelperResponse,
    HelperState,
    HelperStateMachine,
    performed_response,
)


def _run_mutation(
    request: HelperRequest,
    context: HelperContext,
    machine: HelperStateMachine,
    *,
    mutation_fn,
) -> HelperResponse:
    """Shared §20/§22 ordering: stage evidence, cross the no-retry boundary,
    perform the bounded mutation, commit, finalize, respond."""
    ref = context.evidence_stager.stage(request=request)
    machine.assert_may_start_mutation_attempt()
    machine.advance_to(HelperState.MUTATION_ATTEMPT_STARTED)
    context.replay_ledger.mark_consumed(request)  # spent the instant the boundary is crossed (§77)

    committed_digest = mutation_fn()
    machine.advance_to(HelperState.MUTATION_COMMITTED)

    try:
        ref, evidence_digest = context.evidence_stager.finalize(ref, committed_digest=committed_digest)
    except HelperProtocolError:
        # §21/§22: committed but not finalized -> INDETERMINATE / RECONCILIATION
        # REQUIRED. This is NOT reported as REJECTED/failure and NOT retried.
        machine.advance_to(HelperState.INDETERMINATE)
        raise
    machine.advance_to(HelperState.EVIDENCE_WRITTEN)
    response = performed_response(
        request,
        state_reached=HelperState.EVIDENCE_WRITTEN,
        evidence_ref=ref,
        evidence_digest=evidence_digest,
    )
    machine.advance_to(HelperState.RESPONSE_EMITTED)
    return response


def handle_admin_mutation(request: HelperRequest, context: HelperContext, machine: HelperStateMachine) -> HelperResponse:
    """§14.1. ``configure_privileged_helper`` remains metadata-only — it
    never creates/copies helper bytes and never chmod/chowns a path
    (phase-authorization §14); this foundation enforces that by construction
    (it only ever writes a metadata record to the injected store)."""
    mutation = request.operation_params.get("mutation")
    if mutation not in CLOSED_ADMIN_MUTATIONS:
        raise HelperProtocolError("operation_scope_invalid", f"unknown admin mutation {mutation!r}")
    transaction_id = request.operation_params.get("transaction_id")
    if mutation != "configure_privileged_helper" and not transaction_id:
        raise HelperProtocolError("operation_scope_invalid", "missing transaction_id")

    def _do_write() -> str:
        key = f"{request.session_id}:{mutation}:{request.request_id}"
        record = {
            "mutation": mutation,
            "transaction_id": transaction_id,
            "session_id": request.session_id,
            "committed_by": "hpac_pawa_helper_operations.handle_admin_mutation",
        }
        context.store.put_record("admin_mutation_record", key, record)
        return key

    return _run_mutation(request, context, machine, mutation_fn=_do_write)


def handle_certification_write(request: HelperRequest, context: HelperContext, machine: HelperStateMachine) -> HelperResponse:
    """§14.2. Role is re-checked here even though ``validate_and_admit``
    already checked it (defence in depth; a future admission-path refactor
    must not silently drop the role gate)."""
    if request.role not in CLOSED_CERTIFICATION_ROLES:
        raise HelperProtocolError("operation_scope_invalid", "certification_write requires a closed-five role")
    subject = request.proof_id if request.role != "hpac_rhamp_counter_state_verifier" else request.credential_id
    if not subject:
        raise HelperProtocolError("target_scope_invalid", "missing role-appropriate subject binding")

    def _do_write() -> str:
        key = f"{request.role}:{subject}:{request.session_id}"
        context.store.put_record(
            "certification_write_record",
            key,
            {"role": request.role, "subject": subject, "session_id": request.session_id},
        )
        return key

    return _run_mutation(request, context, machine, mutation_fn=_do_write)


def handle_certification_read(request: HelperRequest, context: HelperContext, machine: HelperStateMachine) -> HelperResponse:
    """§15. Returns only the enumerated record's *contents*, never a store
    handle; repeated reads never widen into a generic enumeration
    (HPAC-PAWA-HELPER-REQ-065)."""
    record_type = request.operation_params.get("record_type")
    key = request.operation_params.get("record_key")
    if record_type not in CLOSED_READ_RECORD_TYPES:
        raise HelperProtocolError("operation_scope_invalid", f"record_type {record_type!r} not in enumerated read set")
    if not key:
        raise HelperProtocolError("target_scope_invalid", "missing record_key")
    contents = context.store.get_record(record_type, key)
    if contents is None:
        raise HelperProtocolError("target_scope_invalid", "no such record for the bound session")

    machine.advance_to(HelperState.RESULT_EMITTED)
    context.evidence_stager.stage(request=request)  # §22/§89: audit the read; no staged->committed ordering needed
    return performed_response(
        request,
        state_reached=HelperState.RESULT_EMITTED,
        result_payload={"record_type": record_type, "record_key": key, "contents": contents},
    )


def handle_ceremony_entry(request: HelperRequest, context: HelperContext, machine: HelperStateMachine) -> HelperResponse:
    """§16. The *only* effect is handing off the canonical ceremony request
    bytes; the acknowledgement is a reference, never an authority object,
    never the ceremony's outcome (ceremony_entry != approval/Gate5/etc.)."""
    if request.session_id in context.store.ceremonies_started:
        raise HelperProtocolError("capability_stale", "ceremony_entry already used for this session")
    ceremony_request_bytes = request.operation_params.get("ceremony_request_digest")
    if not ceremony_request_bytes:
        raise HelperProtocolError("operation_scope_invalid", "missing ceremony_request_digest")

    context.store.ceremonies_started[request.session_id] = ceremony_request_bytes
    machine.advance_to(HelperState.RESULT_EMITTED)
    return performed_response(
        request,
        state_reached=HelperState.RESULT_EMITTED,
        result_payload={
            "acknowledgement": "ceremony_started",
            "ceremony_reference": f"ppa-ceremony/{request.session_id}",
        },
    )


def handle_presentation_evidence_write(request: HelperRequest, context: HelperContext, machine: HelperStateMachine) -> HelperResponse:
    """§17. Rejects any attempt to self-assert approved/verified/human_present
    /authenticated (HPAC-PAWA-HELPER-REQ-071) — those fields are simply not
    accepted in ``operation_params`` at all; only a pre-validated
    ``ceremony_approve_ref`` (produced solely by the PPA ceremony, out of
    scope here) is accepted, and this foundation still requires the caller
    to have independently proven it via the injected store."""
    forbidden = {"approved", "verified", "human_present", "authenticated"}
    if forbidden & set(request.operation_params):
        raise HelperProtocolError(
            "operation_scope_invalid",
            "presentation_evidence_write cannot accept caller-asserted approval/authentication facts",
        )
    approve_ref = request.operation_params.get("ceremony_approve_ref")
    if not approve_ref or context.store.ceremonies_started.get(request.session_id) is None:
        raise HelperProtocolError("target_scope_invalid", "no bound, started ceremony for this session")

    def _do_write() -> str:
        key = f"{request.session_id}:{approve_ref}"
        context.store.presentation_evidence[key] = {
            "session_id": request.session_id,
            "approve_ref": approve_ref,
        }
        return key

    return _run_mutation(request, context, machine, mutation_fn=_do_write)


#: The exact 5-key closed dispatch table (validated by
#: ``hpac_pawa_helper_protocol.dispatch`` on every call).
CLOSED_DISPATCH_TABLE: Mapping[str, object] = {
    HelperOperation.ADMIN_MUTATION.value: handle_admin_mutation,
    HelperOperation.CERTIFICATION_WRITE.value: handle_certification_write,
    HelperOperation.CERTIFICATION_READ.value: handle_certification_read,
    HelperOperation.CEREMONY_ENTRY.value: handle_ceremony_entry,
    HelperOperation.PRESENTATION_EVIDENCE_WRITE.value: handle_presentation_evidence_write,
}
