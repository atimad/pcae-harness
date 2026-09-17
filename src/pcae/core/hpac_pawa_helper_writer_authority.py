"""HPAC-PAWA-HELPER-001 v3.0 §30B — Model E: helper-process-isolated
mutation facades with distinct, sealed, non-``HPACWriterCapability``
authority families.

**Module-boundary discipline (HPAC-PAWA-HELPER-REQ-144/145, PAWAH-INV-19/21).**
This module is the exclusive owner of the mint primitive for three new
authority families. It is imported **only** by
``pcae.core.hpac_pawa_helper_operations``'s closed dispatch table. It never
imports, and must never be imported by, ``pcae.core.hpac_foundation``,
``pcae.core.hpac_protected_admin_writer`` (the legacy PAWA factory — REQ-033),
any CLI/runtime/plugin module, or the launcher. A structural import-graph test
(``tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py``) enforces this
mechanically, not by convention alone (threat-matrix row 31/40).

**Why this is not Model D.** Model D's defect was that its mint primitive
lived in the shared, agent-reachable ``hpac_foundation`` module, gated only
by a bare, readable module-level seal — any code with ``hpac_foundation``
already imported could ``getattr`` the seal and mint directly. This module's
seal (``_HELPER_AUTHORITY_SEAL`` below) is defined in a module that is *never
loaded* in any agent-reachable process at all (verified by the import-graph
test), so there is no shared address space from which to read it — the OS
process boundary itself is the gate, not a checkable attribute (REQ-145).

**Authority families are not ``HPACWriterCapability``.** Each of
``HelperAdminMutationAuthority``, ``HelperCertificationWriteAuthority``, and
``HelperPresentationEvidenceAuthority`` is a distinct sealed type with its own
``__slots__`` and no shared base with ``HPACWriterCapability`` — recognition
never uses ``isinstance`` against a shared ancestor (REQ-148/151, PAWAH-INV-20).

**No second trust root (REQ-147/169).** Each facade still terminates in the
same ``HPACStoreAuthority`` the legacy path uses — same OS filesystem root,
same ``_ensure_root``/``_validate_production_boundary`` re-validation on every
mutation, same canonical stores. What is new is only the *outer*,
caller-facing authority type these facades require and produce; internally, a
facade mints one ordinary, single-use ``HPACWriterCapability`` via
``HPACStoreAuthority._new_capability`` (the same, single, canonical
construction site the legacy factory itself uses — this repository already
treats that construction site, not the higher-level seal-gated
``_mint_production_writer_capability`` wrapper, as the actual single point of
``HPACWriterCapability`` issuance) purely to invoke the target canonical
store's existing, unmodified write method. That transient capability is
created and consumed entirely inside one facade call and is never returned,
logged, or exposed to any caller of this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
)
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_ADMIN_MUTATIONS,
    CLOSED_CERTIFICATION_ROLES,
    HelperProtocolError,
)

#: The sole seal gating construction of the three authority classes below.
#: Never exported; never passed outside this module. Because this module is
#: never imported on any agent-reachable code path (REQ-145), this seal is
#: never instantiated in, and therefore never readable from, the configured
#: agent principal's own interpreter.
_HELPER_AUTHORITY_SEAL = object()


class HelperWriterAuthorityError(Exception):
    """Terminal failure minting or recognizing a Model E helper authority.
    ``code`` is one of the existing 21 ``pawa_failure_code`` values
    (HPAC-PAWA-HELPER-REQ-163) — no new vocabulary is introduced."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


def _fail(code: str, detail: str) -> "HelperWriterAuthorityError":
    return HelperWriterAuthorityError(code, detail)


class _SealedNonSerializable:
    """Shared *implementation-reuse* mixin — never used for recognition.

    PAWAH-INV-20 forbids recognition via ``isinstance`` against a shared
    base; this mixin supplies only ``__reduce__``/no-``__dict__`` behaviour,
    never a recognizable type identity. Every recognition predicate in this
    module and in ``hpac_pawa_helper_store_adapter`` checks ``type(x) is
    ExactClass``, never ``isinstance(x, _SealedNonSerializable)``.
    """

    __slots__ = ()

    def __reduce__(self):  # pragma: no cover - defensive serialization guard
        raise TypeError(f"{type(self).__name__} is process-local and non-serializable")

    def __deepcopy__(self, memo):  # pragma: no cover - defensive guard
        raise TypeError(f"{type(self).__name__} cannot be copied")

    __copy__ = __deepcopy__


class HelperAdminMutationAuthority(_SealedNonSerializable):
    """§30B.4/§150/§157 — scoped to exactly one closed ``admin_mutation``
    subtype and its bound subject. Single-use; process-local; restart-dead."""

    __slots__ = (
        "mutation",
        "subject",
        "session_id",
        "request_id",
        "installation_id",
        "generation",
        "authority_class",
        "_spent",
    )

    def __init__(
        self,
        *,
        mutation: str,
        subject: Optional[str],
        session_id: str,
        request_id: str,
        installation_id: str,
        generation: int,
        authority_class: HPACAuthorityClass,
        _seal: object,
    ) -> None:
        if _seal is not _HELPER_AUTHORITY_SEAL:
            raise _fail("internal_fail_closed", "HelperAdminMutationAuthority cannot be caller-constructed")
        self.mutation = mutation
        self.subject = subject
        self.session_id = session_id
        self.request_id = request_id
        self.installation_id = installation_id
        self.generation = generation
        self.authority_class = authority_class
        self._spent = False


class HelperCertificationWriteAuthority(_SealedNonSerializable):
    """§30B.4/§150/§156 — scoped to exactly one closed five-role member and
    its bound subject (``proof_id`` for the four lifecycle roles,
    ``credential_id`` for the counter-verifier role)."""

    __slots__ = (
        "role",
        "subject",
        "session_id",
        "request_id",
        "installation_id",
        "generation",
        "authority_class",
        "_spent",
    )

    def __init__(
        self,
        *,
        role: str,
        subject: str,
        session_id: str,
        request_id: str,
        installation_id: str,
        generation: int,
        authority_class: HPACAuthorityClass,
        _seal: object,
    ) -> None:
        if _seal is not _HELPER_AUTHORITY_SEAL:
            raise _fail("internal_fail_closed", "HelperCertificationWriteAuthority cannot be caller-constructed")
        self.role = role
        self.subject = subject
        self.session_id = session_id
        self.request_id = request_id
        self.installation_id = installation_id
        self.generation = generation
        self.authority_class = authority_class
        self._spent = False


class HelperPresentationEvidenceAuthority(_SealedNonSerializable):
    """§30B.4/§150/§158 — scoped to exactly one ceremony
    ``(invocation_id, attempt_id)``; create-only downstream (unchanged from
    REQ-127)."""

    __slots__ = (
        "invocation_id",
        "attempt_id",
        "session_id",
        "request_id",
        "installation_id",
        "generation",
        "authority_class",
        "_spent",
    )

    def __init__(
        self,
        *,
        invocation_id: str,
        attempt_id: str,
        session_id: str,
        request_id: str,
        installation_id: str,
        generation: int,
        authority_class: HPACAuthorityClass,
        _seal: object,
    ) -> None:
        if _seal is not _HELPER_AUTHORITY_SEAL:
            raise _fail("internal_fail_closed", "HelperPresentationEvidenceAuthority cannot be caller-constructed")
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.session_id = session_id
        self.request_id = request_id
        self.installation_id = installation_id
        self.generation = generation
        self.authority_class = authority_class
        self._spent = False


def _spend(authority) -> None:
    if authority._spent:
        raise _fail("capability_stale", "helper authority already consumed")
    authority._spent = True


def _check_currentness(store_authority: HPACStoreAuthority, *, installation_id: str, generation: int) -> None:
    """§150 — installation/generation binding re-validated at recognition
    time, not merely at mint time."""

    from pcae.core.protected_presentation_installation import (
        ProtectedPresentationInstallationError,
        ProtectedPresentationIntegrityError,
        ProtectedPresentationInstallationStore,
    )

    try:
        resolved = ProtectedPresentationInstallationStore(store_authority).resolve_current_generation()
    except (ProtectedPresentationInstallationError, ProtectedPresentationIntegrityError) as exc:
        raise _fail("descriptor_missing", f"no current protected-presentation generation installed: {exc}")
    if resolved is None:
        raise _fail("descriptor_missing", "no current protected-presentation generation installed")
    if resolved.record.installation_id != installation_id:
        raise _fail("descriptor_installation_mismatch", "installation_id is not current")
    if resolved.anchor.current_generation != generation:
        raise _fail("descriptor_generation_stale", "generation is not current")


def _new_internal_capability(store_authority: HPACStoreAuthority, *, role: str, subject: Optional[str]):
    """The one place this module reaches into ``HPACStoreAuthority`` to
    obtain a transient, internal-use-only ``HPACWriterCapability`` so an
    existing canonical store's unmodified write method can be invoked. Never
    returned to any caller of this module's public facades (REQ-147/169: no
    second trust root — this is the same construction site, same root, same
    ``require_writer``/``record_write`` discipline the legacy path uses)."""

    if store_authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise _fail("internal_fail_closed", "helper facades require a PRODUCTION HPACStoreAuthority")
    return store_authority._new_capability(role, subject, single_use=True)


# ---------------------------------------------------------------------------
# §30B.5 — the three mint-and-perform facades.
# ---------------------------------------------------------------------------


def mint_and_perform_admin_mutation(
    store_authority: HPACStoreAuthority,
    *,
    mutation: str,
    subject: Optional[str],
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§153 — mints a :class:`HelperAdminMutationAuthority` scoped to exactly
    one closed ``admin_mutation`` subtype and performs that one bounded
    mutation in the same call."""

    if mutation not in CLOSED_ADMIN_MUTATIONS:
        raise _fail("operation_scope_invalid", f"unknown admin mutation {mutation!r}")
    if store_authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise _fail("internal_fail_closed", "NON_REAL authority cannot mint a REAL helper authority")

    authority = HelperAdminMutationAuthority(
        mutation=mutation,
        subject=subject,
        session_id=session_id,
        request_id=request_id,
        installation_id=installation_id,
        generation=generation,
        authority_class=HPACAuthorityClass.PRODUCTION,
        _seal=_HELPER_AUTHORITY_SEAL,
    )

    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    try:
        result = perform_recognized_admin_mutation(
            authority,
            store_authority,
            mutation=mutation,
            subject=subject,
            session_id=session_id,
            request_id=request_id,
            installation_id=installation_id,
            generation=generation,
            operation_params=operation_params,
        )
    except HelperWriterAuthorityError:
        raise
    finally:
        _spend(authority)
    return result


def mint_and_perform_certification_write(
    store_authority: HPACStoreAuthority,
    *,
    role: str,
    subject: str,
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§154 — mints a :class:`HelperCertificationWriteAuthority` scoped to
    exactly one closed five-role member and performs that one bounded
    role-specific write in the same call."""

    if role not in CLOSED_CERTIFICATION_ROLES:
        raise _fail("operation_scope_invalid", f"role {role!r} not in closed five-role set")
    if store_authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise _fail("internal_fail_closed", "NON_REAL authority cannot mint a REAL helper authority")

    authority = HelperCertificationWriteAuthority(
        role=role,
        subject=subject,
        session_id=session_id,
        request_id=request_id,
        installation_id=installation_id,
        generation=generation,
        authority_class=HPACAuthorityClass.PRODUCTION,
        _seal=_HELPER_AUTHORITY_SEAL,
    )

    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_certification_write

    try:
        result = perform_recognized_certification_write(
            authority,
            store_authority,
            role=role,
            subject=subject,
            session_id=session_id,
            request_id=request_id,
            installation_id=installation_id,
            generation=generation,
            operation_params=operation_params,
        )
    except HelperWriterAuthorityError:
        raise
    finally:
        _spend(authority)
    return result


def mint_and_perform_presentation_evidence_write(
    store_authority: HPACStoreAuthority,
    *,
    invocation_id: str,
    attempt_id: str,
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§155 — mints a :class:`HelperPresentationEvidenceAuthority` scoped to
    the exact ceremony ``(invocation_id, attempt_id)`` and performs the one
    create-only evidence write after one valid ``ceremony_approve_ref``."""

    if not invocation_id or not attempt_id:
        raise _fail("operation_scope_invalid", "presentation evidence write requires invocation_id and attempt_id")
    if store_authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise _fail("internal_fail_closed", "NON_REAL authority cannot mint a REAL helper authority")

    authority = HelperPresentationEvidenceAuthority(
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        session_id=session_id,
        request_id=request_id,
        installation_id=installation_id,
        generation=generation,
        authority_class=HPACAuthorityClass.PRODUCTION,
        _seal=_HELPER_AUTHORITY_SEAL,
    )

    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_presentation_evidence_write

    try:
        result = perform_recognized_presentation_evidence_write(
            authority,
            store_authority,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
            session_id=session_id,
            request_id=request_id,
            installation_id=installation_id,
            generation=generation,
            operation_params=operation_params,
        )
    except HelperWriterAuthorityError:
        raise
    finally:
        _spend(authority)
    return result


# ---------------------------------------------------------------------------
# NON_REAL / test-only construction (§164 — cannot ever satisfy REAL
# recognition; deterministic authority never carries authority_class
# PRODUCTION).
# ---------------------------------------------------------------------------


def fixture_non_real_admin_mutation_authority(
    *, mutation: str, subject: Optional[str], session_id: str, request_id: str,
    installation_id: str, generation: int,
) -> HelperAdminMutationAuthority:
    """Test-only. Never satisfies REAL recognition (§164) — the
    ``authority_class`` is always ``FIXTURE_NON_REAL``, and every recognition
    predicate in ``hpac_pawa_helper_store_adapter`` requires ``PRODUCTION``."""

    return HelperAdminMutationAuthority(
        mutation=mutation, subject=subject, session_id=session_id, request_id=request_id,
        installation_id=installation_id, generation=generation,
        authority_class=HPACAuthorityClass.FIXTURE_NON_REAL, _seal=_HELPER_AUTHORITY_SEAL,
    )


def fixture_non_real_certification_write_authority(
    *, role: str, subject: str, session_id: str, request_id: str,
    installation_id: str, generation: int,
) -> HelperCertificationWriteAuthority:
    return HelperCertificationWriteAuthority(
        role=role, subject=subject, session_id=session_id, request_id=request_id,
        installation_id=installation_id, generation=generation,
        authority_class=HPACAuthorityClass.FIXTURE_NON_REAL, _seal=_HELPER_AUTHORITY_SEAL,
    )


def fixture_non_real_presentation_evidence_authority(
    *, invocation_id: str, attempt_id: str, session_id: str, request_id: str,
    installation_id: str, generation: int,
) -> HelperPresentationEvidenceAuthority:
    return HelperPresentationEvidenceAuthority(
        invocation_id=invocation_id, attempt_id=attempt_id, session_id=session_id, request_id=request_id,
        installation_id=installation_id, generation=generation,
        authority_class=HPACAuthorityClass.FIXTURE_NON_REAL, _seal=_HELPER_AUTHORITY_SEAL,
    )
