"""Production composition and enablement for the Authority Evaluation
Service (AESIC-001 v1.3) -- Phase 147O.1.

**Enablement model** (frozen by this phase): Authority Evaluation is
automatically enabled when, and only when, at least one Decision
Template has been deployed under ``DEFAULT_TEMPLATE_ROOT``
(``.pcae/authority-evaluation/templates/``) -- a persistent,
repository-integrated, filesystem-based opt-in signal that requires no
config file and no environment variable (AESIC-001 places zero
dependency on either; the codebase's existing composition idiom,
``pcae.commands.decision_session.build_application_context``, already
uses plain default-argument ``Path`` roots under ``.pcae/`` for every
other collaborator, never a config file). Absent that directory, or
present but empty, Authority Evaluation stays disabled and every
pre-Phase-147O.1 caller's behavior is byte-for-byte unchanged
(AESIC-REQ-109) -- ``build_authority_evaluation_service`` returns
``None``, the exact default every ``SessionApplicationService`` caller
already tolerates. A deployed template root that exists but is not a
directory, or cannot be listed, is treated as malformed configuration
-- also safe-disabled, never a crash -- and distinguished by ``reason``
in ``describe_authority_evaluation_configuration``'s return value.

The Authority Registry root and AER/canonical-pointer storage root are
*not* separately gated: an absent or empty Registry directory is
already a fully safe, contractually-defined "no declaration" outcome
(``FilesystemAuthorityRegistry.resolve`` returns ``None``, never
raises, for a missing file -- AESIC-REQ-041), and the AER store creates
its own storage tree on first write. Only the Decision Template store
can turn ordinary operation into a hard per-evaluation failure
(``DecisionTemplateNotFoundError``) if enabled prematurely, so it is
the sole enablement signal.

This module is the single place production code decides whether, and
how, to construct ``AuthorityEvaluationService``; no other module
constructs ``FilesystemAuthorityRegistry``/``AuthorityEvaluationRecordStore``/
``AuthorityEvaluationService`` directly (mirrors the narrow
composition-root discipline already used elsewhere in this codebase).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.aesic.registry_filesystem import DEFAULT_REGISTRY_ROOT, FilesystemAuthorityRegistry
from pcae.aesic.service import AuthorityEvaluationService
from pcae.aesic.storage import DEFAULT_STORAGE_ROOT, AuthorityEvaluationRecordStore
from pcae.aesic.template_store import DEFAULT_TEMPLATE_ROOT

logger = logging.getLogger("pcae.aesic.composition")


@dataclass(frozen=True)
class AuthorityEvaluationConfigurationStatus:
    """Read-only snapshot of the enablement decision (diagnostics only
    -- never itself used to gate anything)."""

    enabled: bool
    reason: str
    template_root: str
    registry_root: str
    aer_store_root: str


def _template_store_populated(template_root: Path) -> tuple:
    if not template_root.exists():
        return False, "template_root_absent"
    if not template_root.is_dir():
        return False, "template_root_not_a_directory"
    try:
        has_entry = any(template_root.rglob("*.json"))
    except OSError:
        return False, "template_root_unreadable"
    if not has_entry:
        return False, "template_root_empty"
    return True, "template_root_populated"


def describe_authority_evaluation_configuration(
    *,
    template_root: Path = DEFAULT_TEMPLATE_ROOT,
    registry_root: Path = DEFAULT_REGISTRY_ROOT,
    aer_store_root: Path = DEFAULT_STORAGE_ROOT,
) -> AuthorityEvaluationConfigurationStatus:
    """Determine, without constructing anything, whether Authority
    Evaluation is enabled in this repository and why."""

    template_root = Path(template_root)
    enabled, reason = _template_store_populated(template_root)
    return AuthorityEvaluationConfigurationStatus(
        enabled=enabled,
        reason=reason,
        template_root=str(template_root),
        registry_root=str(Path(registry_root)),
        aer_store_root=str(Path(aer_store_root)),
    )


def build_authority_evaluation_service(
    *,
    template_root: Path = DEFAULT_TEMPLATE_ROOT,
    registry_root: Path = DEFAULT_REGISTRY_ROOT,
    aer_store_root: Path = DEFAULT_STORAGE_ROOT,
) -> Optional[AuthorityEvaluationService]:
    """Construct a production ``AuthorityEvaluationService`` when, and
    only when, Authority Evaluation is enabled (see module docstring);
    otherwise return ``None``. Deterministic, restart-safe: every call
    re-derives the same decision from the same filesystem state, no
    caching, no process-global singleton (AESIC-REQ-015/017/048)."""

    status = describe_authority_evaluation_configuration(
        template_root=template_root, registry_root=registry_root, aer_store_root=aer_store_root
    )
    if not status.enabled:
        logger.info(
            "authority_evaluation.composition_disabled reason=%s template_root=%s",
            status.reason,
            status.template_root,
        )
        return None

    registry = FilesystemAuthorityRegistry(root=Path(status.registry_root))
    aer_store = AuthorityEvaluationRecordStore(root=Path(status.aer_store_root))
    service = AuthorityEvaluationService(registry, aer_store, template_root=Path(status.template_root))
    logger.info(
        "authority_evaluation.composition_enabled template_root=%s registry_root=%s aer_store_root=%s",
        status.template_root,
        status.registry_root,
        status.aer_store_root,
    )
    return service


__all__ = [
    "AuthorityEvaluationConfigurationStatus",
    "describe_authority_evaluation_configuration",
    "build_authority_evaluation_service",
]
