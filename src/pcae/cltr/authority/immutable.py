"""Recursive immutable JSON-value containers (136Y plan Sec.10-11).

Ordinary ``dict``/``list`` values accepted on input are defensively
converted into immutable equivalents: ``tuple`` for arrays,
``MappingProxyType`` for objects, recursively at every nesting depth. No
Python-specific value (bytes, set, arbitrary object, function) is ever
accepted -- construction raises ``UnsupportedJsonValueError`` instead.

This module performs no interpretation of the values it freezes: it
preserves shape, order, and content only, exactly the discipline required
of ``OpaqueJsonValue`` (``opaque.py``) and ``ExtensionMapping``
(``extensions.py``), both of which are thin wrappers built on top of the
two functions defined here.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from pcae.cltr.authority.errors import UnsupportedJsonValueError

#: The scalar JSON types accepted verbatim, no coercion.
_JSON_SCALAR_TYPES = (type(None), bool, int, float, str)


def freeze_json_value(value: Any) -> Any:
    """Recursively convert a JSON-compatible Python value into its
    immutable equivalent.

    - ``None``/``bool``/``int``/``float``/``str`` are returned unchanged
      (bool is checked before int since ``bool`` is an ``int`` subclass,
      though no distinct handling is actually needed here -- both pass
      through verbatim).
    - A ``Mapping`` (e.g. ``dict``) becomes a ``MappingProxyType`` wrapping
      a freshly built dict of recursively frozen values -- key order is
      preserved exactly as iterated, never re-sorted.
    - A ``list``/``tuple`` becomes a ``tuple`` of recursively frozen
      values -- order is preserved exactly.
    - Any other Python type (bytes, set, frozenset, arbitrary object,
      function) raises ``UnsupportedJsonValueError``.

    The returned structure holds no reference to any mutable input
    container: every mapping/sequence is rebuilt from scratch.
    """

    if isinstance(value, _JSON_SCALAR_TYPES):
        if isinstance(value, float):
            _reject_non_finite_float(value)
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            {_freeze_key(k): freeze_json_value(v) for k, v in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json_value(v) for v in value)
    raise UnsupportedJsonValueError(
        f"unsupported Python value type for JSON-compatible freezing: {type(value)!r}"
    )


def _freeze_key(key: Any) -> str:
    if not isinstance(key, str):
        raise UnsupportedJsonValueError(
            f"JSON object keys must be strings, got {type(key)!r}"
        )
    return key


def _reject_non_finite_float(value: float) -> None:
    if value != value or value in (float("inf"), float("-inf")):  # NaN/Infinity
        raise UnsupportedJsonValueError(
            "non-finite float values (NaN/Infinity) are not JSON-representable"
        )


def thaw_json_value(value: Any) -> Any:
    """Recursively convert a frozen JSON value tree (as produced by
    ``freeze_json_value``) back into plain mutable ``dict``/``list``
    values.

    Always produces a fresh, independent copy: mutating the returned
    structure never affects the frozen value it was derived from.
    """

    if isinstance(value, MappingProxyType):
        return {k: thaw_json_value(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw_json_value(v) for v in value]
    return value


__all__ = ["freeze_json_value", "thaw_json_value"]
