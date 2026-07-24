"""Migration hook skeleton (Phase 143K).

A structural extension point only: a registry from a source
``schema_version`` string to a migration callable. No migration is
registered by Phase 143K -- there is exactly one schema version
(``pcae.interactive_workflow.serialization.SCHEMA_VERSION``) so far, so
there is nothing to migrate from yet. Future phases register hooks here
rather than special-casing version strings inside ``SessionRepository``
implementations.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable, Dict, Mapping

from pcae.interactive_workflow.errors import UnsupportedVersionError

MigrationHook = Callable[[Mapping[str, object]], Mapping[str, object]]
"""A migration hook maps a payload at some prior schema version to a
payload at the next schema version. Pure function: no I/O, no partial
mutation of its input."""


class MigrationRegistry:
    """Registers and looks up migration hooks by source schema version."""

    def __init__(self) -> None:
        self._hooks: Dict[str, MigrationHook] = {}

    def register(self, from_version: str, hook: MigrationHook) -> None:
        self._hooks[from_version] = hook

    def hook_for(self, from_version: str) -> MigrationHook:
        try:
            return self._hooks[from_version]
        except KeyError as exc:
            raise UnsupportedVersionError(
                f"No migration hook registered for schema_version {from_version!r}."
            ) from exc

    def known_versions(self) -> Mapping[str, MigrationHook]:
        return MappingProxyType(dict(self._hooks))


__all__ = [
    "MigrationHook",
    "MigrationRegistry",
]
