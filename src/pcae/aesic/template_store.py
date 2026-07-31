"""Minimal, concrete Decision Template filesystem store (AESIC-001 v1.3
§6; only the minimum concrete adapter required for integration and
tests, per this phase's own authorizing prompt §8).

Decision Templates are ordinary on-disk artifacts under ``.pcae``'s own
storage tree (AESIC-REQ-049) -- never git-history-derived. This module
performs no caching (AESIC-REQ-034) and no retry (AESIC-REQ-037): a
single storage read, once, per call.

Template authoring (write path) is explicitly out of scope for AES and
Resolution (AESIC-REQ-030); ``write_template`` exists only as an
authoring-side convenience for tests and operators, never called by
``DecisionTemplateResolution`` itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pcae.aesic.errors import (
    DecisionTemplateCitationEmptyError,
    DecisionTemplateMalformedError,
    DecisionTemplateNotFoundError,
)

DEFAULT_TEMPLATE_ROOT = Path(".pcae/authority-evaluation/templates")
TEMPLATE_SCHEMA_VERSION = "aesic-decision-template/1.0"


class DecisionTemplateDocument:
    """A resolved Decision Template document's two relevant fields
    (AESIC-REQ-029): ``eligible_authority`` (the sole source of
    ``citation_text``) and its own ``(template_ref, template_version)``
    identity, owned by whoever authors/versions templates (AESIC-REQ-030)."""

    __slots__ = ("template_ref", "template_version", "eligible_authority")

    def __init__(self, template_ref: str, template_version: str, eligible_authority: str) -> None:
        self.template_ref = template_ref
        self.template_version = template_version
        self.eligible_authority = eligible_authority


def _template_path(root: Path, template_ref: str, template_version: str) -> Path:
    return Path(root) / template_ref / f"{template_version}.json"


def write_template(
    template_ref: str,
    template_version: str,
    eligible_authority: str,
    *,
    root: Path = DEFAULT_TEMPLATE_ROOT,
) -> None:
    """Authoring-side convenience only -- never called by Resolution."""

    path = _template_path(root, template_ref, template_version)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "template_ref": template_ref,
        "template_version": template_version,
        "eligible_authority": eligible_authority,
        "schema_version": TEMPLATE_SCHEMA_VERSION,
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")


def read_template(
    template_ref: str,
    template_version: str,
    *,
    root: Path = DEFAULT_TEMPLATE_ROOT,
) -> DecisionTemplateDocument:
    """Read exactly the ``(template_ref, template_version)`` pair supplied
    -- never resolved implicitly to "latest" (AESIC-REQ-036).

    Raises ``DecisionTemplateNotFoundError``, ``DecisionTemplateMalformedError``,
    or ``DecisionTemplateCitationEmptyError`` per §6.4's failure model
    (AESIC-REQ-033), and no other exception type.
    """

    path = _template_path(root, template_ref, template_version)
    if not path.exists():
        raise DecisionTemplateNotFoundError(
            f"No Decision Template document for ({template_ref!r}, {template_version!r})."
        )

    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise DecisionTemplateMalformedError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            f"could not be read/parsed: {exc}."
        ) from exc

    if not isinstance(payload, dict):
        raise DecisionTemplateMalformedError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            "is not a JSON object."
        )

    eligible_authority: Optional[str] = payload.get("eligible_authority")
    doc_template_ref = payload.get("template_ref")
    doc_template_version = payload.get("template_version")
    if not isinstance(doc_template_ref, str) or not doc_template_ref:
        raise DecisionTemplateMalformedError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            "has a missing/empty template_ref."
        )
    if not isinstance(doc_template_version, str) or not doc_template_version:
        raise DecisionTemplateMalformedError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            "has a missing/empty template_version."
        )
    if doc_template_ref != template_ref or doc_template_version != template_version:
        raise DecisionTemplateMalformedError(
            f"Decision Template document at ({template_ref!r}, {template_version!r})'s own "
            f"storage path carries a disagreeing embedded identity "
            f"({doc_template_ref!r}, {doc_template_version!r})."
        )

    if eligible_authority is None or not isinstance(eligible_authority, str):
        raise DecisionTemplateMalformedError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            "has a missing/non-str eligible_authority field."
        )
    if eligible_authority.strip() == "":
        raise DecisionTemplateCitationEmptyError(
            f"Decision Template document for ({template_ref!r}, {template_version!r}) "
            "has an empty/whitespace-only eligible_authority field."
        )

    return DecisionTemplateDocument(
        template_ref=doc_template_ref,
        template_version=doc_template_version,
        eligible_authority=eligible_authority,
    )


__all__ = [
    "DEFAULT_TEMPLATE_ROOT",
    "TEMPLATE_SCHEMA_VERSION",
    "DecisionTemplateDocument",
    "write_template",
    "read_template",
]
