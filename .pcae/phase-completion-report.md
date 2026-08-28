# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.8 Complete — Independent Verification of B1/B7/N1/N2 Production Authority Repair Implementation

Status: completed. **INDEPENDENTLY VERIFIED — B1/B7/N1/N2 PRODUCTION
AUTHORITY REPAIR COMPLETE (VERIFIED WITH NON-BLOCKING FINDINGS) — REAL
AUTHORITY / RUNTIME EXECUTION STILL UNAVAILABLE.**

Verification-entry commit: `96f7d3ec` (tip of `main` at phase start).
Pre-`.1R.7` fixed baseline: `b85e903c62f386f3c5a45747ded5ff7682b77267`.

Canonical verification evidence:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_8_INDEPENDENT_VERIFICATION_B1_B7_N1_N2_PRODUCTION_AUTHORITY_REPAIR_IMPLEMENTATION.md`.

## Outcome

Independently re-derived B1/B7/N1/N2 and the HPAC-REQ-054 Step-4
prerequisite from the fixed pre-`.1R.7` baseline `b85e903c` and from the
primary contracts (RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0,
PBRD-001 v2.0, RDGO-001 v3.0, RPAC-001 v1.0, POL-005) — not trusted from
`.1R.7`'s report, documentation, or tests. All `.1R.7` source and test
change is isolated in commit `3fc26199`, touching exactly
`src/pcae/core/runtime_authority.py`,
`src/pcae/core/runtime_dispatch_permission.py`, and
`src/pcae/core/hpac_verifier.py` — identical to `.1R.6`'s frozen
production-file matrix. This verification phase modified zero `src/` files.

## Adjudication

```text
B1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
B7 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N2 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
```

This does **not** mean real FIDO2 complete, real protected UI complete,
Gate-5/Gate-9 coordinator wiring complete, Permission Broker integrated,
runtime capable, or execution ready — all remain unbuilt and unavailable.

- **B1** — the copyable module-singleton `_validator_seal` is gone.
  `ValidatedAuthorityProjection` is `eq=False`, held by exact-object
  identity in `_VALIDATED_AUTHORITY_CONTEXTS`, with a content binding
  recomputed over every authority field. Copies, `dataclasses.replace`,
  field mutation, hand-built lookalikes, and cross-invocation transfers all
  fail `is_trusted_validated_authority_projection` and the dispatch
  consumer.
- **B7** — `RuntimeDispatchIdentityTracker.revalidate` re-reads the durable
  invocation/idempotency/attempt records at request-build time; deleted,
  content-changed, and foreign-tracker identity all fail closed.
- **N1** — `validate_approval` takes an opaque approval ID, requires the
  exact `RuntimeInvocationApprovalStore` type, re-loads by ID, and
  unconditionally rejects caller approval objects and duck-typed stores
  before any HPAC trust or projection; validation does not mutate the
  canonical record.
- **N2** — caller `approver_id` / `identity_evidence_kind` raise
  `TypeError`; provenance derives only from a freshly re-verified
  verifier-owned `AuthenticatedHumanPrincipal`; `object.__new__`, copy,
  deepcopy, and pickle forgeries are refused
  (`AuthenticatedHumanPrincipal.__reduce__` raises).
- **Option-A NON-REAL hard stop** — present and effective in both
  `create_runtime_invocation_approval` and `validate_approval`. No
  deterministically-writable `HPACStoreAuthority` can carry `PRODUCTION`
  `authority_class`, so the full-strength deterministic chain still fails
  specifically with
  `non_real_authenticated_principal_cannot_create_production_approval`.
  Positive deterministic real-authority paths: **0**.
- **HPAC-REQ-054 Step 4 (F2)** — independently recomputes the exact
  `Challenge` digest from the canonical 10-field body; caller-supplied and
  self-consistent substituted challenges are rejected. **REPAIRED.**

## Isolation

Gate-5/Gate-9 coordinator wiring = 0; Gate-9 consumption = 0; Gate-10
external effects = 0. `permission_broker_foundation.py` (POL-005) and all
seven contracts are byte-identical to `b85e903c`. `POL-005` still hard-DENYs
any `simulation_only=False` request. Runtime remains
`not_implemented / Observed / observe / unavailable`. Consumer inventory
(AST): `runtime_authority.py` is the sole production consumer of
`hpac_verifier`; `runtime_dispatch_permission.py` is the sole consumer of
the repaired projection; the Gate-9 consumption module has zero production
callers.

## Regression attribution

Fixed-SHA, baseline `b85e903c` vs candidate, `-k "hpac or runtime_authority
or runtime_dispatch"`, full collection: **byte-for-byte identical 23-node
pre-existing failing set**, zero candidate-only nonpassing nodes, zero
baseline-only. The full `-m fast_green` marker run is **344 failed at
baseline vs 343 failed at candidate** — the candidate has one fewer
failure and introduces none. **Unexplained attributable functional
regressions = 0.** 47 fresh independent adversarial tests pass; 201 passed
across all phase-affected modules.

## Non-blocking findings

- **O1** — B1's positive `validate_approval` emission path is unreachable
  under Option-A (NON-REAL stop), so the anti-transfer property is verified
  at the predicate and dispatch-consumer levels, not through a live
  positive emission. Inherent to the frozen staging, not a defect.
- **O2** — `RuntimeInvocationApprovalStore` trust is canonical-path +
  file-integrity (create-exclusive, `O_NOFOLLOW`, `st_nlink == 1`, schema),
  not a cryptographic writer-provenance seal; an actor with direct write
  access to the canonical directory (the documented F7 same-process /
  same-account model) could plant a schema-valid record. Consistent with
  `.1R.6` §12 and F7. Redirection (symlink/hardlink/traversal) *is*
  prevented.
- **O3** — minor `.1R.7` `test_*_detected_by_fresh_reverification` naming
  over-promise for the expiry/presentation/lifecycle cases (same class as
  F4); fail-closed behaviour is real.
- **O4** — pre-existing `pcae doctor task-memory` historical `tasks/DONE.md`
  omissions; governance-record hygiene debt, unrelated to any code path.

F2 repaired. F3, F4, F7 unchanged and **not broadened**.

## Final verdict

```text
INDEPENDENTLY VERIFIED — B1/B7/N1/N2 PRODUCTION AUTHORITY REPAIR COMPLETE
(VERIFIED WITH NON-BLOCKING FINDINGS)
```

No blocking finding. No NON-REAL assurance escalation defect. No production
authority scope boundary violation. No contract drift.

## Next-phase status

**No canonical next phase ID exists.** Control returns to `.1R.6` and
`PROJECT_STATUS.md`. Gate-5/Gate-9 coordinator wiring remains a distinct,
unscheduled later chapter with no assigned ID (no-invent-an-ID discipline);
it requires its own separate planning phase under explicit human
authorization. No coordinator wiring, PB production permission integration,
real FIDO2, protected UI, or execution enablement was begun.

## Governance

```text
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Preserved unchanged. This phase's finalization, commits, and push are
performed by the primary operator under the explicit human authorization
for `.1R.8` only, through the governed `pcae` lifecycle — no raw git
commit/push, no `--no-verify`, no force push, no hook bypass, no history
rewrite.
