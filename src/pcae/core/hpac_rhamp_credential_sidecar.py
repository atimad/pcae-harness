"""RHAMP-001 v1.0 §17 — the protected per-credential ``RHAMP-FIDO2-CREDENTIAL/1.0``
sidecar store.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle). The registry ``CredentialRecord`` (HPAC-REQ-013) is **byte-unchanged**
(RHAMP-REQ-055) — no FIDO2-specific field is added to it. The raw CTAP2
credential id, the bound ``rp_id``, the transport set, the advisory AAGUID,
and a duplicate of the COSE public key live in this **new** protected
per-credential artifact instead (RHAMP-REQ-056):

    <HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json

The sidecar is **immutable, create-only, atomically written, read-back
verified** (RHAMP-REQ-057), and resolved only by ``(credential_id,
record_digest)``. It stores **no private key, PIN, or biometric material**
(RHAMP-REQ-059/060) — there is no field for any of them.

``allowList`` construction and assertion verification read the sidecar for
``raw_credential_id`` and ``cose_public_key``; both SHALL be cross-checked
against the registry ``CredentialRecord`` (``public_key`` equality) before
use (RHAMP-REQ-058).
"""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    read_canonical_json_document,
    reject_symlink,
    require_nonempty_str,
    require_safe_relative_id_component,
    require_timestamp,
    write_atomic_create_only,
)
from pcae.core.hpac_rhamp_client_context import MECHANISM_ID, RP_ID

__all__ = [
    "RHAMP_SCHEMA_VERSION",
    "FIDO2_CREDENTIAL_SCHEMA",
    "SIDECAR_WRITER_ROLES",
    "RhampCredentialSidecarError",
    "Fido2CredentialSidecar",
    "HpacRhampCredentialSidecarStore",
    "encode_raw_credential_id",
    "decode_raw_credential_id",
]

#: RHAMP-REQ-005.
RHAMP_SCHEMA_VERSION = "RHAMP-001/1.0"
#: RHAMP-REQ-056.
FIDO2_CREDENTIAL_SCHEMA = "RHAMP-FIDO2-CREDENTIAL/1.0"

#: The sidecar is created by the one bounded ``enroll_credential`` PAWA
#: transaction (HPAC-PAWA-REQ-095 — one capability, role
#: ``human_principal_registry_admin``, for the CredentialRecord + sidecar +
#: counter-state). It is never updated (create-only, RHAMP-REQ-057).
SIDECAR_WRITER_ROLES = frozenset({"human_principal_registry_admin"})

_ALLOWED_TRANSPORTS = ("usb", "nfc")
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_HEX_RE = re.compile(r"^[0-9a-f]+$")

_SIDECAR_FIELDS = frozenset(
    {
        "rhamp_schema_version",
        "artifact_schema_version",
        "record_digest",
        "credential_id",
        "principal_id",
        "rp_id",
        "raw_credential_id",
        "cose_public_key",
        "transports",
        "aaguid",
        "mechanism_id",
        "created_at",
        "writer_provenance_ref",
        "status",
    }
)


class RhampCredentialSidecarError(HPACMalformedError):
    """A ``RHAMP-FIDO2-CREDENTIAL/1.0`` sidecar fails closed schema /
    canonical-byte / digest / provenance / registry-cross-check validation
    (RHAMP-REQ-057)."""


def encode_raw_credential_id(raw: bytes) -> str:
    """RHAMP-REQ-056 — base64url (no padding) of the CTAP2 credential-id bytes."""

    if not isinstance(raw, (bytes, bytearray)) or len(raw) == 0:
        raise RhampCredentialSidecarError("raw_credential_id must be non-empty bytes")
    return base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode("ascii")


def decode_raw_credential_id(value: str) -> bytes:
    text = require_nonempty_str(value, context="raw_credential_id")
    if not _B64URL_RE.fullmatch(text):
        raise RhampCredentialSidecarError("raw_credential_id is not base64url")
    padding = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + padding)
    except ValueError as exc:  # binascii.Error is a ValueError subclass
        raise RhampCredentialSidecarError(f"raw_credential_id base64url decode failed: {exc}") from exc


@dataclass(frozen=True)
class Fido2CredentialSidecar:
    """The closed ``RHAMP-FIDO2-CREDENTIAL/1.0`` object (RHAMP-REQ-056)."""

    credential_id: str
    principal_id: str
    raw_credential_id: str
    cose_public_key: str
    transports: tuple[str, ...]
    aaguid: Optional[str]
    created_at: str
    writer_provenance_ref: str
    status: str

    def to_document(self, *, include_digest: bool) -> dict:
        document = {
            "rhamp_schema_version": RHAMP_SCHEMA_VERSION,
            "artifact_schema_version": FIDO2_CREDENTIAL_SCHEMA,
            "credential_id": self.credential_id,
            "principal_id": self.principal_id,
            "rp_id": RP_ID,
            "raw_credential_id": self.raw_credential_id,
            "cose_public_key": self.cose_public_key,
            "transports": list(self.transports),
            "aaguid": self.aaguid,
            "mechanism_id": MECHANISM_ID,
            "created_at": self.created_at,
            "writer_provenance_ref": self.writer_provenance_ref,
            "status": self.status,
        }
        if include_digest:
            document["record_digest"] = _self_excluding_digest(document)
        return document

    @property
    def record_digest(self) -> str:
        return _self_excluding_digest(self.to_document(include_digest=False))


def _self_excluding_digest(document: dict) -> str:
    projected = dict(document)
    projected["record_digest"] = ""
    return canonical_digest(projected)


def _require_transports(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RhampCredentialSidecarError("transports must be a non-empty ordered list")
    seen: set[str] = set()
    ordered: list[str] = []
    for item in value:
        if item not in _ALLOWED_TRANSPORTS:
            raise RhampCredentialSidecarError(
                f"transport {item!r} is outside the RHAMP-001 v1.0 profile {_ALLOWED_TRANSPORTS} (RHAMP-REQ-132/133)"
            )
        if item in seen:
            raise RhampCredentialSidecarError(f"duplicate transport: {item!r}")
        seen.add(item)
        ordered.append(item)
    # RHAMP-REQ-056: "ordered subset of ['usb', 'nfc']" — canonical order.
    return tuple(sorted(ordered, key=_ALLOWED_TRANSPORTS.index))


def _require_aaguid(value: object) -> Optional[str]:
    if value is None:
        return None
    text = require_nonempty_str(value, context="aaguid")
    if not _HEX_RE.fullmatch(text) or len(text) % 2 != 0:
        raise RhampCredentialSidecarError("aaguid must be null or an even-length lowercase hex string")
    return text


def _require_cose_public_key(value: object) -> str:
    text = require_nonempty_str(value, context="cose_public_key")
    if not _HEX_RE.fullmatch(text) or len(text) % 2 != 0:
        raise RhampCredentialSidecarError("cose_public_key must be an even-length lowercase hex string")
    return text


def _parse_sidecar_document(document: object) -> Fido2CredentialSidecar:
    if not isinstance(document, dict):
        raise RhampCredentialSidecarError("sidecar record is not an object")
    if set(document) != _SIDECAR_FIELDS:
        raise RhampCredentialSidecarError(
            f"sidecar closed-field-set violation: {sorted(set(document) ^ _SIDECAR_FIELDS)}"
        )
    if document["rhamp_schema_version"] != RHAMP_SCHEMA_VERSION:
        raise RhampCredentialSidecarError("rhamp_schema_version is not the frozen const (RHAMP-REQ-006 fail closed)")
    if document["artifact_schema_version"] != FIDO2_CREDENTIAL_SCHEMA:
        raise RhampCredentialSidecarError("artifact_schema_version is not the frozen const")
    if document["rp_id"] != RP_ID:
        raise RhampCredentialSidecarError("rp_id is not the frozen const hpac.pcae.local (RHAMP-REQ-021)")
    if document["mechanism_id"] != MECHANISM_ID:
        raise RhampCredentialSidecarError("mechanism_id is not the frozen const")
    stored_digest = require_nonempty_str(document["record_digest"], context="record_digest")
    if _self_excluding_digest(document) != stored_digest:
        raise RhampCredentialSidecarError("record_digest does not recompute over the canonical bytes")
    credential_id = require_nonempty_str(document["credential_id"], context="credential_id")
    principal_id = require_nonempty_str(document["principal_id"], context="principal_id")
    raw_credential_id = document["raw_credential_id"]
    decode_raw_credential_id(raw_credential_id)  # grammar check
    cose_public_key = _require_cose_public_key(document["cose_public_key"])
    transports = _require_transports(document["transports"])
    aaguid = _require_aaguid(document["aaguid"])
    created_at = require_timestamp(document["created_at"], context="sidecar.created_at")
    provenance_ref = require_nonempty_str(document["writer_provenance_ref"], context="writer_provenance_ref")
    status = document["status"]
    if status not in ("active", "revoked"):
        raise RhampCredentialSidecarError(f"sidecar status is invalid: {status!r}")
    return Fido2CredentialSidecar(
        credential_id=credential_id,
        principal_id=principal_id,
        raw_credential_id=raw_credential_id,
        cose_public_key=cose_public_key,
        transports=transports,
        aaguid=aaguid,
        created_at=created_at,
        writer_provenance_ref=provenance_ref,
        status=status,
    )


class HpacRhampCredentialSidecarStore:
    """``<root>/credentials/<credential_id>/fido2-credential.json``.

    Create-only, atomic, canonical-lookup-only by ``credential_id``. Mirrors
    the :class:`HumanAuthenticationProofStore` discipline.
    """

    _WRITER_ROLE = "human_principal_registry_admin"

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "HpacRhampCredentialSidecarStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def _path(self, credential_id: str) -> Path:
        component = require_safe_relative_id_component(credential_id, context="credential_id")
        return self._root / "credentials" / component / "fido2-credential.json"

    def path(self, credential_id: str) -> Path:
        return self._path(credential_id)

    def create_canonical(
        self,
        writer: HPACWriterCapability,
        sidecar: Fido2CredentialSidecar,
        *,
        transaction_subject: str,
    ) -> Fido2CredentialSidecar:
        """RHAMP-REQ-057 — atomic create-only write + writer provenance +
        read-back verification. ``transaction_subject`` is the enrollment
        transaction id the PAWA ``enroll_credential`` capability is bound to
        (HPAC-PAWA-REQ-100)."""

        reject_symlink(self._root)
        try:
            self._authority.require_writer(writer, self._WRITER_ROLE, subject=transaction_subject)
        except HPACAuthorityError as exc:
            raise RhampCredentialSidecarError(str(exc)) from exc
        path = self._path(sidecar.credential_id)
        relative = path.relative_to(self._root).as_posix()
        key = hashlib.sha256(relative.encode("utf-8")).hexdigest()
        sidecar = replace(sidecar, writer_provenance_ref=f"provenance/{key}.json")
        # Validate before write.
        document = sidecar.to_document(include_digest=True)
        _parse_sidecar_document(document)
        write_atomic_create_only(path, canonical_json_bytes(document))
        self._authority.record_write(
            path,
            document["record_digest"],
            writer,
            role=self._WRITER_ROLE,
            subject=transaction_subject,
        )
        readback = read_canonical_json_document(path)
        if readback != document:
            raise RhampCredentialSidecarError("sidecar read-back verification failed after write")
        return _parse_sidecar_document(readback)

    def resolve(self, credential_id: str) -> Optional[Fido2CredentialSidecar]:
        """Validated sidecar data without conferring canonical authority."""

        reject_symlink(self._root)
        path = self._path(credential_id)
        reject_symlink(path)
        if not path.exists():
            return None
        return _parse_sidecar_document(read_canonical_json_document(path))

    def resolve_canonical(
        self, credential_id: str
    ) -> Optional[HPACResolvedRecord[Fido2CredentialSidecar]]:
        sidecar = self.resolve(credential_id)
        if sidecar is None:
            return None
        try:
            return self._authority.resolve_record(
                record=sidecar,
                record_path=self._path(credential_id),
                record_digest=sidecar.record_digest,
                roles=SIDECAR_WRITER_ROLES,
            )
        except HPACAuthorityError as exc:
            raise RhampCredentialSidecarError(str(exc)) from exc

    def resolve_against_registry(self, credential_id: str, registry) -> Fido2CredentialSidecar:
        """RHAMP-REQ-057/058 — resolve the sidecar canonically and
        cross-check ``credential_id`` / ``principal_id`` / ``mechanism_id`` /
        ``cose_public_key`` against the registry ``CredentialRecord``. The
        registry is authoritative for ``status``. Fails closed on any
        disagreement (``protected_root_invalid`` territory)."""

        resolved = self.resolve_canonical(credential_id)
        if resolved is None:
            raise RhampCredentialSidecarError(f"no sidecar for credential_id: {credential_id}")
        sidecar = resolved.record
        credential = registry.resolve_credential(credential_id)
        if credential is None:
            raise RhampCredentialSidecarError("sidecar credential_id is absent from the registry")
        if sidecar.principal_id != credential.principal_id:
            raise RhampCredentialSidecarError("sidecar principal_id disagrees with the registry")
        if credential.mechanism_id != MECHANISM_ID:
            raise RhampCredentialSidecarError("registry credential mechanism_id is not the real RHAMP mechanism")
        if sidecar.cose_public_key != credential.public_key:
            raise RhampCredentialSidecarError("sidecar cose_public_key disagrees with the registry public_key")
        if resolved.authority_class is not registry.authority.authority_class:
            raise RhampCredentialSidecarError("sidecar / registry assurance-class mismatch")
        return sidecar
