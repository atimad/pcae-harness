"""
HPAC-001 v2.0 §17 — `HumanAuthenticationProof` canonical model/store.

Phase .3.2 separates proof data from canonical proof authority. ``create`` /
``resolve`` remain explicit structural fixture compatibility operations.
Only ``create_canonical`` with an opaque root-bound proof-writer capability
and ``resolve_canonical`` with matching persisted provenance produce a
resolver-sealed canonical record. The fixture authority is permanently
non-real; the mechanism-neutral production verifier remains Layer 3.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    id_pattern_matches,
    new_hpac_id,
    read_canonical_json_document,
    reject_symlink,
    write_atomic_create_only,
)

PROOF_SCHEMA_VERSION = "HPAC-PROOF/2.0"

_PROOF_ALLOWED_FIELDS = frozenset(
    {
        "proof_schema_version",
        "proof_id",
        "proof_digest",
        "mechanism_id",
        "principal_id",
        "credential_id",
        "challenge_digest",
        "approval_subject_digest",
        "trusted_presentation_ref",
        "assertion",
        "up",
        "uv",
        "authenticated_at",
        "verifier_version",
    }
)


class HumanAuthenticationProofError(Exception):
    """Base error for `HumanAuthenticationProof` store operations."""


class HumanAuthenticationProofTrustError(HumanAuthenticationProofError):
    """A structural check failed -- a caller-constructed or forged proof
    is not trustworthy (HPAC-REQ-005)."""


@dataclass(frozen=True)
class HumanAuthenticationProof:
    proof_schema_version: str
    proof_id: str
    proof_digest: str
    mechanism_id: str
    principal_id: str
    credential_id: str
    challenge_digest: str
    approval_subject_digest: str
    trusted_presentation_ref: dict  # {"presentation_id": ..., "presentation_digest": ...}
    assertion: str
    up: bool
    uv: bool
    authenticated_at: str
    verifier_version: str

    def to_document(self, *, include_digest: bool) -> dict:
        doc = {
            "proof_schema_version": self.proof_schema_version,
            "proof_id": self.proof_id,
            "mechanism_id": self.mechanism_id,
            "principal_id": self.principal_id,
            "credential_id": self.credential_id,
            "challenge_digest": self.challenge_digest,
            "approval_subject_digest": self.approval_subject_digest,
            "trusted_presentation_ref": self.trusted_presentation_ref,
            "assertion": self.assertion,
            "up": self.up,
            "uv": self.uv,
            "authenticated_at": self.authenticated_at,
            "verifier_version": self.verifier_version,
        }
        if include_digest:
            doc["proof_digest"] = self.proof_digest
        return doc


def new_proof_id() -> str:
    return new_hpac_id("hap")


def _validate_proof_document(document: dict) -> None:
    if not isinstance(document, dict):
        raise HPACMalformedError("proof record is not an object")
    unknown = set(document.keys()) - _PROOF_ALLOWED_FIELDS
    if unknown:
        raise HPACMalformedError(f"proof record has unrecognized fields: {sorted(unknown)}")
    missing = _PROOF_ALLOWED_FIELDS - set(document.keys())
    if missing:
        raise HPACMalformedError(f"proof record missing required fields: {sorted(missing)}")
    if document.get("proof_schema_version") != PROOF_SCHEMA_VERSION:
        raise HPACMalformedError("proof record has unknown/wrong proof_schema_version")
    if not id_pattern_matches("hap", document.get("proof_id")):
        raise HPACMalformedError("proof_id does not match ^hap-[0-9a-f]{32}$")
    if document.get("up") is not True or document.get("uv") is not True:
        # HPAC-REQ-052: `up`/`uv` are const `true` on a canonical proof --
        # a proof recording a false UP/UV never reaches canonical storage
        # in a real implementation (verification, Phase 3, would reject
        # it before it got here). This store enforces the const shape
        # directly since no verifier exists yet to enforce it upstream.
        raise HumanAuthenticationProofTrustError("a canonical HumanAuthenticationProof requires up == uv == true")
    ref = document.get("trusted_presentation_ref")
    if not isinstance(ref, dict) or set(ref.keys()) != {"presentation_id", "presentation_digest"}:
        raise HPACMalformedError("trusted_presentation_ref has an incorrect closed field set")


class HumanAuthenticationProofStore:
    """`<root>/proofs/v2/<proof_id>/proof.json` (HPAC-REQ-053).
    Create-only, atomic, canonical-lookup-only by `proof_id`."""

    _WRITER_ROLE = "human_authentication_proof_verifier"

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "HumanAuthenticationProofStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def fixture_proof_writer(self, mechanism_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._WRITER_ROLE, subject=mechanism_id)

    def _path(self, proof_id: str) -> Path:
        return self._root / "proofs" / "v2" / proof_id / "proof.json"

    def create(self, proof: HumanAuthenticationProof) -> HumanAuthenticationProof:
        reject_symlink(self._root)
        body_without_digest = proof.to_document(include_digest=False)
        _validate_proof_document({**body_without_digest, "proof_digest": "placeholder"})
        recomputed = canonical_digest(body_without_digest)
        if recomputed != proof.proof_digest:
            raise HumanAuthenticationProofTrustError("proof_digest does not match canonical proof bytes")
        payload_document = proof.to_document(include_digest=True)
        payload = canonical_json_bytes(payload_document)
        write_atomic_create_only(self._path(proof.proof_id), payload)
        return proof

    def create_canonical(
        self,
        writer: HPACWriterCapability,
        proof: HumanAuthenticationProof,
        *,
        certification_proof_subject: Optional[str] = None,
    ) -> HumanAuthenticationProof:
        """Create the canonical ``proof.json`` under the
        ``human_authentication_proof_verifier`` role.

        The fixture path binds the writer capability to ``proof.mechanism_id``
        (its historical ``subject`` convention). HPAC-PAWA-001 v1.3 §33A /
        §43A binds the *certification* proof-verifier capability to the
        reserved ``proof_id`` instead (one verification transaction shared
        with ``HPACLifecycleStore.record_verified_canonical``). Passing
        ``certification_proof_subject`` — which the N-16-5 certification
        coordinator does with the exact ``proof_id`` — checks the capability
        against that subject. This is strictly ADDITIVE (HPAC-PAWA-REQ-260):
        the fixture ``subject == mechanism_id`` path is unchanged and not
        weakened; the override must equal ``proof.proof_id`` or the write is
        refused."""

        if certification_proof_subject is not None:
            if certification_proof_subject != proof.proof_id:
                raise HumanAuthenticationProofTrustError(
                    "certification_proof_subject must equal proof.proof_id"
                )
            require_subject = certification_proof_subject
        else:
            require_subject = proof.mechanism_id
        try:
            self._authority.require_writer(
                writer, self._WRITER_ROLE, subject=require_subject
            )
        except HPACAuthorityError as exc:
            raise HumanAuthenticationProofTrustError(str(exc)) from exc
        created = self.create(proof)
        self._authority.record_write(
            self._path(proof.proof_id),
            proof.proof_digest,
            writer,
            role=self._WRITER_ROLE,
            subject=require_subject,
        )
        return created

    def resolve(self, proof_id: str) -> Optional[HumanAuthenticationProof]:
        """Return validated proof data, without conferring canonical authority."""
        if not id_pattern_matches("hap", proof_id):
            raise HumanAuthenticationProofTrustError("proof_id does not match the hap- grammar")
        reject_symlink(self._root)
        path = self._path(proof_id)
        reject_symlink(path)
        if not path.exists():
            return None
        document = read_canonical_json_document(path)
        _validate_proof_document(document)
        stored_digest = document.get("proof_digest")
        without_digest = {k: v for k, v in document.items() if k != "proof_digest"}
        recomputed = canonical_digest(without_digest)
        if recomputed != stored_digest:
            raise HumanAuthenticationProofTrustError("stored proof_digest does not match canonical bytes")
        return HumanAuthenticationProof(proof_digest=stored_digest, **without_digest)

    def resolve_canonical(
        self, proof_id: str
    ) -> Optional[HPACResolvedRecord[HumanAuthenticationProof]]:
        proof = self.resolve(proof_id)
        if proof is None:
            return None
        try:
            resolved = self._authority.resolve_record(
                record=proof,
                record_path=self._path(proof_id),
                record_digest=proof.proof_digest,
                roles=frozenset({self._WRITER_ROLE}),
                subject=None,
            )
        except HPACAuthorityError as exc:
            raise HumanAuthenticationProofTrustError(str(exc)) from exc
        # The canonical proof-writer capability's ``subject`` is either the
        # ``mechanism_id`` (the fixture-path convention) or the reserved
        # ``proof_id`` (HPAC-PAWA-001 v1.3 §33A / §43A — the N-16-5
        # certification proof-verifier capability). Both are immutable,
        # digest-bound, non-forgeable fields of *this exact* proof record, so
        # accepting either is not a weakening: a forged provenance would have
        # to name one of them, which requires a genuine
        # ``human_authentication_proof_verifier`` capability bound to it.
        if resolved.writer_subject not in {proof.mechanism_id, proof.proof_id}:
            raise HumanAuthenticationProofTrustError(
                "HPAC writer subject binding mismatch (not the proof's mechanism_id or proof_id)"
            )
        return resolved
