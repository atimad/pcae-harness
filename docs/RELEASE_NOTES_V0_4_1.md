# PCAE v0.4.1 Release Notes (Release Candidate — Not Yet Published)

**Status:** release-candidate preparation only. No tag, GitHub Release,
or PyPI upload has been created as of this document. See
`docs/PHASE_149O_20L_7O_3H_PCAE_V0_4_1_RELEASE_HARDENING.md` for the
full evidence trail and publication checklist.

## Theme: Permission Broker Rollback Coverage Completion

Since `v0.4.0`, PCAE gained one narrow, backward-compatible governance
hardening: **the default (non-`HATP_MANDATORY`) `pcae rollback`
dispatch path now consumes the centralized Permission Broker**, closing
the final Permission Broker coverage gap identified by the current
production mutation-path audit (`pcae push`, `pcae commit`, `pcae
promote`, the alternate push path, and publication were already
broker-gated as of `v0.4.0`; rollback's default path was the one
remaining unguarded root-mutating command).

### What is new (`PRODUCTION-CONSUMED`)

- **Rollback default-path Permission Broker gate**: `build_rollback_execution`'s
  default (non-`HATP_MANDATORY`) branch now calls a new
  `mutation_permission.evaluate_rollback_permission()` adapter,
  mirroring the shape of the existing commit/push/promotion/publication
  adapters, immediately before the restore/remove mutation loop.
- **Fail-closed on DENY, broker failure, and malformed result**: any of
  these three outcomes returns immediately with zero file mutation and
  a new, correctly-registered terminal `RollbackExecutionRecord` status
  (`aborted_permission_denied`) — no fallback path exists back into the
  mutation loop.
- **ALLOW preserves existing eligible behavior**: when the broker
  authorizes, dispatch proceeds exactly as it did before this release —
  identical file restore/remove behavior, identical `RollbackExecutionRecord`
  success shape.

### What has not changed

- **Dry-run/readiness/evidence behavior is unchanged.** `pcae rollback
  --per-id X --dry-run` returns before reaching either the
  `HATP_MANDATORY` check or the new gate, with zero broker/task
  precondition — exactly as before this release.
- **The `HATP_MANDATORY` path is unchanged.** Its own, separate,
  pre-existing HATP-integrated broker gate (`hatp_rollback_consumption.evaluate_for_real_effect`)
  is byte-identical to `v0.4.0`; the new adapter is never invoked on
  that branch.
- **Human rollback initiation is unchanged.** `pcae rollback --per-id
  <PER_ID> [--dry-run] [--hatp-evidence-id ID] [--json]` remains the
  sole production entry point; the broker adds a machine-checked
  authorization gate on an already-human-initiated action, not a
  substitute trigger and not a new human step.
- **Runtime remains non-executing.** `State: Observed`, `Maximum
  Capability: observe`, `Execution Availability: unavailable` —
  independently reverified unchanged before and after a disposable
  ALLOW-path rollback.
- `Permission Broker ALLOW != execution capability`; `Permission !=
  human authority`; `human rollback trigger != Permission Broker
  decision`; `dry-run/readiness != rollback effect`; `HATP_MANDATORY !=
  default rollback path`.

### Existing capability exposure (unchanged, `EXPOSED`, not newly
consumed)

- Repository Intelligence CLI/product exposure remains available and
  manual; this release does not add any internal PCAE consumption of
  Repository Intelligence output.
- Runtime/plugin introspection (`pcae runtime inspect`) remains
  available and non-effectful.
- `pcae authority inspect` remains inspection-only.
- The `v0.4.0` connected-consumption graph (`pcae phase complete` →
  Interactive Workflow auto-detect/route → CHGR → Permission Broker →
  Publication Execution Ownership) is unchanged and reverified intact
  by this release's regression pass.

## Permission Broker coverage — scope of the claim

This release closes the rollback default-path gap, the last one
identified by the current production mutation-path audit conducted
across `149O.20L.7O.3C.1`, `3E`, `3F`, `3F.1`, and `3H`. It is not a
claim that every conceivable mutation path anywhere in PCAE is
permanently covered — only that every root-mutating command currently
identified and audited (`push`, `commit`, `promote`, the alternate
push path, publication, and now rollback's default path) consumes the
centralized Permission Broker.

## Why v0.4.1, not v0.5.0

The change since `v0.4.0` is patch-level by every criterion this
project's own architecture documentation uses: backward compatible, no
new conceptual workflow (rollback's CLI syntax and semantics are
unchanged), no authority-model change, no execution-capability
increase, no new contract or schema (reuses existing `ACTION_ROLLBACK`/
`EXECUTION_CLASS_MUTATION` vocabulary and the existing
`_RER_VALID_STATUSES` extension mechanism), and no CLI redesign. See
`docs/PHASE_149O_20L_7O_3G_POST_ROLLBACK_PERMISSION_INTEGRATION_RELEASE_AND_NEXT_CAPABILITY_DECISION.md`
for the full version-decision rationale.

## Release engineering

Build infrastructure is unchanged from `v0.4.0`: `[build-system].requires`
remains pinned to `hatchling==1.32.0`; `[tool.hatch.build.targets.sdist]`
`include` patterns remain root-anchored (`/src/pcae`, `/README.md`,
`/LICENSE`, `/pyproject.toml`). This release reuses that exact,
previously-verified reproducible-build process without modification.

## Deferred (explicitly not part of this release)

Runtime preflight disclosure; rollback readiness/evidence
auto-generation; Repository Intelligence internal consumption;
Advisory context integration; Runtime Enforcement consumption; HATP/
HMIC/Class-B authority activation; CLTR cutover; runtime execution;
Telegram inbound; backend/model execution.
