"""Phase 135K — Production Canonical Lifecycle Transition Record (CLTR).

This package is the production, shadow-mode-only implementation of
CLTR-SCHEMA-001 v1.0.1 (Phase 135I, repaired by 135J). It is deliberately
separate from ``pcae.cltr_prototype`` (Phase 135F/135G): the prototype is
evidence this package re-derives algorithms from where independently
justified, never a production dependency. No module in this package is
imported by ``pcae.cltr_prototype``, and no module in this package imports
from it.

**Non-authority boundary (binding for every module in this package):**
Nothing here controls lifecycle transitions, certification, report
promotion, notification dispatch, marker creation, receipt finalization,
task completion, or Architecture Status. Every constructed record, every
persisted generation, and every CLI output explicitly discloses
``shadow_mode: true`` / ``authoritative: false``. See
``docs/PHASE_135_PRODUCTION_CLTR_SHADOW_INTEGRATION_IMPLEMENTATION.md``.
"""
