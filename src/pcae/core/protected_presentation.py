"""HPAC-PPA-001 v1.0 §6–§9 — the trusted protected-presentation launcher /
mediator and the runtime evidence-writer issuer, plus the resolver-side
real-``pcae-protected-local-presentation/1.0`` attestation verifier.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1; portable held-byte launch
repaired by phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.

This module is the **sole** launcher / mediator and the **sole** producer
of ``HPAC-PRESENTATION-EVIDENCE/2.0`` records for the real presentation
mechanism (HPAC-PPA-REQ-052/054). It:

* resolves and revalidates the current installation generation immediately
  before launch (HPAC-PPA-REQ-029/062) and opens the fixed helper once with
  no symlink traversal, hashing the opened bytes against the pinned digest;
* executes exactly that opened object (identity-preserving, no helper-path
  re-open — HPAC-PPA-REQ-030) via the fixed trusted interpreter reading the
  held fd; there is no shell, PATH, cwd lookup, caller argv, network, or
  generic subprocess API (HPAC-PPA-REQ-031);
* creates a fresh ≥256-bit CSPRNG nonce and a private parent/child pipe pair
  the requesting agent cannot write to (HPAC-PPA-REQ-034), binds the exact
  request, and validates the closed one-shot response (HPAC-PPA-REQ-035..039);
* only on one valid explicit ``APPROVE`` response mints — through the
  seal-guarded ``protected_presentation_mechanism`` runtime evidence-writer
  factory, held only here (HPAC-PPA-REQ-040/041) — one single-use writer and
  performs exactly one create-only ``HPAC-PRESENTATION-EVIDENCE/2.0`` write
  (HPAC-PPA-REQ-043..046);
* fails closed on ``REJECT`` / cancel / timeout / crash / malformed / dup /
  binding mismatch / post-launch currentness change, preserving no reusable
  writer (HPAC-PPA-REQ-044).

Launch permission is not PAWA installation authority and not runtime
dispatch authority (HPAC-PPA-REQ-033). This module implements no Gate wiring,
N-16-6, N-16-7, Slice C, adapter, ``DispatchEnvelope``, runtime capability,
or external effect.

The PAWA installer factory and the runtime evidence-writer factory are
imported **lazily**, inside the launch path only, so that
``hpac_verifier`` (and any other resolver-side caller) importing this module
for :func:`verify_protected_presentation_evidence` never transitively
imports the non-agent-importable admin-writer fence (HPAC-PPA-REQ-055).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import select
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    CanonicalRuntimeApprovalSubject,
    PresentationMechanismDescriptor,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationEvidence,
    TrustedApprovalPresentationStore,
    new_election_event_id,
    new_presentation_id,
    presentation_attestation_object,
    PRESENTATION_EVIDENCE_SCHEMA_VERSION,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACFoundationError,
    HPACStoreAuthority,
    canonical_digest,
    canonical_json_bytes,
)
from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError, TerminalReasonCode
from pcae.core.protected_presentation_installation import (
    MECHANISM_ID,
    VERIFIER_KIND,
    ProtectedPresentationInstallationError,
    ProtectedPresentationInstallationStore,
    ProtectedPresentationIntegrityError,
    ResolvedCurrentGeneration,
    verify_helper_bytes,
)

__all__ = [
    "MECHANISM_ID",
    "VERIFIER_KIND",
    "ProtectedPresentationCeremonyError",
    "ProtectedPresentationResult",
    "run_protected_presentation_ceremony",
    "verify_protected_presentation_evidence",
    "is_real_protected_presentation_verifier_kind",
]

_REQUEST_SCHEMA_VERSION = "HPAC-PPLP-REQUEST/1.0"
_RESPONSE_SCHEMA_VERSION = "HPAC-PPLP-RESPONSE/1.0"
_HELPER_MODULE = "pcae.protected_presentation_helper"
_HUMAN_VISIBLE_FACT_KEYS = (
    "repository_identity",
    "repository_display",
    "task_id",
    "task_display",
    "runtime_target_id",
    "runtime_target_display",
    "operation_effect_scope_display",
    "prompt_hash",
    "prompt_instruction_display",
    "invocation_id",
    "invocation_display",
    "expires_at",
    "one_shot_notice",
)
_DEFAULT_TIMEOUT_SECONDS = 120

# HPAC-PPA-REQ-030/031 — fixed interpreter bootstrap. macOS's system Python
# 3.9 exits successfully without executing ``python -I /dev/fd/N``. ``-c`` is
# portable across the supported interpreters and this constant reads and
# executes only the already-verified, inherited helper fd: no pathname reopen,
# PATH lookup, caller argv, shell, import from cwd, or substitution window.
_HELD_HELPER_BOOTSTRAP = (
    "import os\n"
    "_fd=int(os.environ['PCAE_PPLP_HELPER_FD'])\n"
    "_parts=[]\n"
    "while True:\n"
    " _part=os.read(_fd,1048576)\n"
    " if not _part: break\n"
    " _parts.append(_part)\n"
    "os.close(_fd)\n"
    "_source=b''.join(_parts)\n"
    "exec(compile(_source,'<pcae-protected-presentation-helper>','exec'),"
    "{'__name__':'__main__','__file__':'<pcae-protected-presentation-helper>'})\n"
)


class ProtectedPresentationCeremonyError(RhampTerminalError):
    """A protected-presentation ceremony failure carrying one frozen
    RHAMP-001 §49 ``terminal_reason_code`` (HPAC-PPA-REQ-076). No new
    terminal reason is introduced."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _self_excluding_digest(document: dict, *, field: str) -> str:
    projected = dict(document)
    projected[field] = ""
    return canonical_digest(projected)


def is_real_protected_presentation_verifier_kind(kind: object) -> bool:
    return kind == VERIFIER_KIND


@dataclass(frozen=True)
class ProtectedPresentationResult:
    """The outcome of one protected-presentation ceremony. On ``APPROVE`` it
    references the one durable ``HPAC-PRESENTATION-EVIDENCE/2.0`` record the
    launcher wrote; possession authorizes nothing — every consumer resolves
    the evidence freshly through the canonical store + verifier
    (HPAC-PPA-REQ-049)."""

    decision: str
    approval_id: str
    challenge_id: str
    invocation_id: str
    attempt_id: str
    installation_id: str
    generation: int
    presentation_id: Optional[str]
    presentation_digest: Optional[str]
    evidence: Optional[TrustedApprovalPresentationEvidence]
    responded_at: str


# ─────────────────────────────────────────────────────────────────────────
# Launcher / mediator
# ─────────────────────────────────────────────────────────────────────────


def _resolve_or_terminal(store: ProtectedPresentationInstallationStore) -> ResolvedCurrentGeneration:
    try:
        resolved = store.resolve_current_generation()
    except ProtectedPresentationIntegrityError as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_INTEGRITY_UNVERIFIED, str(exc)
        ) from exc
    if resolved is None:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_INTEGRITY_UNVERIFIED,
            "no current protected-presentation installation generation",
        )
    return resolved


def _validate_visible_subject_binding(human_visible_facts: dict, canonical_subject: CanonicalRuntimeApprovalSubject) -> None:
    if set(human_visible_facts) != set(_HUMAN_VISIBLE_FACT_KEYS):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_DIGEST_MISMATCH, "human_visible_facts is not the closed 13-field set"
        )
    subject = canonical_subject.subject
    if not isinstance(subject, dict):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.SUBJECT_DIGEST_MISMATCH, "canonical subject.subject is malformed"
        )
    for fact_key, subject_key in (
        ("repository_identity", "repository_identity"),
        ("task_id", "task_id"),
        ("runtime_target_id", "runtime_target_id"),
        ("prompt_hash", "prompt_hash"),
        ("invocation_id", "invocation_id"),
    ):
        if human_visible_facts.get(fact_key) != subject.get(subject_key):
            raise ProtectedPresentationCeremonyError(
                TerminalReasonCode.SUBJECT_DIGEST_MISMATCH,
                f"human-visible {fact_key} is not bound to the canonical subject",
            )
    if human_visible_facts.get("expires_at") != canonical_subject.expires_at:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.SUBJECT_DIGEST_MISMATCH, "human-visible expiry is not bound to the canonical subject"
        )
    if human_visible_facts.get("one_shot_notice") is not True or canonical_subject.attempt_limit != 1:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.SUBJECT_DIGEST_MISMATCH, "one-shot presentation binding is invalid"
        )


def run_protected_presentation_ceremony(
    *,
    authority: HPACStoreAuthority,
    approval_id: str,
    challenge_id: str,
    canonical_subject: CanonicalRuntimeApprovalSubject,
    human_visible_facts: dict,
    principal_id: str,
    invocation_id: str,
    attempt_id: str,
    presented_at: Optional[str] = None,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
    _test_decision_source: Optional[str] = None,
) -> ProtectedPresentationResult:
    """Run exactly one protected local human-approval ceremony for the
    installed ``pcae-protected-local-presentation`` mechanism and, on one
    valid explicit ``APPROVE``, persist exactly one
    ``HPAC-PRESENTATION-EVIDENCE/2.0`` record.

    ``_test_decision_source`` is the disclosed HPAC-PPA §16 test-only seam
    (mirrors ``hpac_protected_admin_writer``'s ``_topology_probe`` /
    ``_protected_root``): a decision directive string
    (``APPROVE`` / ``REJECT`` / ``CANCEL`` / ``NO_RESPONSE`` /
    ``MALFORMED_RESPONSE`` / ``CRASH``) delivered to the helper over the
    private channel *only* when set. A guard test asserts no production
    caller passes it, and it forces ``ceremony_mode == "test-only"``.
    """

    if not isinstance(authority, HPACStoreAuthority):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, "an HPACStoreAuthority is required"
        )
    presented_at = presented_at or _now()
    store = ProtectedPresentationInstallationStore(authority)
    resolved = _resolve_or_terminal(store)

    _validate_visible_subject_binding(human_visible_facts, canonical_subject)

    deployment_owner_uid = authority.root.stat().st_uid
    try:
        verified = verify_helper_bytes(
            resolved.helper_path,
            expected_sha256=resolved.record.helper_sha256,
            deployment_owner_uid=deployment_owner_uid,
            protected_root=authority.root,
        )
    except ProtectedPresentationIntegrityError as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_INTEGRITY_UNVERIFIED, str(exc)
        ) from exc

    nonce = os.urandom(32).hex()
    request_id = f"hpr-{uuid.uuid4().hex}"
    renderer_profile = resolved.record.renderer_profile
    displayed_bytes = _render_human_visible_bytes(human_visible_facts, renderer_profile=renderer_profile)
    displayed_digest = hashlib.sha256(displayed_bytes).hexdigest()

    if canonical_subject.approval_preview_digest != displayed_digest:
        os.close(verified.fd)
        # RHAMP-REQ-093/094 — `approval_preview_digest` SHALL equal the
        # re-rendered human-visible representation digest.
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_DIGEST_MISMATCH,
            "canonical_subject.approval_preview_digest != re-rendered human_visible_representation_digest",
        )

    approval_subject_digest = canonical_subject.digest()
    presentation_digest_placeholder = _canonical_subject_bound_presentation_digest(
        approval_id=approval_id,
        approval_subject_digest=approval_subject_digest,
        human_visible_representation_digest=displayed_digest,
        descriptor_digest=resolved.record.descriptor_digest,
    )

    request = _build_request(
        ceremony_mode="test-only" if _test_decision_source is not None else "production",
        nonce=nonce,
        request_id=request_id,
        approval_id=approval_id,
        challenge_id=challenge_id,
        presentation_digest=presentation_digest_placeholder,
        approval_subject_digest=approval_subject_digest,
        principal_id=principal_id,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        expires_at=canonical_subject.expires_at,
        resolved=resolved,
        human_visible_facts=human_visible_facts,
    )
    if _test_decision_source is not None:
        request["test_decision_directive"] = {
            "decision": _test_decision_source,
            "displayed_digest_ack": displayed_digest,
        }

    response = _launch_and_exchange(verified.fd, request, timeout_seconds=timeout_seconds)

    if response is None:
        # No response bytes: cancel / EOF / crash — no approval evidence.
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.CEREMONY_CANCELLED, "the protected helper produced no response"
        )

    decision = _validate_response(response, request, displayed_digest=displayed_digest)

    # HPAC-PPA-REQ-045/062 — revalidate currentness immediately before any
    # persistence; a generation switch supersedes this ceremony.
    revalidated = _resolve_or_terminal(store)
    if (
        revalidated.anchor.current_generation != resolved.anchor.current_generation
        or revalidated.record.installation_digest != resolved.record.installation_digest
        or revalidated.record.descriptor_digest != resolved.record.descriptor_digest
    ):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.CEREMONY_SUPERSEDED,
            "the installation generation changed during the ceremony",
        )

    if decision == "REJECT":
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.APPROVAL_REJECTED_BY_HUMAN, "the human explicitly rejected the operation"
        )

    # decision == APPROVE — persist exactly one evidence record.
    evidence = _build_and_persist_evidence(
        authority=authority,
        resolved=resolved,
        approval_id=approval_id,
        canonical_subject=canonical_subject,
        approval_subject_digest=approval_subject_digest,
        human_visible_facts=human_visible_facts,
        human_visible_representation_digest=displayed_digest,
        presented_at=presented_at,
        responded_at=response["responded_at"],
    )

    return ProtectedPresentationResult(
        decision="APPROVE",
        approval_id=approval_id,
        challenge_id=challenge_id,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        installation_id=resolved.anchor.installation_id,
        generation=resolved.anchor.current_generation,
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
        evidence=evidence,
        responded_at=response["responded_at"],
    )


def _canonical_subject_bound_presentation_digest(
    *, approval_id: str, approval_subject_digest: str, human_visible_representation_digest: str, descriptor_digest: str
) -> str:
    return canonical_digest(
        {
            "bind": "pcae-protected-local-presentation-request",
            "approval_id": approval_id,
            "approval_subject_digest": approval_subject_digest,
            "human_visible_representation_digest": human_visible_representation_digest,
            "descriptor_digest": descriptor_digest,
        }
    )


def _render_human_visible_bytes(human_visible_facts: dict, *, renderer_profile: str) -> bytes:
    # The renderer lives in the helper module so a single implementation is
    # both executed by the helper and re-rendered here for digest equality.
    from pcae.protected_presentation_helper import render_human_visible_bytes

    return render_human_visible_bytes(human_visible_facts, renderer_profile=renderer_profile)


def _build_request(
    *,
    ceremony_mode: str,
    nonce: str,
    request_id: str,
    approval_id: str,
    challenge_id: str,
    presentation_digest: str,
    approval_subject_digest: str,
    principal_id: str,
    invocation_id: str,
    attempt_id: str,
    expires_at: str,
    resolved: ResolvedCurrentGeneration,
    human_visible_facts: dict,
) -> dict:
    document = {
        "request_schema_version": _REQUEST_SCHEMA_VERSION,
        "ceremony_mode": ceremony_mode,
        "nonce": nonce,
        "request_id": request_id,
        "approval_id": approval_id,
        "challenge_id": challenge_id,
        "presentation_digest": presentation_digest,
        "approval_subject_digest": approval_subject_digest,
        "principal_id": principal_id,
        "invocation_id": invocation_id,
        "attempt_id": attempt_id,
        "expires_at": expires_at,
        "mechanism_id": MECHANISM_ID,
        "installation_id": resolved.anchor.installation_id,
        "generation": resolved.anchor.current_generation,
        "installation_digest": resolved.record.installation_digest,
        "descriptor_digest": resolved.record.descriptor_digest,
        "renderer_profile": resolved.record.renderer_profile,
        "human_visible_facts": human_visible_facts,
        "request_digest": "",
    }
    document["request_digest"] = _self_excluding_digest(document, field="request_digest")
    return document


def _launch_and_exchange(helper_fd: int, request: dict, *, timeout_seconds: int) -> Optional[dict]:
    req_r, req_w = os.pipe()
    resp_r, resp_w = os.pipe()
    os.set_inheritable(req_r, True)
    os.set_inheritable(resp_w, True)
    os.set_inheritable(helper_fd, True)
    payload = canonical_json_bytes({k: v for k, v in request.items()})

    env = {
        # HPAC-PPA-REQ-032 — a closed minimal allowlist; the fd numbers are
        # the only channel by which the helper learns the private pipes.
        "PCAE_PPLP_REQUEST_FD": str(req_r),
        "PCAE_PPLP_RESPONSE_FD": str(resp_w),
        "PCAE_PPLP_HELPER_FD": str(helper_fd),
        "LC_ALL": "C",
    }
    # HPAC-PPA-REQ-031 — a fixed local one-shot invocation with a fixed
    # executable identity (the trusted interpreter) and fixed argv; no shell,
    # PATH lookup, caller argv extension, cwd lookup, network, or generic
    # subprocess API. posix_spawn avoids fork() in a possibly multi-threaded
    # runtime.
    pid = os.posix_spawn(
        sys.executable,
        [sys.executable, "-I", "-c", _HELD_HELPER_BOOTSTRAP],
        env,
        file_actions=[
            # Ordinary inherited stdio is structurally ineligible for either
            # protocol or election input. The helper opens /dev/tty itself.
            (os.POSIX_SPAWN_CLOSE, 0),
            (os.POSIX_SPAWN_CLOSE, 1),
            (os.POSIX_SPAWN_CLOSE, 2),
            (os.POSIX_SPAWN_CLOSE, req_w),
            (os.POSIX_SPAWN_CLOSE, resp_r),
        ],
    )

    os.close(req_r)
    os.close(resp_w)
    os.close(helper_fd)
    try:
        os.write(req_w, payload)
    finally:
        os.close(req_w)

    chunks: list[bytes] = []
    try:
        while True:
            ready, _, _ = select.select([resp_r], [], [], timeout_seconds)
            if not ready:
                os.kill(pid, 9)
                os.waitpid(pid, 0)
                raise ProtectedPresentationCeremonyError(
                    TerminalReasonCode.CEREMONY_TIMED_OUT, "the protected helper did not respond in time"
                )
            chunk = os.read(resp_r, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(resp_r)
    _, status = os.waitpid(pid, 0)
    if os.WIFSIGNALED(status) or (os.WIFEXITED(status) and os.WEXITSTATUS(status) != 0):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED,
            f"the protected helper exited abnormally (status {status})",
        )
    raw = b"".join(chunks)
    if not raw:
        return None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, f"helper response is not canonical JSON: {exc}"
        ) from exc
    if raw != canonical_json_bytes(document):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, "helper response is not exact canonical JSON"
        )
    return document


_RESPONSE_KEYS = frozenset(
    {
        "response_schema_version",
        "nonce",
        "request_id",
        "approval_id",
        "challenge_id",
        "presentation_digest",
        "mechanism_id",
        "installation_id",
        "generation",
        "installation_digest",
        "descriptor_digest",
        "renderer_profile",
        "human_visible_representation_digest",
        "decision",
        "responded_at",
        "response_digest",
    }
)


def _validate_response(response: dict, request: dict, *, displayed_digest: str) -> str:
    if not isinstance(response, dict) or set(response) != _RESPONSE_KEYS:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, "helper response closed-field-set violation"
        )
    if response["response_schema_version"] != _RESPONSE_SCHEMA_VERSION:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, "helper response schema version mismatch"
        )
    digest = response["response_digest"]
    if _self_excluding_digest(response, field="response_digest") != digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, "helper response_digest does not recompute"
        )
    for key in (
        "nonce",
        "request_id",
        "approval_id",
        "challenge_id",
        "presentation_digest",
        "mechanism_id",
        "installation_id",
        "generation",
        "installation_digest",
        "descriptor_digest",
        "renderer_profile",
    ):
        if response[key] != request[key]:
            raise ProtectedPresentationCeremonyError(
                TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED,
                f"helper response {key} is not bound to the request",
            )
    if response["human_visible_representation_digest"] != displayed_digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_DIGEST_MISMATCH,
            "helper response human_visible_representation_digest != re-rendered bytes",
        )
    decision = response["decision"]
    if decision not in ("APPROVE", "REJECT"):
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, f"helper response decision {decision!r} is outside the closed vocabulary"
        )
    return decision


def _build_and_persist_evidence(
    *,
    authority: HPACStoreAuthority,
    resolved: ResolvedCurrentGeneration,
    approval_id: str,
    canonical_subject: CanonicalRuntimeApprovalSubject,
    approval_subject_digest: str,
    human_visible_facts: dict,
    human_visible_representation_digest: str,
    presented_at: str,
    responded_at: str,
) -> TrustedApprovalPresentationEvidence:
    descriptor = resolved.descriptor
    mechanism_ref = {
        "mechanism_id": descriptor.mechanism_id,
        "descriptor_version": descriptor.descriptor_version,
        "descriptor_digest": descriptor.descriptor_digest,
    }
    election = {"event_id": new_election_event_id(), "action": "approve", "occurred_at": responded_at}
    presentation_id = new_presentation_id()

    unsigned_body = {
        "presentation_schema_version": PRESENTATION_EVIDENCE_SCHEMA_VERSION,
        "presentation_id": presentation_id,
        "approval_id": approval_id,
        "canonical_subject": canonical_subject.to_document(),
        "approval_subject_digest": approval_subject_digest,
        "mechanism_ref": mechanism_ref,
        "human_visible_facts": human_visible_facts,
        "human_visible_representation_digest": human_visible_representation_digest,
        "presented_at": presented_at,
        "election": election,
        "mechanism_attestation": "",
        "mechanism_attestation_digest": "",
    }
    unsigned_evidence = TrustedApprovalPresentationEvidence(presentation_digest="", **unsigned_body)
    attestation_object = presentation_attestation_object(unsigned_evidence)
    attestation_bytes = canonical_json_bytes(attestation_object)
    mechanism_attestation = base64.urlsafe_b64encode(attestation_bytes).decode("ascii").rstrip("=")
    mechanism_attestation_digest = hashlib.sha256(attestation_bytes).hexdigest()

    body_without_digest = {
        **unsigned_body,
        "mechanism_attestation": mechanism_attestation,
        "mechanism_attestation_digest": mechanism_attestation_digest,
    }
    presentation_digest = canonical_digest(body_without_digest)
    evidence = TrustedApprovalPresentationEvidence(presentation_digest=presentation_digest, **body_without_digest)

    # HPAC-PPA-REQ-041 — the seal-guarded, process-local, single-use runtime
    # evidence-writer capability. Imported lazily so a resolver-side importer
    # never pulls the non-agent-importable admin-writer fence.
    from pcae.core.hpac_protected_admin_writer import mint_protected_presentation_evidence_writer

    try:
        writer = mint_protected_presentation_evidence_writer(authority, mechanism_id=MECHANISM_ID)
    except Exception as exc:  # PawaError / HPACAuthorityError
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, f"evidence-writer issuance refused: {exc}"
        ) from exc

    installed_descriptor = PresentationMechanismDescriptorStore(authority).resolve_canonical(MECHANISM_ID)
    if installed_descriptor is None:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_INTEGRITY_UNVERIFIED, "installed descriptor vanished before evidence persistence"
        )
    store = TrustedApprovalPresentationStore(authority)
    try:
        return store.create_canonical(writer, evidence, installed_descriptor)
    except (ApprovalPresentationTrustError, HPACAuthorityError, HPACFoundationError) as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED, f"evidence persistence failed: {exc}"
        ) from exc


# ─────────────────────────────────────────────────────────────────────────
# Resolver-side real-attestation verifier (HPAC-PPA-REQ-047/048/050)
# ─────────────────────────────────────────────────────────────────────────


def verify_protected_presentation_evidence(
    *,
    authority: HPACStoreAuthority,
    evidence: TrustedApprovalPresentationEvidence,
    descriptor: PresentationMechanismDescriptor,
) -> None:
    """Verify a resolved ``HPAC-PRESENTATION-EVIDENCE/2.0`` record's real
    ``pcae-protected-local-presentation/1.0`` ``mechanism_attestation``
    against the current installation generation.

    Called by ``approval_presentation`` (attestation verification for the
    real kind) and, transitively, by ``hpac_verifier`` step 5. It never
    imports the admin-writer fence and mints nothing.

    Raises :class:`ProtectedPresentationCeremonyError` (frozen RHAMP §49
    terminal reason) on any mismatch, superseded/revoked generation, or
    attestation failure.
    """

    if descriptor.verifier_kind != VERIFIER_KIND:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID,
            "verify_protected_presentation_evidence called for a non-real verifier kind",
        )
    store = ProtectedPresentationInstallationStore(authority)
    resolved = _resolve_or_terminal(store)

    # HPAC-PPA-REQ-048/050 — the descriptor digest must resolve through the
    # CURRENT anchor for an ACTIVE generation; a rotated/revoked generation's
    # evidence is stale.
    if evidence.mechanism_ref.get("descriptor_digest") != resolved.record.descriptor_digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.CEREMONY_SUPERSEDED,
            "evidence is bound to a superseded/revoked presentation generation",
        )
    if resolved.descriptor.descriptor_digest != descriptor.descriptor_digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.CEREMONY_SUPERSEDED,
            "the resolved presentation descriptor is not the current generation's descriptor",
        )
    if resolved.descriptor.verifier_kind != VERIFIER_KIND:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, "current descriptor verifier_kind mismatch"
        )

    # HPAC-REQ-092 — the attestation is exactly the closed 8-field
    # HPAC-PRESENTATION-ATTESTATION/2.0 object binding this evidence.
    attestation_bytes = _decode_attestation(evidence.mechanism_attestation)
    if hashlib.sha256(attestation_bytes).hexdigest() != evidence.mechanism_attestation_digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, "mechanism_attestation_digest does not bind decoded bytes"
        )
    try:
        attestation_object = json.loads(attestation_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, f"attestation object is malformed: {exc}"
        ) from exc
    expected = presentation_attestation_object(evidence)
    if attestation_object != expected or canonical_json_bytes(attestation_object) != attestation_bytes:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, "attestation object does not bind the evidence exactly"
        )
    if attestation_object.get("descriptor_digest") != resolved.record.descriptor_digest:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.CEREMONY_SUPERSEDED, "attestation descriptor_digest is not the current generation"
        )


def _decode_attestation(value: object) -> bytes:
    if not isinstance(value, str) or not value:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, "mechanism_attestation is empty"
        )
    try:
        padded = value + "=" * (-len(value) % 4)
        return base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise ProtectedPresentationCeremonyError(
            TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID, "mechanism_attestation is not base64url"
        ) from exc
