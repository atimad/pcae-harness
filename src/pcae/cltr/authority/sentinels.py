"""The ``ABSENT`` sentinel (136Y plan Sec.9).

Distinguishes "field not present in the wire payload" from "field present
with an explicit ``null``" wherever an executable schema itself
distinguishes the two (i.e. wherever a field is not ``required`` and its
type union permits ``null``). Ordinary ``None`` is never reused to carry
both meanings on any field where the schema distinguishes absent from
null.

``ABSENT`` is a single, module-level, identity-comparable singleton. It is
never a valid wire value: canonical serialization omits any field whose
value ``is ABSENT`` entirely, rather than emitting it as ``null`` or any
other JSON-representable value.
"""

from __future__ import annotations

from typing import Any


class _AbsentType:
    """Private sentinel type. Only one instance (``ABSENT``) is ever
    constructed; callers must not instantiate this class themselves."""

    __slots__ = ()

    _instance: "_AbsentType | None" = None

    def __new__(cls) -> "_AbsentType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<absent>"

    def __bool__(self) -> bool:
        raise TypeError(
            "ABSENT has no truth value; compare identity with 'is ABSENT' instead"
        )

    def __eq__(self, other: Any) -> bool:
        return other is self

    def __ne__(self, other: Any) -> bool:
        return other is not self

    def __hash__(self) -> int:
        return hash(_AbsentType)

    def __copy__(self) -> "_AbsentType":
        return self

    def __deepcopy__(self, memo: dict) -> "_AbsentType":
        return self

    def __reduce__(self):
        return (_absent_singleton, ())


def _absent_singleton() -> "_AbsentType":
    return ABSENT


#: The canonical singleton. Distinct from ``None``, from ``""``, from
#: ``{}``/``[]``, from ``False``, and from ``0`` -- identity comparison
#: (``is ABSENT``) is the only correct way to test for it.
ABSENT: _AbsentType = _AbsentType()

#: Type alias for annotating optional fields whose declared type is
#: ``Union[T, None, AbsentType]`` with ``default=ABSENT``.
AbsentType = _AbsentType

__all__ = ["ABSENT", "AbsentType"]
