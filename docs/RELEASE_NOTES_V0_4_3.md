# PCAE v0.4.3 Release Notes

**Status:** release candidate frozen, NOT PUBLISHED. No `v0.4.3` tag,
no GitHub Release, no PyPI upload has been created. See
`docs/PHASE_149O_20L_7O_3O_PCAE_V0_4_3_RELEASE_HARDENING.md` for the
full evidence trail and publication checklist. Publication requires a
separate, explicitly human-authorized phase
(`149O.20L.7O.3O.1`).

## Theme: Rollback Evidence Visibility

Rollback commands now surface the file plan and divergence evidence
already computed and consumed by PCAE's rollback workflow, making the
evidence behind terminal rollback outcomes immediately visible without
requiring a separate rollback-execution inspection step.

This is **EVIDENCE SURFACING / OBSERVABILITY**, not new rollback
preparation automation. Independent verification in `149O.20L.7O.3M.1`
established that, before this change (and before `149O.20L.7O.3M`),
rollback's `file_plan` and `divergence_check` evidence was **already**
computed unconditionally, already internally consumed to gate every
rollback outcome, and already persisted in the canonical
`RollbackExecutionRecord`. `149O.20L.7O.3M` (carried into this release)
only added that already-computed, already-consumed evidence to the
*returned*/printed result of `pcae rollback`, which previously required
a separate `pcae rollback-execution show <rer_id>` call to see.

### What is new

- **Immediate file-plan visibility**: `pcae rollback`'s terminal and
  programmatic output now includes the `file_plan` PCAE already
  computed and already used to decide the outcome, across relevant
  terminal paths (including divergence-conflict and HATP_MANDATORY
  denial results).
- **Immediate divergence-evidence visibility**: the same applies to
  `divergence_check`, surfaced across relevant terminal paths
  (including Permission Broker denial and final success/partial/
  failure results).
- **Additive only**: `file_plan`/`divergence_check` are merged into
  existing result dictionaries and printed alongside existing output;
  no existing field, key, or CLI flag was removed or renamed.
- **Never authoritative**: this surfaced evidence never re-derives,
  overrides, or substitutes for the canonical `RollbackExecutionRecord`
  — it mirrors evidence that already determined the outcome being
  displayed.

### What has not changed

- **Rollback preparation was already automatic before v0.4.3.** The
  `file_plan` and `divergence_check` computation, and their internal
  consumption to gate rollback outcomes, are pre-existing behavior
  independently verified in `149O.20L.7O.3M.1`. `v0.4.3` changes only
  what is *displayed*, not what is *computed* or *consumed*.
  `v0.4.3` CHANGE: evidence surfacing / observability only.
- **Evidence does not authorize rollback.** Surfacing this evidence
  grants no new authority; a clean file plan and divergence check with
  a Permission Broker `DENY` still results in zero mutation.
- **The Permission Broker is unaffected.** Rollback, push, and
  publication Permission Broker gates are unchanged; this release does
  not alter Permission Broker semantics in any way.
- **HATP semantics are unchanged.** `HATP_MANDATORY` denial paths
  behave identically; evidence visibility on that path is additive
  only.
- **Human rollback trigger is unchanged.** Rollback remains explicitly
  human-initiated; no automatic rollback trigger was introduced.
- **Manual dry-run is unaffected and remains optional.** `pcae
  rollback --dry-run` continues to work exactly as before; running a
  real rollback with no prior dry-run continues to work exactly as
  before — dry-run has never been, and is not now, a prerequisite.
- **Runtime remains non-executing.** `State: Observed`, `Maximum
  Capability: observe`, `Execution Availability: unavailable` —
  unchanged by this release.

## Why v0.4.3, not v0.5.0

The only product behavior delta since `v0.4.2` is the additive,
backward-compatible evidence-surfacing change described above: no
authority-model change, no Permission Broker semantics change, no
execution-capability change, no contract/schema redesign, and no new
conceptual CLI workflow. This satisfies patch-version semantics by
every criterion this project's own architecture documentation uses.
See `docs/PHASE_149O_20L_7O_3O_PCAE_V0_4_3_RELEASE_HARDENING.md` for
the full version-decision rationale.

## Release engineering

Build infrastructure is unchanged from `v0.4.2`/`v0.4.1`:
`[build-system].requires` remains pinned to `hatchling==1.32.0`;
`[tool.hatch.build.targets.sdist]` `include` patterns remain
root-anchored. This release reuses that exact, previously-verified
reproducible-build process without modification.

## Deferred (explicitly not part of this release)

True RI-backed Advisory reasoning consumption; F1 repository-provenance
/symlink hardening; a real (non-mock) `AdvisoryProvider` production
connection; new rollback preparation automation, readiness, or
authority; new Permission Broker behavior; HATP/HMIC/Class-B authority
activation; CLTR cutover; runtime execution; model/network expansion.
The mature-capability consumption program at S/M scope was reconfirmed
exhausted in `149O.20L.7O.3N.1`; this release does not reopen it.
