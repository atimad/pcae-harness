"""RHAMP-001 v1.0 §13 / §14 / §15 / §31 — the protected-admin credential
registration + first-credential bootstrap ceremony, and the canonical
active-credential resolution used by authentication.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle — Decision A / RE-MERGE). This module is **inside the
non-agent-importable fence** (HPAC-PAWA-REQ-084/085): it imports
``hpac_protected_admin_writer`` and is itself driven only by the standalone
``scripts/hpac_principal_admin.py``, run by the deployment owner. Ordinary
agent / runtime / Gate / plugin / ``pcae`` CLI code SHALL NOT import it
(directly or transitively) — a guard test enforces this.

All credential enrollment / revocation / bootstrap authority originates from
the independently-verified Slice-1 PAWA production writer boundary
(``production_writer``) — **no second admin authority** (RHAMP-REQ-047/049,
HPAC-PAWA-REQ-140, PAWA-INV-2). No ``root``/``euid`` shortcut, no
``SUDO_USER``, no OS-username-to-human-principal inference, no agent-identity
authority.

The ``enroll_credential`` + ``RHAMP-FIDO2-CREDENTIAL/1.0`` sidecar +
``RHAMP-COUNTER-STATE/1.0`` writes are **one bounded enrollment transaction**
authorised by **one** ``_multi_write`` capability, spent once via
``authority.complete_multi_write`` after the final read-back
(HPAC-PAWA-REQ-106).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACStoreAuthority,
    canonical_digest,
    canonical_json_bytes,
    new_hpac_id,
    write_atomic_create_only,
)
from pcae.core.human_principal_registry import (
    CredentialRecord,
    HumanPrincipalRegistryConflictError,
    HumanPrincipalRegistryStore,
    new_credential_id,
)
from pcae.core.hpac_protected_admin_writer import (
    AUTHORITY_NAMESPACE,
    PawaError,
    PawaOperation,
    ProductionWriterHandle,
    production_writer,
)
from pcae.core.hpac_pawa_schemas import new_operation_id
from pcae.core.hpac_rhamp_client_context import MECHANISM_ID, build_client_context
from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore
from pcae.core.hpac_rhamp_credential_sidecar import (
    Fido2CredentialSidecar,
    HpacRhampCredentialSidecarStore,
    encode_raw_credential_id,
)
from pcae.core.hpac_rhamp_ctap2 import (
    Ctap2CancelledError,
    Ctap2Provider,
    Ctap2UnavailableError,
    MakeCredentialResult,
    resolve_production_ctap2_provider,
)
from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError, TerminalReasonCode

__all__ = [
    "ENROLLMENT_EVIDENCE_SCHEMA",
    "RhampEnrollmentError",
    "EnrollmentResult",
    "ActiveCredentialMaterial",
    "enroll_first_credential",
    "revoke_credential",
    "resolve_active_credentials",
    "resolve_authentication_allowlist",
]

ENROLLMENT_EVIDENCE_SCHEMA = "RHAMP-ENROLLMENT-EVIDENCE/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class RhampEnrollmentError(RhampTerminalError):
    """A terminal enrollment / bootstrap / revocation failure, carrying one
    RHAMP-001 §49 ``terminal_reason_code``."""


@dataclass(frozen=True)
class EnrollmentResult:
    credential_id: str
    principal_id: str
    raw_credential_id_digest: str
    mechanism_id: str
    transports: tuple[str, ...]
    enrollment_operation_id: str
    enrollment_evidence_ref: str
    credential_generation_before: Optional[str]
    credential_generation_after: str
    enrolled_at: str


@dataclass(frozen=True)
class ActiveCredentialMaterial:
    credential_id: str
    principal_id: str
    raw_credential_id: bytes
    cose_public_key: str  # hex(cbor(COSE_Key)) — == CredentialRecord.public_key
    transports: tuple[str, ...]


def _pawa_reason(exc: PawaError) -> RhampEnrollmentError:
    return RhampEnrollmentError(exc.rhamp_terminal_reason, f"PAWA {exc.code}: {exc.detail}")


def _require_active_principal(registry: HumanPrincipalRegistryStore, principal_id: str):
    principal = registry.resolve_principal(principal_id)
    if principal is None:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_PRINCIPAL_INELIGIBLE, f"principal {principal_id!r} is absent (RHAMP-REQ-044)"
        )
    if principal.status != "active":
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_PRINCIPAL_INELIGIBLE,
            f"principal {principal_id!r} is not active (RHAMP-REQ-044)",
        )
    return principal


def _reject_duplicate(registry: HumanPrincipalRegistryStore, credential_id: str, raw_credential_id: bytes) -> None:
    if registry.resolve_credential(credential_id) is not None:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_DUPLICATE_CREDENTIAL, f"credential_id already registered: {credential_id}"
        )
    raw_digest = hashlib.sha256(raw_credential_id).hexdigest()
    sidecar_store = HpacRhampCredentialSidecarStore(registry.authority)
    for existing in registry.list_credentials():
        sc = sidecar_store.resolve(existing.credential_id)
        if sc is not None and hashlib.sha256(_decode(sc.raw_credential_id)).hexdigest() == raw_digest:
            raise RhampEnrollmentError(
                TerminalReasonCode.ENROLLMENT_DUPLICATE_CREDENTIAL,
                "raw CTAP2 credential id is already registered (RHAMP-REQ-045 — 'first registrant wins' is prohibited)",
            )


def _decode(b64u: str) -> bytes:
    from pcae.core.hpac_rhamp_credential_sidecar import decode_raw_credential_id

    return decode_raw_credential_id(b64u)


def enroll_first_credential(
    *,
    principal_id: str,
    subject_digest: str,
    presentation_digest: str,
    invocation_id: str,
    attempt_id: str,
    provider: Optional[Ctap2Provider] = None,
    protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> EnrollmentResult:
    """RHAMP-REQ-043/048 — the frozen registration flow. Solves the
    non-circular bootstrap (RHAMP-REQ-047): an existing canonical
    ``PrincipalRecord`` + PAWA protected-admin authority + real CTAP2
    ``makeCredential`` → the first canonical real credential. **No prior
    real FIDO2 authentication is required for the first credential**
    (RHAMP-REQ-047); **no first-caller-wins** (RHAMP-REQ-045/049).

    ``provider`` defaults to the production native CTAP2 provider; CI passes
    an explicit :class:`DeterministicCtap2Provider` (RHAMP-REQ-154 — the
    fixture is reachable only by explicit construction).
    """

    provider = provider or resolve_production_ctap2_provider()
    transaction_id = new_operation_id()

    # §33 anchor recognition + PAWA authority (one bounded transaction).
    try:
        handle: ProductionWriterHandle = production_writer(
            PawaOperation.ENROLL_CREDENTIAL,
            principal_id=principal_id,
            transaction_id=transaction_id,
            _protected_root=protected_root,
            _configured_agent_identity_source=_configured_agent_identity_source,
            _topology_probe=_topology_probe,
        )
    except PawaError as exc:
        raise _pawa_reason(exc) from exc

    authority: HPACStoreAuthority = handle.authority
    registry = HumanPrincipalRegistryStore(authority)
    sidecar_store = HpacRhampCredentialSidecarStore(authority)
    counter_store = HpacRhampCounterStateStore(authority)

    principal = _require_active_principal(registry, principal_id)
    # RHAMP-REQ-051: ``credential_generation`` before is over the (as yet
    # absent) CredentialRecord — recorded as null for a first credential.
    generation_before: Optional[str] = None

    try:
        capability = handle.consume(
            PawaOperation.ENROLL_CREDENTIAL, principal_id=principal_id, transaction_id=transaction_id
        )
    except PawaError as exc:
        raise _pawa_reason(exc) from exc

    # RHAMP-REQ-043 — canonical native-CTAP2 client context for enrollment.
    credential_id = new_credential_id()
    enroll_context = build_client_context(
        ceremony_kind="credential-enrollment",
        challenge_digest=canonical_digest(
            {"kind": "credential-enrollment", "transaction_id": transaction_id, "principal_id": principal_id}
        ),
        approval_subject_digest=subject_digest,
        trusted_presentation_digest=presentation_digest,
        principal_id=principal_id,
        credential_id=credential_id,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        nonce=hashlib.sha256(f"{transaction_id}:{credential_id}".encode()).hexdigest(),
        issued_at=_now(),
        expires_at=_now(),
    )

    try:
        mc: MakeCredentialResult = provider.make_credential(
            client_data_hash=enroll_context.client_data_hash,
            user_id=hashlib.sha256(principal_id.encode()).digest(),
            user_name=principal_id,
        )
    except Ctap2CancelledError:
        raise
    except Ctap2UnavailableError as exc:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID, f"makeCredential unavailable: {exc.detail}"
        ) from exc

    # RHAMP-REQ-022/048 — validate the creation result before publication.
    if not (mc.up and mc.uv):
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID,
            "makeCredential response is not UP+UV (RHAMP-REQ-033 floor)",
        )
    if mc.transport not in ("usb", "nfc"):
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID,
            f"unsupported transport {mc.transport!r} (RHAMP-REQ-132)",
        )
    if not mc.raw_credential_id or not mc.cose_public_key:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID, "makeCredential response missing material"
        )

    _reject_duplicate(registry, credential_id, mc.raw_credential_id)

    public_key_hex = mc.cose_public_key.hex()
    enrolled_at = _now()
    enrollment_provenance_ref = f"{AUTHORITY_NAMESPACE}/issuance-evidence/{handle.operation_id}.json"

    # ── the one bounded enrollment transaction (RHAMP-REQ-043 / §24/§25) ──
    # Order: sidecar + counter (create-only, orphan-safe) → registry
    # (append) → complete. A failure before the registry write leaves only
    # orphan create-only files and no registry credential; a failure after
    # leaves a registry credential with no usable material — both are
    # non-authoritative to `resolve_active_credentials` (RHAMP-REQ-041/026).
    sidecar = Fido2CredentialSidecar(
        credential_id=credential_id,
        principal_id=principal_id,
        raw_credential_id=encode_raw_credential_id(mc.raw_credential_id),
        cose_public_key=public_key_hex,
        transports=(mc.transport,),
        aaguid=mc.aaguid.hex() if mc.aaguid else None,
        created_at=enrolled_at,
        writer_provenance_ref="pending",  # computed inside the store
        status="active",
    )
    try:
        sidecar_store.create_canonical(capability, sidecar, transaction_subject=transaction_id)
        counter_store.initialize_canonical(
            capability, credential_id=credential_id, updated_at=enrolled_at, transaction_subject=transaction_id
        )
        record: CredentialRecord = registry.enroll_credential(
            capability,
            credential_id=credential_id,
            principal_id=principal_id,
            mechanism_id=MECHANISM_ID,
            public_key=public_key_hex,
            assurance_capabilities=("UP", "UV", mc.transport),
            enrollment_provenance_ref=enrollment_provenance_ref,
            enrolled_at=enrolled_at,
            _production_transaction_subject=transaction_id,
        )
        authority.complete_multi_write(capability)
    except HumanPrincipalRegistryConflictError as exc:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_DUPLICATE_CREDENTIAL, str(exc)
        ) from exc
    except (HPACAuthorityError, PawaError) as exc:
        raise RhampEnrollmentError(
            TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID,
            f"enrollment transaction write failed: {exc}",
        ) from exc

    # RHAMP-REQ-025 — read-back the whole published set before it is ACTIVE.
    material = _resolve_material(registry, sidecar_store, credential_id)
    # RHAMP-REQ-118 — credential_generation is the whole-record canonical
    # digest of the current CredentialRecord (HPAC-REQ-098a). No parallel
    # freshness system.
    generation_after = canonical_digest(record.to_document())

    # RHAMP-REQ-051 — durable enrollment evidence (audit, not authority).
    evidence_ref = _write_enrollment_evidence(
        authority,
        operation_id=handle.operation_id,
        transaction_id=transaction_id,
        principal_id=principal_id,
        credential_id=credential_id,
        raw_credential_id_digest=hashlib.sha256(mc.raw_credential_id).hexdigest(),
        mechanism_id=MECHANISM_ID,
        enrollment_nonce_id=enroll_context.nonce,
        registrar_provenance_ref=enrollment_provenance_ref,
        credential_generation_before=generation_before,
        credential_generation_after=generation_after,
        enrolled_at=enrolled_at,
    )

    return EnrollmentResult(
        credential_id=credential_id,
        principal_id=principal_id,
        raw_credential_id_digest=hashlib.sha256(mc.raw_credential_id).hexdigest(),
        mechanism_id=MECHANISM_ID,
        transports=material.transports,
        enrollment_operation_id=handle.operation_id,
        enrollment_evidence_ref=evidence_ref,
        credential_generation_before=generation_before,
        credential_generation_after=generation_after,
        enrolled_at=enrolled_at,
    )


def _resolve_material(
    registry: HumanPrincipalRegistryStore,
    sidecar_store: HpacRhampCredentialSidecarStore,
    credential_id: str,
) -> ActiveCredentialMaterial:
    sidecar = sidecar_store.resolve_against_registry(credential_id, registry)
    credential = registry.resolve_credential(credential_id)
    assert credential is not None  # resolve_against_registry already checked
    return ActiveCredentialMaterial(
        credential_id=credential_id,
        principal_id=credential.principal_id,
        raw_credential_id=_decode(sidecar.raw_credential_id),
        cose_public_key=sidecar.cose_public_key,
        transports=sidecar.transports,
    )


_ENROLLMENT_EVIDENCE_FIELDS = (
    "artifact_schema_version",
    "record_digest",
    "enrollment_operation_id",
    "enrollment_transaction_id",
    "principal_id",
    "credential_id",
    "raw_credential_id_digest",
    "mechanism_id",
    "enrollment_nonce_id",
    "registrar_provenance_ref",
    "credential_generation_before",
    "credential_generation_after",
    "enrolled_at",
)


def _write_enrollment_evidence(
    authority: HPACStoreAuthority,
    *,
    operation_id: str,
    transaction_id: str,
    principal_id: str,
    credential_id: str,
    raw_credential_id_digest: str,
    mechanism_id: str,
    enrollment_nonce_id: str,
    registrar_provenance_ref: str,
    credential_generation_before: Optional[str],
    credential_generation_after: str,
    enrolled_at: str,
) -> str:
    document = {
        "artifact_schema_version": ENROLLMENT_EVIDENCE_SCHEMA,
        "record_digest": "",
        "enrollment_operation_id": operation_id,
        "enrollment_transaction_id": transaction_id,
        "principal_id": principal_id,
        "credential_id": credential_id,
        "raw_credential_id_digest": raw_credential_id_digest,
        "mechanism_id": mechanism_id,
        "enrollment_nonce_id": enrollment_nonce_id,
        "registrar_provenance_ref": registrar_provenance_ref,
        "credential_generation_before": credential_generation_before,
        "credential_generation_after": credential_generation_after,
        "enrolled_at": enrolled_at,
    }
    projected = dict(document)
    projected["record_digest"] = ""
    document["record_digest"] = canonical_digest(projected)
    rel = Path("credentials") / credential_id / "enrollment-evidence.json"
    path = authority.root / rel
    from pcae.core.hpac_foundation import reject_symlink

    reject_symlink(path)
    if not path.exists():
        write_atomic_create_only(path, canonical_json_bytes(document))
    return rel.as_posix()


# ─────────────────────────────────────────────────────────────────────────
# Revocation (RHAMP-REQ-116 — PAWA-authorized)
# ─────────────────────────────────────────────────────────────────────────


def revoke_credential(
    *,
    credential_id: str,
    protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> CredentialRecord:
    """RHAMP-REQ-116 — a PAWA-authorized revocation. The registry
    ``CredentialRecord.status`` moves to ``revoked``; future
    :func:`resolve_active_credentials` excludes it (RHAMP-REQ-054). The
    sidecar / counter-state files are immutable and remain as historical
    audit evidence — the registry is authoritative for status
    (RHAMP-REQ-056)."""

    try:
        handle = production_writer(
            PawaOperation.REVOKE_CREDENTIAL,
            credential_id=credential_id,
            _protected_root=protected_root,
            _configured_agent_identity_source=_configured_agent_identity_source,
            _topology_probe=_topology_probe,
        )
        capability = handle.consume(PawaOperation.REVOKE_CREDENTIAL, credential_id=credential_id)
    except PawaError as exc:
        raise _pawa_reason(exc) from exc
    registry = HumanPrincipalRegistryStore(handle.authority)
    return registry.revoke_credential(capability, credential_id=credential_id, revoked_at=_now())


# ─────────────────────────────────────────────────────────────────────────
# Canonical active-credential resolution (RHAMP-REQ-053/054, §31)
# ─────────────────────────────────────────────────────────────────────────


def resolve_active_credentials(
    registry: HumanPrincipalRegistryStore, principal_id: str
) -> tuple[ActiveCredentialMaterial, ...]:
    """§31 — the canonical read-only resolution used by authentication.
    ``principal_id`` → its current ACTIVE canonical credential set → the
    trusted allowList material. No caller-injected allowList
    (RHAMP-REQ-031). A credential is ACTIVE only if the registry record is
    ``active`` **and** its sidecar + counter-state resolve canonically and
    cross-check (RHAMP-REQ-025 — no partial state is ACTIVE)."""

    principal = registry.resolve_principal(principal_id)
    if principal is None or principal.status != "active":
        return ()
    sidecar_store = HpacRhampCredentialSidecarStore(registry.authority)
    counter_store = HpacRhampCounterStateStore(registry.authority)
    out: list[ActiveCredentialMaterial] = []
    for credential in registry.list_credentials():
        if credential.principal_id != principal_id or credential.status != "active":
            continue
        if credential.mechanism_id != MECHANISM_ID:
            continue
        try:
            sidecar = sidecar_store.resolve_against_registry(credential.credential_id, registry)
            counter_store.resolve_canonical(credential.credential_id)  # must exist + verify
        except Exception:  # noqa: BLE001 — a non-resolving artifact => not ACTIVE
            continue
        out.append(
            ActiveCredentialMaterial(
                credential_id=credential.credential_id,
                principal_id=principal_id,
                raw_credential_id=_decode(sidecar.raw_credential_id),
                cose_public_key=sidecar.cose_public_key,
                transports=sidecar.transports,
            )
        )
    return tuple(sorted(out, key=lambda m: m.credential_id))


def resolve_authentication_allowlist(
    registry: HumanPrincipalRegistryStore, principal_id: str
) -> tuple[bytes, ...]:
    """The raw CTAP2 credential ids of every ACTIVE canonical credential of
    ``principal_id`` — the ``allow_list`` for ``getAssertion`` (§9/§33)."""

    return tuple(m.raw_credential_id for m in resolve_active_credentials(registry, principal_id))
