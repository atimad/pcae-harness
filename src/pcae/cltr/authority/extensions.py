"""``ExtensionMapping`` (136Y plan Sec.10).

Shared representation for a record's ``_extensions`` field. Applies only
to Tier 2 families (confirmed per 136X Sec.3: at minimum
``compatibility_state``, ``quarantine_record``); which families are Tier 2
is re-confirmed against each family's executable schema at the time that
family's record model is implemented, never assumed uniformly here.

An ``ExtensionMapping`` never interprets its contents: it never promotes
an extension key into a canonical field, never treats an extension as
authority, never interprets an embedded lifecycle instruction, never
executes an embedded command, and never resolves an embedded URL. No
secret-detection is implemented or claimed.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import AbstractSet, Any, ItemsView, KeysView, ValuesView

from pcae.cltr.authority.errors import TypedModelConstructionError
from pcae.cltr.authority.immutable import freeze_json_value, thaw_json_value

#: Matches the executable schema's ``maxProperties: 32`` bound on
#: ``_extensions`` (136Y plan Sec.10).
MAX_EXTENSION_PROPERTIES = 32


@dataclasses.dataclass(frozen=True)
class ExtensionMapping:
    """An immutable, order-preserving, deep-copied wrapper over the
    ``_extensions`` field.

    Values are constrained to JSON-representable types only
    (str/int/float/bool/None/list/dict, recursively) -- never Python-
    specific types. The wrapper itself is immutable (no ``__setitem__``);
    construction deep-copies (via freezing) the input mapping so a
    caller's later mutation of their own source dict cannot retroactively
    alter a constructed instance.
    """

    _frozen_mapping: MappingProxyType

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Any],
        *,
        reserved_keys: AbstractSet[str] = frozenset(),
    ) -> "ExtensionMapping":
        """Construct from a plain mapping.

        ``reserved_keys`` names the owning record's canonical field names
        (supplied by the caller, since this shared-core type has no
        knowledge of any specific record family's field list) -- an
        extension key colliding with a reserved key is rejected outright,
        never silently shadowed or promoted.
        """

        if len(mapping) > MAX_EXTENSION_PROPERTIES:
            raise TypedModelConstructionError(
                f"_extensions has {len(mapping)} keys, exceeding the maximum of "
                f"{MAX_EXTENSION_PROPERTIES}"
            )
        for key in mapping:
            if not isinstance(key, str):
                raise TypedModelConstructionError(
                    f"_extensions keys must be strings, got {type(key)!r}"
                )
            if key in reserved_keys:
                raise TypedModelConstructionError(
                    f"_extensions key {key!r} collides with a canonical field name"
                )
        frozen = freeze_json_value(dict(mapping))
        return cls(_frozen_mapping=frozen)

    def to_dict(self) -> dict:
        """Return a fresh, independent, mutable copy of the extension
        mapping, in original key order."""

        return thaw_json_value(self._frozen_mapping)

    def __len__(self) -> int:
        return len(self._frozen_mapping)

    def __contains__(self, key: object) -> bool:
        return key in self._frozen_mapping

    def __getitem__(self, key: str) -> Any:
        return thaw_json_value(self._frozen_mapping[key])

    def keys(self) -> KeysView:
        return self._frozen_mapping.keys()

    def values(self) -> ValuesView:
        return self._frozen_mapping.values()

    def items(self) -> ItemsView:
        return self._frozen_mapping.items()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExtensionMapping):
            return NotImplemented
        return self._frozen_mapping == other._frozen_mapping

    # Deliberately not hashable (Sec.10/19): a Mapping-backed value is not
    # forced to be hashable, and no `__hash__` is defined here, so any
    # containing record model with an `_extensions` field is itself
    # unhashable by default dataclass behavior.
    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"ExtensionMapping({self.to_dict()!r})"


__all__ = ["ExtensionMapping", "MAX_EXTENSION_PROPERTIES"]
