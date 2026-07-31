"""Minimal, concrete filesystem-backed ``AuthorityRegistry`` (AESIC-001
v1.3 §7; only the minimum concrete adapter required for integration and
tests, per this phase's own authorizing prompt §8).

Exposes exactly the one ABC method (AESIC-REQ-040): no ``create``/
``persist``/``delete``/``list``/``enumerate`` method is added. Performs no
git/repository read (AESIC-REQ-049); restart-durable with no in-memory-only
state (AESIC-REQ-048); pure function of its two inputs at a fixed point in
time (AESIC-REQ-041).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pcae.authority_evaluation.errors import (
    AuthorityRegistryCorruptError,
    AuthorityRegistryUnavailableError,
)
from pcae.authority_evaluation.models import EligibleAuthorityDeclaration
from pcae.authority_evaluation.registry import AuthorityRegistry
from pcae.authority_evaluation.serialization import declaration_from_payload

DEFAULT_REGISTRY_ROOT = Path(".pcae/authority-evaluation/registry")


def _declaration_path(root: Path, template_ref: str, template_version: str) -> Path:
    return Path(root) / template_ref / f"{template_version}.json"


class FilesystemAuthorityRegistry(AuthorityRegistry):
    """Read-only lookup of Declarations stored as ordinary on-disk JSON
    artifacts under ``root`` (AESIC-REQ-049), one file per
    ``(template_ref, template_version)`` pair -- the pair is definitionally
    the storage key (AESIC-REQ-043), so no duplicate-detection scan is ever
    needed (AESIC-REQ-044): the filesystem itself admits at most one file
    per key."""

    def __init__(self, root: Path = DEFAULT_REGISTRY_ROOT) -> None:
        self._root = Path(root)

    def resolve(
        self, template_ref: str, template_version: str
    ) -> Optional[EligibleAuthorityDeclaration]:
        path = _declaration_path(self._root, template_ref, template_version)
        try:
            if not path.exists():
                return None
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AuthorityRegistryUnavailableError(
                f"Registry storage could not be consulted for ({template_ref!r}, "
                f"{template_version!r}): {exc}."
            ) from exc

        try:
            payload = json.loads(raw)
            declaration = declaration_from_payload(payload)
        except Exception as exc:  # noqa: BLE001 -- every parse/shape failure is corruption
            raise AuthorityRegistryCorruptError(
                f"Registry record for ({template_ref!r}, {template_version!r}) is "
                f"structurally malformed: {exc}."
            ) from exc

        if declaration.template_ref != template_ref or declaration.template_version != template_version:
            raise AuthorityRegistryCorruptError(
                f"Registry record stored at ({template_ref!r}, {template_version!r}) carries a "
                f"disagreeing embedded identity ({declaration.template_ref!r}, "
                f"{declaration.template_version!r})."
            )
        return declaration

    def write_declaration(self, declaration: EligibleAuthorityDeclaration) -> None:
        """Authoring-side convenience only (out of this contract's scope,
        §2.2) -- never called by AES, Resolution, or ``resolve`` itself.
        Immutable once written (AESIC-REQ-046): refuses to overwrite an
        existing, differently-keyed-but-colliding file."""

        from pcae.authority_evaluation.serialization import declaration_to_payload

        path = _declaration_path(self._root, declaration.template_ref, declaration.template_version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(declaration_to_payload(declaration), sort_keys=True, indent=2),
            encoding="utf-8",
        )


__all__ = ["DEFAULT_REGISTRY_ROOT", "FilesystemAuthorityRegistry"]
