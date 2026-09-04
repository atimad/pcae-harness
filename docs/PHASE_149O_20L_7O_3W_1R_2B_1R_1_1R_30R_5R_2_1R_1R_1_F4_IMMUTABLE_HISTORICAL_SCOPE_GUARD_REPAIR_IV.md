# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.1

## Independent Verification of the F-4 Immutable Historical-Scope Guard Repair

## Verdict

**COMPLETE. F-4: INDEPENDENTLY VERIFIED REPAIRED. F-5: OPEN / UNCHANGED.
N-16-5: NOT CLOSED.**

CPIPC-001 v1.0 accepts the exact phase identifier above. This verification
changed no predecessor test, production source, production script, dependency,
or normative contract.

## Independently derived lineage

- `P = 3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f` — finalized BLOCKED
  `.30R.5R.2.1R.1` certification phase.
- `R = V = 90510428422e451382549ce76111610752aaafb4` — finalized F-4 repair and
  this IV's clean entry.
- `L = a727dbf4f160f904836905d3cb4adeba91953676` — finalized `.30R.4R`
  contract-reconciliation head and true immutable lower bound.
- `U = 5b6b4013a69ffcb366209b12c495571917bb5ccc` — finalized `.30R.4R.1`
  pushed-state head and true immutable upper bound.

The first `.30R.4R.1` commit `99bc5705` has parent `L`. Immutable completion
metadata at `L` identifies completed `.30R.4R`; immutable completion metadata
at `U` identifies completed `.30R.4R.1` and records entry `L`. The first-parent
interval `L..U` is exactly five linear `.30R.4R.1` commits: task open,
implementation, task close, completion staging, and pushed-state reconciliation.
Its immediate child `0a5cc654` opens `.30R.4R.2` and is correctly outside the
historical interval.

## F-4 reconstruction and semantic verification

At `P`, retained owner node
`test_35_no_production_or_script_implementation_changed` combined two source
diffs ending at live history: one explicit `HEAD`, one implicit omitted upper
bound. Its invariant was historical and narrower: production/script changes
attributable to `.30R.4R.1` must remain within the exact eight-file
implementation allowlist. Later legitimate CTAP2 work was therefore absorbed
into the old phase and falsely rejected.

The repair retains the node, name, subset assertion, and exact allowlist, and
changes both reads to `L..U`. Independent Git evaluation produces exactly:

- `scripts/hpac_protected_presentation_admin.py`
- `src/pcae/core/approval_presentation.py`
- `src/pcae/core/hpac_protected_admin_writer.py`
- `src/pcae/core/hpac_protected_presentation_admin.py`
- `src/pcae/core/hpac_verifier.py`
- `src/pcae/core/protected_presentation.py`
- `src/pcae/core/protected_presentation_installation.py`
- `src/pcae/protected_presentation_helper.py`

No live `HEAD`, `origin/main`, completion metadata, report, or
`PROJECT_STATUS.md` determines the historical endpoint. Fixed Git trees make
the result invariant under any descendant. Injecting
`src/pcae/unauthorized.py`, or extending the historical set with the later
`src/pcae/core/hpac_rhamp_ctap2.py`, still fails the original subset assertion.
The guard is therefore history-stable and non-vacuous.

## Test and attribution results

- Fresh F-4 IV suite: **56 passed, 0 failed**.
- F-4 owner plus fresh IV: **98 passed, 0 failed**.
- F-4 repair suite: **43 passed, 0 failed**.
- `.30R.5R.2` predecessor: **71 passed, 0 failed**.
- F-3 repair: **45 passed, 0 failed**.
- F-3 independent verification: **55 passed, 0 failed**.
- Historical `.30R.5R.2.1` current valid evidence: **84 passed, one preserved
  obsolete F-3 demonstration deselected**; its historical BLOCKED report is
  unchanged.
- Focused predecessor/F-3/F-4 group: **312 passed, 0 failed**.
- Broad deterministic affected-scope sweep: **1,433 passed, 3 failed, 1
  deselected**. The three failures are two historical `object.__new__`
  adversarial finding demonstrations and one historical live HMIC digest
  assertion. All three reproduce identically in an isolated worktree at `P`,
  so none is F-4-attributable.

No existing test definition was removed or renamed. No skip, skipif,
`pytest.skip`, xfail, wildcard, glob, `fnmatch`, current-head special case, or
future-commit allowlist was added. The only new test file is the 56-case fresh
IV suite.

## Product, deployment, and runtime boundaries

Production source, scripts, `pyproject.toml`, and all normative contracts are
byte-identical across `P..R` and unchanged in this IV. H-1 source and historical
real-hardware certification, H-2 software IV, F-2 software IV, and F-3
independent verification remain preserved.

F-5 was inspected read-only. The platform-fixed production protected root
`/Library/Application Support/PCAE/HPAC/protected-root` remains absent. No root,
descriptor, helper generation, installation, configuration, rotation,
revocation, or PAWA deployment write occurred. No human election, YubiKey
interaction, presentation evidence, fresh assertion, principal, or Gate
certification occurred.

Runtime remains `not_implemented / Observed / observe / unavailable`, with zero
plugins and zero capabilities. No source changed, so no new effect path,
`adapter.dispatch()`, N-16-6, N-16-7, Slice C, or first external effect became
reachable.

## Disposition and sequenced successors

F-4 is **INDEPENDENTLY VERIFIED REPAIRED**. F-5 remains **OPEN / UNCHANGED**.
N-16-5 remains **NOT CLOSED**.

The exact CPIPC-valid sequence, derived and not begun, is:

1. `.30R.5R.2.1R.1R.2` — Production Protected-Root / Protected-Presentation
   Helper Deployment Preparation.
2. `.30R.5R.2.1R.1R.2.1` — Independent Verification of Production
   Protected-Presentation Helper Installation and Current-Generation Trust
   State.
3. `.30R.5R.2.1R.1R.3` — Final Real Protected-Presentation Human Election +
   Presentation-Bound N-16-5 Certification and Closure.

Each requires separate human authorization. FIDO2/YubiKey remains one
real-hardware-verified supported authentication profile, not exclusive. Local
protected TTY remains one supported presentation profile, not exclusive.
Mechanism-neutral human authentication and protected approval, including a
mobile-only profile, remain open planned future architecture and do not block
unrelated non-effecting development.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
