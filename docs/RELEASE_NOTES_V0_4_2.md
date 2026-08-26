# PCAE v0.4.2 Release Notes

**Status:** published. Tag `v0.4.2` and the GitHub Release are live,
pinned to release-candidate commit
`bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`. No PyPI upload has been
created. See
`docs/PHASE_149O_20L_7O_3L_PCAE_V0_4_2_RELEASE_HARDENING.md` for the
full evidence trail and publication checklist.

## Theme: Repository Intelligence Context Attachment for Advisory Mode

Since `v0.4.1`, PCAE gained one narrow, backward-compatible, additive
behavior: **`pcae advisory check` now automatically attaches available
Repository Intelligence context to its output.** This is **AUTOMATIC
RI CONTEXT ATTACHMENT**, not RI-backed Advisory reasoning — Advisory
Mode's decision logic does not read, weigh, or otherwise consume this
context. It is disclosed alongside the existing, unchanged decision
output for human/tooling review.

### What is new (`AUTOMATIC RI CONTEXT ATTACHMENT`)

- **Automatic acquisition**: `build_advisory` (the function behind
  `pcae advisory check`) now automatically acquires the existing
  Repository Intelligence Advisory-context package, via the same
  canonical bridge (`pcae.advisory.context.build_advisory_context`)
  previously reachable only through the manual `pcae advisory-context
  build` CLI command, and attaches it to Advisory Mode output as a new
  `repository_intelligence_context` field.
- **No manual prerequisite**: obtaining RI context in Advisory Mode
  output no longer requires running `pcae advisory-context build`
  first. If a Repository Intelligence snapshot already exists at the
  canonical `.pcae/repository-intelligence/latest.json` path, it is
  used automatically.
- **Read-only acquisition**: this acquisition path never writes,
  regenerates, or otherwise mutates the Repository Intelligence
  snapshot or any other repository state.
- **Provenance and limitations preserved**: the attached context
  carries the same `context_metadata`/`limitation_bundle` fields the
  existing manual context-build path produces, plus a new
  `possibly_stale_snapshot` limitation entry when the snapshot's
  recorded source commit differs from the current `HEAD`.
- **Truthful fail-soft degradation**: if no snapshot exists, or the
  snapshot is invalid/incompatible, `repository_intelligence_context`
  reports `"available": false` with a specific `unavailable_reason`
  (`no_repository_intelligence_snapshot_found` or
  `repository_intelligence_context_build_failed`) — never a fabricated
  or partially-valid context, and never a raised exception/traceback.

### What has not changed

- **TRUE RI-BACKED ADVISORY REASONING IS NOT IMPLEMENTED.** Advisory
  Mode's `broker_decision`, `advisory_decision`, all `would_*` fields,
  `hard_block_present`, and every other existing authority/decision
  field are computed exactly as before this release, from exactly the
  same inputs. `repository_intelligence_context` is additive-only and
  is never read by the Permission Broker or by any decision-computing
  code path in `build_advisory`. This distinction is deliberate and
  remains open/deferred: see
  `docs/PHASE_149O_20L_7O_3K_POST_RI_ATTACHMENT_ARCHITECTURE_AND_RELEASE_DECISION.md`.
- **The Permission Broker is unaffected.** Push, commit, promotion,
  publication, and rollback Permission Broker gates are unchanged and
  do not consume Repository Intelligence context.
- **Runtime remains non-executing.** `State: Observed`, `Maximum
  Capability: observe`, `Execution Availability: unavailable` —
  unchanged by this release; the new acquisition path issues no
  model or network call.
- **Manual `pcae advisory-context build` behavior is unchanged**,
  including its own existing fail-closed semantics for that command's
  direct callers.

### Known, disclosed, non-blocking limitation carried forward (F1)

A foreign Repository Intelligence snapshot placed at the canonical
`.pcae/repository-intelligence` path through a filesystem symlink can
be consumed by this automatic attachment path, the same way the prior
manual context-build path already could. This requires pre-existing
filesystem write access to the target repository's `.pcae` tree, and
is **non-blocking for attachment-only v0.4.2** because the attached
context is informational-only and never influences Advisory authority
output. This must be repaired before any future phase permits
Repository Intelligence to influence actual reasoning output — see the
phase document for full disposition.

## Why v0.4.2, not v0.5.0

The change since `v0.4.1` is patch-level by every criterion this
project's own architecture documentation uses: additive output field,
backward compatible, no authority-model change, no execution-capability
change, no new contract/schema redesign, no true reasoning consumer,
no new CLI conceptual workflow, and independently verified in
`149O.20L.7O.3J.1`. See
`docs/PHASE_149O_20L_7O_3K_POST_RI_ATTACHMENT_ARCHITECTURE_AND_RELEASE_DECISION.md`
for the full version-decision rationale.

## Release engineering

Build infrastructure is unchanged from `v0.4.1`: `[build-system].requires`
remains pinned to `hatchling==1.32.0`; `[tool.hatch.build.targets.sdist]`
`include` patterns remain root-anchored. This release reuses that
exact, previously-verified reproducible-build process without
modification.

## Deferred (explicitly not part of this release)

True RI-backed Advisory reasoning consumption; F1 repository-provenance
/symlink hardening; a 115W contract amendment/extension for
`AdvisoryContextPackage` reasoning integration; a real (non-mock)
`AdvisoryProvider` production connection; Candidate A rollback
readiness/evidence auto-generation/consumption; Candidate B runtime
preflight; HATP/HMIC/Class-B authority activation; CLTR cutover;
runtime execution; model/network expansion.
