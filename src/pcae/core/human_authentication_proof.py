"""
HPAC-001 v2.0 §17 — `HumanAuthenticationProof` canonical model/store.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). Implements
HPAC-REQ-052/053's exact closed field set and canonical, create-only,
lookup-only-by-ID storage. This module does **not** implement HPAC-018's
verification sequence (Phase 3) -- the canonical
`HumanAuthenticationProofStore.create` path in a real implementation
would only be reachable after that sequence succeeds; this foundation
phase exposes `create` directly so deterministic tests can exercise store
correctness without a verifier that does not exist yet, while still
proving (via `hpac_foundation`'s create-only exclusivity and digest
recomputation) that a caller-constructed lookalike is not silently
accepted as canonical without a matching digest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    canonical_digest,
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

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

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
        import json

        payload = json.dumps(payload_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_create_only(self._path(proof.proof_id), payload)
        return proof

    def resolve(self, proof_id: str) -> Optional[HumanAuthenticationProof]:
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
