"""``OpaqueJsonValue`` (136Y plan Sec.11, [NEW] component).

Lossless representation for contract-underspecified and extension values.
Applies today to exactly two fields (per 136X's ambiguity register):
``FinalizationReceiptAuthorityBinding.staleness_check`` (``DEFERRED-136T-1``)
and ``CompatibilityState.retirement_state`` (``DEFERRED-136V-1``), both
currently pinned to an empty-shape placeholder (``{}``) by the frozen
executable schema. This wrapper type is deliberately general-purpose (not
field-specific), so it is ready to keep preserving whatever JSON value it
is given verbatim once a future contract erratum defines a richer shape --
round-trip safety does not depend on knowing that shape in advance.

No semantic meaning is ever assigned to an opaque value: this module
performs no interpretation, no execution, no network access, no
repository lookup, and no secret expansion.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from pcae.cltr.authority.errors import OpaqueValuePreservationError
from pcae.cltr.authority.immutable import freeze_json_value, thaw_json_value


@dataclasses.dataclass(frozen=True)
class OpaqueJsonValue:
    """An immutable, order-preserving, deep-copied wrapper around an
    arbitrary JSON-compatible value.

    Construction freezes the input recursively (``immutable.py``); nested
    values are never mutable after construction, and a caller's later
    mutation of their own source dict/list cannot retroactively alter a
    constructed instance.
    """

    _frozen_value: Any

    @classmethod
    def from_json(cls, value: Any) -> "OpaqueJsonValue":
        return cls(_frozen_value=freeze_json_value(value))

    def to_json(self) -> Any:
        """Return the exact JSON value this instance was constructed with,
        as a fresh, independent, mutable copy."""

        return thaw_json_value(self._frozen_value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OpaqueJsonValue):
            return NotImplemented
        return self._frozen_value == other._frozen_value

    def __hash__(self) -> int:
        # A MappingProxyType-wrapped or tuple-of-unhashable-elements value
        # is itself unhashable; that unhashability is allowed to propagate
        # (Section 19: hashability is never forced).
        return hash(self._frozen_value)

    def __repr__(self) -> str:
        return f"OpaqueJsonValue({self.to_json()!r})"


def verify_round_trip(original: Any, wrapped: OpaqueJsonValue) -> None:
    """Defensive internal-consistency check (Sec.29's
    ``OpaqueValuePreservationError``): raised only if a round trip through
    ``OpaqueJsonValue`` produced a value unequal to its input, which should
    be unreachable in a correct implementation."""

    round_tripped = wrapped.to_json()
    if round_tripped != original:
        raise OpaqueValuePreservationError(
            "OpaqueJsonValue round-trip produced a value unequal to its input"
        )


__all__ = ["OpaqueJsonValue", "verify_round_trip"]
