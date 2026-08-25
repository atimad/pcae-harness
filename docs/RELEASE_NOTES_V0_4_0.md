# PCAE v0.4.0 Release Notes (Release Candidate — Not Yet Published)

**Status:** release-candidate preparation only. No tag, GitHub Release,
or PyPI upload has been created as of this document. See
`docs/PHASE_149O_20L_7O_3C_4_CONNECTED_CAPABILITY_RELEASE_SCOPE_VERSION_AND_REPRODUCIBLE_BUILD_HARDENING.md`
for the full evidence trail and publication checklist.

## Theme: Connected Governance Capability Consumption

Since `v0.3.1`, PCAE gained a materially new, backward-compatible
capability: **`pcae phase complete` now automatically detects and routes
into PCAE's existing Interactive Workflow / Confirmable Human Governance
Record (CHGR) lifecycle**, rather than requiring the operator to
manually run `decision-session readiness` followed by `governance-record
publish` by hand once a human has confirmed a decision. This is a
workflow-automation change, not a new authority — every human-authority
boundary, permission check, and fail-closed behavior it routes through
already existed and is unchanged.

### What is new (`PRODUCTION-CONSUMED` / `AUTO-ORCHESTRATED`)

- **Interactive Workflow auto-detect + route**: `pcae phase complete`
  looks up whether the active task's `subject_ref` has a `Confirmed`
  Interactive Workflow session, and if so, automatically prepares and
  hands off its publication — non-blocking and silent when there is no
  such session (the overwhelmingly common case; ordinary phase
  completion is unaffected).
- **CHGR downstream automatic consumption**: a confirmed session's
  readiness package is automatically consumed into a Confirmable Human
  Governance Record publication attempt, with the existing CHGR
  identity/uniqueness guarantees unchanged.
- **Publication Execution Ownership auto-invocation**: the existing
  Publication Execution Ownership coordinator is invoked automatically
  as part of this route, through the same production composition root
  the manual CLI commands already use — a caller of this path and an
  operator typing the equivalent commands by hand reach identical
  service state.
- **Permission Broker coverage, no-bypass**: a Permission Broker
  evaluation (`pcae.core.mutation_permission`) is now interposed between
  publication preparation and execution for *both* the manual
  `governance-record publish` CLI path and the new automatic path —
  neither can reach `PublicationCoordinator.execute()` without passing
  this gate.
- **Corrupt-store fail-closed hardening**: a corrupt, unrelated
  Interactive Workflow session file no longer crashes `pcae phase
  complete`; only genuinely relevant corruption fails closed, everything
  else is isolated.

### What has not changed

- **Human authority is preserved exactly as before.** Automatic routing
  never confirms a session, selects a decision, or answers a
  clarification — it only relays an already-`Confirmed` human decision
  into the publication pipeline that already existed for it.
- `automatic routing != automatic approval`; `human confirmation !=
  permission`; `CHGR != general authorization`; `Permission Broker ALLOW
  != execution capability`; `publication ownership != arbitrary
  execution`; `producer provenance != authenticated identity`;
  `confirmed != authorized != permitted != capable != executed`.
- **Runtime remains non-executing.** `State: Observed`, `Maximum
  Capability: observe`, `Execution Availability: unavailable` —
  unchanged by this release.

### Existing capability exposure (unchanged, `EXPOSED`, not newly
consumed)

- Repository Intelligence CLI/product exposure remains available and
  manual; this release does **not** add any internal PCAE consumption of
  Repository Intelligence output.
- Runtime/plugin introspection (`pcae runtime inspect`) remains
  available and non-effectful.
- `pcae authority inspect` remains inspection-only.
- Existing manual Interactive Workflow / CHGR CLI commands
  (`decision-session ...`, `governance-record ...`) remain fully usable
  for diagnostics and for any workflow that predates a bound task
  `subject_ref`.

## Why v0.4.0, not v0.3.2

The changes since `v0.3.1` are not a patch-level fix: `pcae phase
complete` now performs automatic cross-capability orchestration and
introduces new production consumption behavior (an operator-visible
workflow simplification), which is the SemVer-minor bar this project's
own architecture documentation uses. See the phase document's §6/§7 for
the full version-decision rationale.

## Release engineering hardening in this release

- **Reproducible builds**: the sdist's `[tool.hatch.build.targets.sdist]`
  `include` patterns are now root-anchored (`/src/pcae`, `/README.md`,
  `/LICENSE`, `/pyproject.toml`); the previous unanchored patterns could
  match nested paths anywhere in the working tree (for example, a local,
  gitignored `.claude/worktrees/<agent-id>/` directory containing its
  own `src/pcae`), producing a contaminated sdist depending on
  incidental local disk state. `[build-system].requires` now pins
  `hatchling==1.32.0`, the exact backend version verified (via two
  independent clean-clone builds) to produce byte-identical artifacts.

## Deferred (explicitly not part of this release)

Repository Intelligence internal consumption; Runtime Enforcement
consumption; rollback integration; shell-gate enforcement/audit
surfacing; broad Advisory wiring; HATP/HMIC/Class-B authority
activation; CLTR cutover; runtime execution; Telegram inbound; backend/
model execution.
