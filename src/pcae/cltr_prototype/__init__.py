"""Phase 135F — Canonical Lifecycle Transition Record (CLTR) read-only prototype.

This package is a fixture-driven, offline prototype that demonstrates CLTR-001
v1.0 (frozen, 135B/135C-verified) and the 135D formal state-machine/invariant
model can be represented and evaluated deterministically. It is prototype-only:

- No module here is imported by production finalization code
  (``src/pcae/core/finalization_transaction.py`` or any production entry
  point), and no module here imports them.
- The only permitted write path is ``persistence.py``, and its writes are
  hardcoded to ``.pcae/cltr-prototypes/``.
- No module here executes a shell command, invokes a backend, sends a
  notification, or authorizes execution of any kind.

See docs/PHASE_135_CANONICAL_TRANSITION_RECORD_READ_ONLY_PROTOTYPE.md for the
full implementation report and docs/PHASE_135_CANONICAL_TRANSITION_RECORD_PROTOTYPE_PLAN.md
for the plan this package implements.
"""
