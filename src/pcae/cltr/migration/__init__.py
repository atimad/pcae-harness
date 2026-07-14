"""Phase 135O — Stage 1 dual derivation, legacy lifecycle authority.

This package implements exactly the Stage 1 slice of the verified 135M
migration contract (as repaired and confirmed by 135N): one shared,
immutable transition-input package; staged assembly matching field
availability (135M §8.4); a design-B independent ``transition_id``; a
dual-derivation coordinator that runs the existing legacy finalization
path and the existing production CLTR package against the *same* shared
input and compares them; migration evidence persistence; and read-only
status/reconciliation surfaces.

Non-authority disclosure applies to every artifact this package produces:
legacy lifecycle remains the sole production authority; CLTR remains
derivative; this package never certifies, promotes, checkpoints,
notifies, marks, or finalizes a receipt; it never introduces execution
capability (no subprocess/shell/socket/backend invocation).
"""
