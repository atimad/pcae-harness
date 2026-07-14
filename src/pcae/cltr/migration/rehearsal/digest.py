"""Stage 2 digest contract (135Q §19).

Reuses CLTR-SCHEMA-001's canonicalization exactly (sorted keys, NFC
strings, compact JSON, SHA-256) via ``pcae.cltr.digest`` /
``pcae.cltr.canonicalization`` -- never a reimplementation.
"""

from __future__ import annotations

from pcae.cltr.digest import compute_dict_digest

DIGEST_ALGORITHM = "sha256"


def compute_artifact_digest(content: dict) -> str:
    return compute_dict_digest(content)


def compute_generation_digest(
    *,
    artifact_digests_in_order: tuple[str, ...],
    rehearsal_generation_id: str,
    migration_epoch: str,
    authority_epoch: str,
    transition_id: str,
) -> str:
    """135Q §19 -- nested digest binding: covers each artifact's own
    (already-computed) digest, never raw artifact bytes, plus the four
    generation-identity fields. Excludes the manifest's own
    ``generation_digest`` field from its own input by construction (the
    caller never passes it here)."""

    return compute_dict_digest(
        {
            "artifact_digests": list(artifact_digests_in_order),
            "rehearsal_generation_id": rehearsal_generation_id,
            "migration_epoch": migration_epoch,
            "authority_epoch": authority_epoch,
            "transition_id": transition_id,
        }
    )
