"""HPAC-PPA-001 v1.0 §5 — the sole production consumer of the HPAC-PAWA-001
v1.2 ``configure_presentation_mechanism`` writer factory.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1.

This module is the **only** enumerated production consumer of the
``configure_presentation_mechanism`` PAWA capability (HPAC-PAWA-REQ-087,
HPAC-PPA-REQ-022). It is inside the non-agent-importable fence: ordinary
agent / runtime / Gate / plugin / ``pcae`` CLI code SHALL NOT import it,
directly or transitively, and it is reached only from the standalone
``scripts/hpac_protected_presentation_admin.py`` entry point, run by an
operator logged in as the deployment owner (the real security boundary).

It registers and pins **metadata only** (HPAC-PPA-REQ-004): the helper
executable bytes are installed out of band by the deployment owner at the
fixed content-addressed path. This module never copies, replaces, chmods,
chowns, packages, downloads, or executes helper bytes; it launches no
helper; it writes no presentation evidence; and it touches no Gate,
runtime, adapter, or effect.

Each ``configure_presentation_mechanism`` operation (``install`` / ``rotate``
/ ``revoke``) runs a fresh, complete HPAC-PAWA-001 §33 recognition sequence,
mints one bounded ``_multi_write`` capability bound to the mechanism id and
lifecycle action, and applies exactly one configuration transaction as a
single bounded multi-write completed exactly once (HPAC-PPA-REQ-023).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import HPACStoreAuthority
from pcae.core.hpac_pawa_schemas import new_operation_id
from pcae.core.hpac_protected_admin_writer import (
    PawaError,
    PawaOperation,
    ProductionWriterHandle,
    production_writer,
)
from pcae.core.protected_presentation_installation import (
    MECHANISM_ID,
    ProtectedPresentationInstallationError,
    ProtectedPresentationInstallationStore,
    ResolvedCurrentGeneration,
)

__all__ = [
    "ProtectedPresentationAdminError",
    "configure_presentation_mechanism",
    "resolve_current_presentation_generation",
]


class ProtectedPresentationAdminError(Exception):
    """A protected-presentation configuration administration failure. Wraps
    a terminal PAWA failure code (``exc.pawa_code``) or a
    :class:`ProtectedPresentationInstallationError`."""

    def __init__(self, message: str, *, pawa_code: Optional[str] = None) -> None:
        super().__init__(message)
        self.pawa_code = pawa_code


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def configure_presentation_mechanism(
    *,
    action: str,
    helper_sha256: Optional[str] = None,
    helper_implementation_version: Optional[str] = None,
    verifier_configuration_digest: Optional[str] = None,
    renderer_profile: Optional[str] = None,
    descriptor_version: Optional[str] = None,
    protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> ResolvedCurrentGeneration:
    """Apply exactly one HPAC-PPA-001 v1.0 configuration transaction for the
    ``pcae-protected-local-presentation`` mechanism.

    ``action`` is one of ``install`` / ``rotate`` / ``revoke``. For
    ``install`` and ``rotate`` the helper executable bytes MUST already be
    present out of band at the fixed content-addressed path for
    ``helper_sha256`` (HPAC-PPA-REQ-004/010); ``revoke`` carries the current
    generation's metadata forward and only revokes.

    ``protected_root`` / ``_configured_agent_identity_source`` /
    ``_topology_probe`` are the disclosed HPAC-PAWA-001 §72/§73 test-only
    seams; a guard test asserts no non-test module passes any of them.
    """

    if action not in ("install", "rotate", "revoke"):
        raise ProtectedPresentationAdminError(
            f"action {action!r} is outside the closed lifecycle enum {{install, rotate, revoke}}"
        )
    if action in ("install", "rotate"):
        for name, value in (
            ("helper_sha256", helper_sha256),
            ("helper_implementation_version", helper_implementation_version),
            ("verifier_configuration_digest", verifier_configuration_digest),
            ("renderer_profile", renderer_profile),
            ("descriptor_version", descriptor_version),
        ):
            if not value:
                raise ProtectedPresentationAdminError(f"{action} requires {name}")

    transaction_id = new_operation_id()

    try:
        handle: ProductionWriterHandle = production_writer(
            PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
            mechanism_id=MECHANISM_ID,
            transaction_id=transaction_id,
            presentation_action=action,
            _protected_root=protected_root,
            _configured_agent_identity_source=_configured_agent_identity_source,
            _topology_probe=_topology_probe,
        )
    except PawaError as exc:
        raise ProtectedPresentationAdminError(
            f"PAWA recognition/issuance refused: {exc.code}: {exc.detail}", pawa_code=exc.code
        ) from exc

    authority: HPACStoreAuthority = handle.authority
    try:
        capability = handle.consume(
            PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
            mechanism_id=MECHANISM_ID,
            transaction_id=transaction_id,
        )
    except PawaError as exc:
        raise ProtectedPresentationAdminError(
            f"PAWA capability consume refused: {exc.code}: {exc.detail}", pawa_code=exc.code
        ) from exc

    store = ProtectedPresentationInstallationStore(authority)
    try:
        return store.apply_configuration(
            capability,
            action=action,
            helper_sha256=helper_sha256 or "",
            helper_implementation_version=helper_implementation_version or "",
            verifier_configuration_digest=verifier_configuration_digest or "",
            renderer_profile=renderer_profile or "",
            descriptor_version=descriptor_version or "",
            installed_at=_now(),
        )
    except ProtectedPresentationInstallationError as exc:
        raise ProtectedPresentationAdminError(str(exc)) from exc


def resolve_current_presentation_generation(
    authority: HPACStoreAuthority,
) -> Optional[ResolvedCurrentGeneration]:
    """Read-only helper for the standalone admin tool's ``status``
    sub-command. Not a mutation and not a PAWA consumer."""

    return ProtectedPresentationInstallationStore(authority).resolve_current_generation()
