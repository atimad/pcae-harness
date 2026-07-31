"""Decision Template & Declaration Resolution (AESIC-001 v1.3 §6).

Internal to AES (AESIC-REQ-027): not a separately callable public
component. Performs no caching (AESIC-REQ-034), no retry (AESIC-REQ-037),
and is Registry's only caller, exactly once per invocation
(AESIC-REQ-038). Always completes, successfully or with a disclosed
failure, before ``evaluate()`` is invoked (AESIC-REQ-039).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.authority_evaluation.errors import (
    AuthorityRegistryCorruptError,
    AuthorityRegistryUnavailableError,
)
from pcae.aesic.errors import (
    DecisionTemplateCitationEmptyError,
    DecisionTemplateMalformedError,
    DecisionTemplateNotFoundError,
)
from pcae.authority_evaluation.models import EligibleAuthorityDeclaration
from pcae.authority_evaluation.registry import AuthorityRegistry
from pcae.aesic.template_store import DEFAULT_TEMPLATE_ROOT, read_template


@dataclass(frozen=True)
class ResolutionResult:
    """The two values Resolution derives from one resolved Decision
    Template document (AESIC-REQ-029) -- never two independent reads."""

    citation_text: str
    declaration: Optional[EligibleAuthorityDeclaration]


class DecisionTemplateResolution:
    """AES's own, internal Decision Template & Declaration Resolution
    capability. Stateless and side-effect-free apart from the one template
    read and one Registry call each invocation performs."""

    def __init__(self, registry: AuthorityRegistry, template_root: Path = DEFAULT_TEMPLATE_ROOT) -> None:
        self._registry = registry
        self._template_root = template_root

    def resolve(self, template_ref: str, template_version: str) -> ResolutionResult:
        """Resolve ``(template_ref, template_version)`` -- accepts exactly
        this pair, no other input (AESIC-REQ-028), always the exact pair
        supplied, never "latest" (AESIC-REQ-036).

        Raises ``DecisionTemplateNotFoundError``, ``DecisionTemplateMalformedError``,
        or ``DecisionTemplateCitationEmptyError`` for a template-resolution
        failure; propagates ``AuthorityRegistryUnavailableError``/
        ``AuthorityRegistryCorruptError`` unchanged for a Registry failure
        (AESIC-REQ-033) -- never conflated with each other.
        """

        document = read_template(template_ref, template_version, root=self._template_root)
        # AESIC-REQ-031: citation_text is the resolved document's own
        # eligible_authority, copied verbatim -- never summarized/re-derived.
        citation_text = document.eligible_authority

        declaration = self._registry.resolve(template_ref, template_version)
        return ResolutionResult(citation_text=citation_text, declaration=declaration)


__all__ = ["ResolutionResult", "DecisionTemplateResolution"]
