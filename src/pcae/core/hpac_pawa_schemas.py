"""HPAC-PAWA-001 v1.1 — closed schema helpers for the production
protected-admin writer anchor (`docs/contracts/HPAC_PRODUCTION_PROTECTED_
ADMIN_WRITER_ANCHOR_CONTRACT.md`).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (Slice 1). This module holds
only the *pure* closed-schema / canonical-digest / grammar helpers for the
three PAWA records this slice touches:

- ``HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0``  — §13/§14 (13 closed fields;
  **schema byte-unchanged** in v1.1 — no account identity is added here);
- ``HPAC-PAWA-CURRENT-GENERATION/1.0``    — §20 / §20A (v1.1 **7** closed
  fields — adds ``agent_exclusion_digest``; the schema id is deliberately
  **not** bumped to ``/1.1``: the record is an internal, installation-local
  monotonic anchor whose required shape is governed by the contract
  version, HPAC-PAWA-REQ-169);
- ``HPAC-PAWA-ISSUANCE-EVIDENCE/1.0``     — §55 (audit projection only; it
  is never authority, PAWA-INV-10).

It reads no OS account database, resolves no protected root, mints no
writer capability, and imports nothing agent-reachable. The recognition
sequence, the writer factory, the failure taxonomy, and the ``.authority/``
namespace I/O all live in ``hpac_protected_admin_writer.py`` (inside the
non-agent-importable consumer-inventory fence, HPAC-PAWA-REQ-208).

Every fault fails closed (§0): a :class:`PawaSchemaError` is raised and the
caller maps it onto the closed 21-value ``pawa_failure_code`` vocabulary
(§56 / §42A — this module never invents a reason string).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    canonical_digest,
    canonical_json_bytes,
)

__all__ = [
    "PawaSchemaError",
    "AUTHORITY_DESCRIPTOR_SCHEMA",
    "CURRENT_GENERATION_SCHEMA",
    "ISSUANCE_EVIDENCE_SCHEMA",
    "AGENT_EXCLUSION_SCHEMA",
    "DEPLOYMENT_OWNER_ROLE_VOCAB",
    "ANCHOR_STATE_VOCAB",
    "AUTHORITY_NAMESPACE",
    "PawaAuthorityDescriptor",
    "PawaCurrentGeneration",
    "new_anchor_id",
    "new_installation_id",
    "new_operation_id",
    "self_excluding_digest",
    "require_hex64",
    "require_anchor_id",
    "require_installation_id",
    "require_generation",
    "require_pawa_timestamp",
    "require_root_identity",
    "validate_authority_descriptor",
    "validate_current_generation",
    "build_authority_descriptor_document",
    "build_current_generation_document",
    "build_issuance_evidence_document",
    "ISSUANCE_EVIDENCE_FIELDS",
]


AUTHORITY_DESCRIPTOR_SCHEMA = "HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0"
CURRENT_GENERATION_SCHEMA = "HPAC-PAWA-CURRENT-GENERATION/1.0"
ISSUANCE_EVIDENCE_SCHEMA = "HPAC-PAWA-ISSUANCE-EVIDENCE/1.0"
#: Frozen in ``hpac_pawa_agent_exclusion`` — re-exported here so a single
#: import site carries every PAWA schema id.
AGENT_EXCLUSION_SCHEMA = "HPAC-PAWA-AGENT-EXCLUSION/1.0"

AUTHORITY_NAMESPACE = ".authority"

#: §14 HPAC-PAWA-REQ-036 — one member, no ``all`` / ``root`` / wildcard.
DEPLOYMENT_OWNER_ROLE_VOCAB = frozenset({"HPAC_PROTECTED_ADMIN"})
#: §51 HPAC-PAWA-REQ-111.
ANCHOR_STATE_VOCAB = frozenset({"ACTIVE", "REVOKED", "SUPERSEDED"})

_ANCHOR_ID_RE = re.compile(r"^hpaw-[0-9a-f]{32}$")
_INSTALLATION_ID_RE = re.compile(r"^hpawi-[0-9a-f]{32}$")
_OPERATION_ID_RE = re.compile(r"^hpawop-[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_ROLE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
#: HPAC-001 v2.1 ``_TIMESTAMP_RE`` profile (RFC3339 UTC, ``Z`` suffix).
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")

_DESCRIPTOR_FIELDS = frozenset(
    {
        "artifact_schema_version",
        "descriptor_digest",
        "anchor_id",
        "installation_id",
        "protected_root_identity",
        "authority_namespace",
        "deployment_owner_role",
        "configured_agent_exclusion_binding",
        "generation",
        "created_at",
        "supersedes",
        "provenance_ref",
        "state",
    }
)
_EXCLUSION_BINDING = {
    "excluded_principal_kind": "PCAE_CONFIGURED_AGENT_PRINCIPAL",
    "exclusion_basis": "OS_FILESYSTEM_WRITE_AUTHORITY",
}
#: v1.1 — closed **7**-field set (§20A HPAC-PAWA-REQ-168).
_CURRENT_GENERATION_FIELDS = frozenset(
    {
        "artifact_schema_version",
        "record_digest",
        "installation_id",
        "current_generation",
        "descriptor_digest",
        "agent_exclusion_digest",
        "updated_at",
    }
)
#: §55 HPAC-PAWA-REQ-118 — the closed issuance-evidence field set (audit
#: projection only; never authority — the ``_authority_seal`` is never here).
ISSUANCE_EVIDENCE_FIELDS = (
    "event_schema_version",
    "operation_id",
    "operation",
    "anchor_id",
    "installation_id",
    "descriptor_generation",
    "protected_root_identity",
    "target_principal_id",
    "target_credential_id",
    "enrollment_transaction_id",
    "issued_at",
    "issuer",
    "result",
    "capability_identifier",
    "context_annotation",
)


class PawaSchemaError(HPACMalformedError):
    """A PAWA closed-schema / canonical-byte / digest / grammar failure.

    Fails closed (§0). The recognition sequence maps this onto exactly one
    closed ``pawa_failure_code`` (§56 / §42A) — no new reason string, no
    contract-vocabulary expansion.
    """


# ─────────────────────────────────────────────────────────────────────────
# ID minters (out-of-band provisioning only)
# ─────────────────────────────────────────────────────────────────────────


def new_anchor_id() -> str:
    return f"hpaw-{uuid.uuid4().hex}"


def new_installation_id() -> str:
    return f"hpawi-{uuid.uuid4().hex}"


def new_operation_id() -> str:
    return f"hpawop-{uuid.uuid4().hex}"


# ─────────────────────────────────────────────────────────────────────────
# Canonical digest
# ─────────────────────────────────────────────────────────────────────────


def self_excluding_digest(document: dict, *, digest_field: str) -> str:
    """SHA-256 over the canonical bytes of ``document`` with
    ``digest_field`` set to the empty string (§14 / §20A / §32A.1).

    Uses the exact HPAC-REQ-089 canonicalisation (NFC, ``sort_keys``,
    ``(",",":")``, UTF-8) already frozen by ``canonical_json_bytes`` /
    ``canonical_digest``.
    """

    if digest_field not in document:
        raise PawaSchemaError(f"digest field {digest_field!r} absent from record")
    projected = dict(document)
    projected[digest_field] = ""
    return canonical_digest(projected)


# ─────────────────────────────────────────────────────────────────────────
# Grammar primitives (shared by every PAWA record validator)
# ─────────────────────────────────────────────────────────────────────────


def require_hex64(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _HEX64_RE.fullmatch(value):
        raise PawaSchemaError(f"{context}: expected 64 lowercase hex characters")
    return value


def require_anchor_id(value: object, *, context: str = "anchor_id") -> str:
    if not isinstance(value, str) or not _ANCHOR_ID_RE.fullmatch(value):
        raise PawaSchemaError(f"{context}: expected an opaque hpaw-<hex32> identifier")
    return value


def require_installation_id(value: object, *, context: str = "installation_id") -> str:
    if not isinstance(value, str) or not _INSTALLATION_ID_RE.fullmatch(value):
        raise PawaSchemaError(f"{context}: expected an opaque hpawi-<hex32> identifier")
    return value


def require_operation_id(value: object, *, context: str = "operation_id") -> str:
    if not isinstance(value, str) or not _OPERATION_ID_RE.fullmatch(value):
        raise PawaSchemaError(f"{context}: expected an opaque hpawop-<hex32> identifier")
    return value


def require_generation(value: object, *, context: str = "generation") -> int:
    # bool is an int subclass — reject it explicitly.
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise PawaSchemaError(f"{context}: expected an integer >= 1")
    return value


def require_pawa_timestamp(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise PawaSchemaError(f"{context}: expected an RFC3339 UTC timestamp")
    return value


def require_root_identity(value: object, *, context: str = "protected_root_identity") -> dict:
    if (
        not isinstance(value, dict)
        or set(value) != {"device", "inode"}
        or not isinstance(value["device"], int)
        or isinstance(value["device"], bool)
        or not isinstance(value["inode"], int)
        or isinstance(value["inode"], bool)
    ):
        raise PawaSchemaError(f"{context}: expected a closed {{device, inode}} integer object")
    return value


def require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise PawaSchemaError(f"{context}: expected a non-empty, non-whitespace-padded string")
    return value


# ─────────────────────────────────────────────────────────────────────────
# Typed views
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PawaAuthorityDescriptor:
    document: dict
    anchor_id: str
    installation_id: str
    protected_root_identity: dict
    deployment_owner_role: str
    generation: int
    descriptor_digest: str
    provenance_ref: str
    state: str
    supersedes: Optional[dict]


@dataclass(frozen=True)
class PawaCurrentGeneration:
    document: dict
    installation_id: str
    current_generation: int
    descriptor_digest: str
    agent_exclusion_digest: str
    record_digest: str


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0 (§14) — schema byte-unchanged in v1.1
# ─────────────────────────────────────────────────────────────────────────


def _validate_supersedes(value: object, generation: int, *, digest_key: str) -> Optional[dict]:
    if generation == 1:
        if value is not None:
            raise PawaSchemaError("supersedes: must be null for generation 1")
        return None
    if not isinstance(value, dict) or set(value) != {"previous_generation", digest_key}:
        raise PawaSchemaError(
            f"supersedes: expected a closed {{previous_generation, {digest_key}}} object for generation > 1"
        )
    previous = value["previous_generation"]
    if not isinstance(previous, int) or isinstance(previous, bool) or previous < 1 or previous >= generation:
        raise PawaSchemaError("supersedes.previous_generation: must be an integer in [1, generation)")
    require_hex64(value[digest_key], context=f"supersedes.{digest_key}")
    return value


def validate_authority_descriptor(document: object) -> PawaAuthorityDescriptor:
    """§14 / §38 — exact closed field set, ``artifact_schema_version``
    const, recomputed ``descriptor_digest`` equality, grammar, the closed
    ``configured_agent_exclusion_binding`` shape (v1.1: still records only
    *kind* + *basis*, HPAC-PAWA-REQ-174), ``supersedes`` monotonicity.

    Root-identity / provenance / current-generation cross-checks are the
    recognition sequence's job (they need live OS state) — this validator
    is pure.
    """

    if not isinstance(document, dict):
        raise PawaSchemaError("authority descriptor is not an object")
    if set(document) != _DESCRIPTOR_FIELDS:
        raise PawaSchemaError(
            f"authority descriptor closed-field-set violation: {sorted(set(document) ^ _DESCRIPTOR_FIELDS)}"
        )
    if document["artifact_schema_version"] != AUTHORITY_DESCRIPTOR_SCHEMA:
        raise PawaSchemaError("authority descriptor artifact_schema_version is not the frozen const")
    digest = require_hex64(document["descriptor_digest"], context="descriptor_digest")
    if self_excluding_digest(document, digest_field="descriptor_digest") != digest:
        raise PawaSchemaError("authority descriptor descriptor_digest does not recompute")
    anchor_id = require_anchor_id(document["anchor_id"])
    installation_id = require_installation_id(document["installation_id"])
    root_identity = require_root_identity(document["protected_root_identity"])
    if document["authority_namespace"] != AUTHORITY_NAMESPACE:
        raise PawaSchemaError("authority descriptor authority_namespace is not the frozen const")
    role = document["deployment_owner_role"]
    if role not in DEPLOYMENT_OWNER_ROLE_VOCAB or not _ROLE_RE.fullmatch(role):
        raise PawaSchemaError("authority descriptor deployment_owner_role is outside the closed vocabulary")
    if document["configured_agent_exclusion_binding"] != _EXCLUSION_BINDING:
        raise PawaSchemaError("authority descriptor configured_agent_exclusion_binding is not the frozen closed object")
    generation = require_generation(document["generation"])
    require_pawa_timestamp(document["created_at"], context="descriptor.created_at")
    supersedes = _validate_supersedes(
        document["supersedes"], generation, digest_key="previous_descriptor_digest"
    )
    provenance_ref = require_nonempty_str(document["provenance_ref"], context="descriptor.provenance_ref")
    state = document["state"]
    if state not in ANCHOR_STATE_VOCAB:
        raise PawaSchemaError("authority descriptor state is outside the closed vocabulary")
    return PawaAuthorityDescriptor(
        document=document,
        anchor_id=anchor_id,
        installation_id=installation_id,
        protected_root_identity=root_identity,
        deployment_owner_role=role,
        generation=generation,
        descriptor_digest=digest,
        provenance_ref=provenance_ref,
        state=state,
        supersedes=supersedes,
    )


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PAWA-CURRENT-GENERATION/1.0 (§20 / §20A) — v1.1 closed 7-field set
# ─────────────────────────────────────────────────────────────────────────


def validate_current_generation(document: object) -> PawaCurrentGeneration:
    """§20A HPAC-PAWA-REQ-168/169 — the v1.1 closed **7**-field set. A
    record missing ``agent_exclusion_digest`` is a v1.0-era anchor and
    SHALL fail closed (never a silent downgrade to a digest-unbound
    check).
    """

    if not isinstance(document, dict):
        raise PawaSchemaError("current-generation record is not an object")
    if set(document) != _CURRENT_GENERATION_FIELDS:
        missing = _CURRENT_GENERATION_FIELDS - set(document)
        if missing == {"agent_exclusion_digest"}:
            raise PawaSchemaError(
                "current-generation record is a v1.0-era anchor missing agent_exclusion_digest; "
                "HPAC-PAWA-001 v1.1 recognition fails closed (HPAC-PAWA-REQ-169)"
            )
        raise PawaSchemaError(
            f"current-generation record closed-field-set violation: "
            f"{sorted(set(document) ^ _CURRENT_GENERATION_FIELDS)}"
        )
    if document["artifact_schema_version"] != CURRENT_GENERATION_SCHEMA:
        raise PawaSchemaError("current-generation record artifact_schema_version is not the frozen const")
    record_digest = require_hex64(document["record_digest"], context="current_generation.record_digest")
    if self_excluding_digest(document, digest_field="record_digest") != record_digest:
        raise PawaSchemaError("current-generation record record_digest does not recompute")
    installation_id = require_installation_id(document["installation_id"])
    current_generation = require_generation(document["current_generation"], context="current_generation")
    descriptor_digest = require_hex64(document["descriptor_digest"], context="current_generation.descriptor_digest")
    agent_exclusion_digest = require_hex64(
        document["agent_exclusion_digest"], context="current_generation.agent_exclusion_digest"
    )
    require_pawa_timestamp(document["updated_at"], context="current_generation.updated_at")
    return PawaCurrentGeneration(
        document=document,
        installation_id=installation_id,
        current_generation=current_generation,
        descriptor_digest=descriptor_digest,
        agent_exclusion_digest=agent_exclusion_digest,
        record_digest=record_digest,
    )


# ─────────────────────────────────────────────────────────────────────────
# Document builders (out-of-band provisioning / rotation only)
# ─────────────────────────────────────────────────────────────────────────


def build_authority_descriptor_document(
    *,
    anchor_id: str,
    installation_id: str,
    protected_root_identity: dict,
    generation: int,
    created_at: str,
    provenance_ref: str,
    supersedes: Optional[dict],
    state: str = "ACTIVE",
) -> dict:
    document = {
        "artifact_schema_version": AUTHORITY_DESCRIPTOR_SCHEMA,
        "descriptor_digest": "",
        "anchor_id": require_anchor_id(anchor_id),
        "installation_id": require_installation_id(installation_id),
        "protected_root_identity": require_root_identity(protected_root_identity),
        "authority_namespace": AUTHORITY_NAMESPACE,
        "deployment_owner_role": "HPAC_PROTECTED_ADMIN",
        "configured_agent_exclusion_binding": dict(_EXCLUSION_BINDING),
        "generation": require_generation(generation),
        "created_at": require_pawa_timestamp(created_at, context="created_at"),
        "supersedes": _validate_supersedes(supersedes, generation, digest_key="previous_descriptor_digest"),
        "provenance_ref": require_nonempty_str(provenance_ref, context="provenance_ref"),
        "state": state if state in ANCHOR_STATE_VOCAB else _raise_state(state),
    }
    document["descriptor_digest"] = self_excluding_digest(document, digest_field="descriptor_digest")
    return document


def build_current_generation_document(
    *,
    installation_id: str,
    current_generation: int,
    descriptor_digest: str,
    agent_exclusion_digest: str,
    updated_at: str,
) -> dict:
    document = {
        "artifact_schema_version": CURRENT_GENERATION_SCHEMA,
        "record_digest": "",
        "installation_id": require_installation_id(installation_id),
        "current_generation": require_generation(current_generation, context="current_generation"),
        "descriptor_digest": require_hex64(descriptor_digest, context="descriptor_digest"),
        "agent_exclusion_digest": require_hex64(agent_exclusion_digest, context="agent_exclusion_digest"),
        "updated_at": require_pawa_timestamp(updated_at, context="updated_at"),
    }
    document["record_digest"] = self_excluding_digest(document, digest_field="record_digest")
    return document


def build_issuance_evidence_document(
    *,
    operation_id: str,
    operation: str,
    anchor_id: str,
    installation_id: str,
    descriptor_generation: int,
    protected_root_identity: dict,
    target_principal_id: Optional[str],
    target_credential_id: Optional[str],
    enrollment_transaction_id: Optional[str],
    issued_at: str,
    issuer: str,
    result: str,
    capability_identifier: Optional[str],
    context_annotation: Optional[str],
) -> dict:
    return {
        "event_schema_version": ISSUANCE_EVIDENCE_SCHEMA,
        "operation_id": require_operation_id(operation_id),
        "operation": require_nonempty_str(operation, context="operation"),
        "anchor_id": require_anchor_id(anchor_id),
        "installation_id": require_installation_id(installation_id),
        "descriptor_generation": require_generation(descriptor_generation, context="descriptor_generation"),
        "protected_root_identity": require_root_identity(protected_root_identity),
        "target_principal_id": target_principal_id,
        "target_credential_id": target_credential_id,
        "enrollment_transaction_id": enrollment_transaction_id,
        "issued_at": require_pawa_timestamp(issued_at, context="issued_at"),
        "issuer": require_nonempty_str(issuer, context="issuer"),
        "result": require_nonempty_str(result, context="result"),
        "capability_identifier": capability_identifier,
        "context_annotation": context_annotation,
    }


def _raise_state(state: object):
    raise PawaSchemaError(f"state {state!r} is outside the closed vocabulary")


def canonical_bytes(document: object) -> bytes:
    """Re-export of the frozen HPAC-REQ-089 canonicaliser for the admin
    writer / provisioning script's atomic writes."""

    return canonical_json_bytes(document)
