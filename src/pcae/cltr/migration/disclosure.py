"""Shared non-authority disclosure constant (Phase 135S — fixes F-135P-4).

135P found ``NON_AUTHORITY_DISCLOSURE`` independently hardcoded five times
in this package (``evidence.py``, ``coordinator.py``, ``persistence.py``,
``status.py``, ``reconciliation.py``); 135R confirmed the count and
disclosed two further, differently-shaped copies in the Stage 0
``cltr/`` namespace (``cltr/persistence.py``, ``cltr/inspection.py``),
out of this fix's scope since Stage 0 is a separate migration stage with
its own field set.

One source of truth for the Stage 1/Stage 2 migration-namespace
disclosure shape. All five Stage 1 consumers, plus every Stage 2
rehearsal module, import this constant rather than hardcoding their own
copy.
"""

from __future__ import annotations

from pcae.cltr.migration.enums import ProductionAuthority

NON_AUTHORITY_DISCLOSURE: dict = {
    "migration_evidence_only": True,
    "authoritative": False,
    "production_authority": ProductionAuthority.LEGACY.value,
    "authority_cutover": False,
    "execution_capability": False,
    "runtime_boundary": "observe",
}


def disclosure() -> dict:
    """Returns a fresh copy — callers may extend it without mutating the
    shared constant."""

    return dict(NON_AUTHORITY_DISCLOSURE)
