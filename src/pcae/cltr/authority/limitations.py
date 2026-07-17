"""``Limitations`` and ``AuthorityDisclosure`` (136Y plan Sec.5; schema
source: ``shared/limitations.schema.json``).

Limitations are disclosures only and never alter authority or lifecycle
outcome. ``AuthorityDisclosure.is_authoritative`` is pinned to the literal
``False`` -- never computed, never settable, matching the frozen schema's
``const: false`` restriction exactly.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Tuple

from pcae.cltr.authority.enums import AuthorityRole
from pcae.cltr.authority.errors import TypedModelConstructionError

_CONTROL_CHAR_PATTERN = re.compile(r"^[^\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*$")
_MAX_NEWLINES_PATTERN = re.compile(r"^(?:[^\n]*\n){0,8}[^\n]*$")
_DISCLOSURE_TEXT_PATTERN = re.compile(r"^[\x20-\x7E]*$")

MAX_LIMITATIONS_ITEMS = 32
MAX_LIMITATION_ENTRY_LENGTH = 2000
MAX_DISCLOSURE_TEXT_LENGTH = 500


def _validate_limitation_entry(entry: str) -> str:
    if not isinstance(entry, str) or not (1 <= len(entry) <= MAX_LIMITATION_ENTRY_LENGTH):
        raise TypedModelConstructionError(
            f"limitation entry must be a non-empty string of at most "
            f"{MAX_LIMITATION_ENTRY_LENGTH} characters"
        )
    if not _CONTROL_CHAR_PATTERN.fullmatch(entry):
        raise TypedModelConstructionError(
            "limitation entry contains a forbidden control character"
        )
    if not _MAX_NEWLINES_PATTERN.fullmatch(entry):
        raise TypedModelConstructionError(
            "limitation entry contains more than 8 newline characters"
        )
    return entry


@dataclasses.dataclass(frozen=True)
class Limitations:
    """The bounded free-text ``limitations`` array present on every
    ``records/*.schema.json`` file. An empty tuple is permitted (no
    limitations to disclose); duplicate entries are not rejected here
    (a Layer 4/authoring-review concern)."""

    entries: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        entries = tuple(self.entries)
        if len(entries) > MAX_LIMITATIONS_ITEMS:
            raise TypedModelConstructionError(
                f"limitations array has {len(entries)} entries, exceeding the "
                f"maximum of {MAX_LIMITATIONS_ITEMS}"
            )
        for entry in entries:
            _validate_limitation_entry(entry)
        object.__setattr__(self, "entries", entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def to_wire(self) -> list:
        """The wire shape of ``limitations`` is a plain JSON array of
        strings, not an object -- this wrapper's own single field is
        elided at serialization time via this hook."""

        return list(self.entries)


@dataclasses.dataclass(frozen=True)
class AuthorityDisclosure:
    """Schema validity of this struct never establishes lifecycle
    authority, cutover eligibility, authorization, publication success, or
    recovery truth (contract Sec.1/Sec.40)."""

    authority_role: AuthorityRole
    disclosure_text: str
    is_authoritative: bool = False

    def __post_init__(self) -> None:
        if self.is_authoritative is not False:
            raise TypedModelConstructionError(
                "AuthorityDisclosure.is_authoritative is a frozen const false; "
                "no model may override it locally"
            )
        if not isinstance(self.disclosure_text, str) or not (
            1 <= len(self.disclosure_text) <= MAX_DISCLOSURE_TEXT_LENGTH
        ):
            raise TypedModelConstructionError(
                f"AuthorityDisclosure.disclosure_text must be a non-empty string "
                f"of at most {MAX_DISCLOSURE_TEXT_LENGTH} characters"
            )
        if not _DISCLOSURE_TEXT_PATTERN.fullmatch(self.disclosure_text):
            raise TypedModelConstructionError(
                "AuthorityDisclosure.disclosure_text must be single-line "
                "printable ASCII only"
            )


__all__ = [
    "Limitations",
    "AuthorityDisclosure",
    "MAX_LIMITATIONS_ITEMS",
    "MAX_LIMITATION_ENTRY_LENGTH",
    "MAX_DISCLOSURE_TEXT_LENGTH",
]
