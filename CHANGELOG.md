# Changelog

## v0.4.0 — 2026-08-25

- **Phase 149O.20L.7O.3D** — PCAE v0.4.0 Public Release: published under
  explicit human publication authorization. Annotated tag `v0.4.0`
  created and pushed, bound exactly to the frozen release candidate
  `ea3f731ef50ea16985fd4a0562f0c091bb8109b2` (verified local == remote
  == candidate). GitHub Release published at
  https://github.com/atimad/pcae-harness/releases/tag/v0.4.0 with
  hash-verified `pcae_harness-0.4.0-py3-none-any.whl`
  (`sha256:8125d21d...`) and `pcae_harness-0.4.0.tar.gz`
  (`sha256:13492127...`) — both re-verified byte-identical via
  independent clean-clone rebuild and independent download+re-hash of
  the public assets. Independently resolved a real
  arithmetic/categorization error in the 3C.4 report's Fast Green count
  (its "344+2+1=347" breakdown did not match its own "345" total); the
  corrected finding, from direct nodeid inspection, is that the failing
  set is a broader pre-existing self-referential "no drift since my own
  historical candidate SHA" cluster than 3C.4 described, with zero
  nodeids touching the new auto-publish production code — attributable
  regressions remain 0. Ran the Plan B+/corrupt-store/Permission Broker
  behavioral suite (51 tests) against the public wheel's installed code
  (43/51 pass; 8 failures are repo-checkout-dependent AST tests, not
  regressions). Confirmed PyPI **not published**. Runtime unchanged
  (`Observed`/`observe`/`unavailable`).

## Unreleased

- Transitioned active task from Phase 149O.20L.7O.3D: PCAE v0.4.0 Public Release to Idle: awaiting next governed phase (post-149O.20L.7O.3D); session refreshed and governance continuity revalidated.
- Transitioned active task from Phase 149O.20L.7O.3C.4: Connected Capability Release Scope, Version, and Reproducible-Build Hardening to Idle: awaiting next governed phase (post-149O.20L.7O.3C.4); session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3C.4** — Connected Capability Release Scope,
  Version, and Reproducible-Build Hardening: prepared a **release
  candidate — not published** — for **v0.4.0**. Froze the
  independently-verified connected-capability scope (Interactive
  Workflow auto-detect/route, CHGR automatic consumption, Publication
  Execution Ownership auto-invocation, Permission Broker coverage/
  no-bypass, corrupt-store fail-closed isolation) and derived v0.4.0
  from the actual post-v0.3.1 delta (unconditional automatic
  cross-capability orchestration at `pcae phase complete`, not a
  patch-level fix). Found and fixed a real sdist packaging defect:
  unanchored `[tool.hatch.build.targets.sdist].include` globs matched a
  local `.claude/worktrees/<agent-id>/` directory at any depth,
  contaminating the sdist; patterns are now root-anchored.
  `[build-system].requires` pins `hatchling==1.32.0`, verified
  byte-reproducible across two independent clean-clone builds.
  `pyproject.toml`/`src/pcae/__init__.py` bumped `0.3.2` → `0.4.0`. New
  `docs/RELEASE_NOTES_V0_4_0.md`. No tag, GitHub Release, or PyPI
  publication created. Runtime unchanged
  (`Observed`/`observe`/`unavailable`). Recommends
  `149O.20L.7O.3D — PCAE v0.4.0 Public Release` next, gated on explicit
  human authorization before any irreversible publication step.
- Transitioned active task from Phase 149O.20L.7O.3C.3.2: Auto-Publish Corrupt-Store Repair Independent Verification to Idle: awaiting next governed phase (post-149O.20L.7O.3C.3.2); session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3C.3.2** — Auto-Publish Corrupt-Store Repair
  Independent Verification: independently closes finding
  `B-149O.20L.7O.3C.3-1`. Reproduced the historical crash for real from
  the fixed pre-repair commit (`2fd7fe3a`) via a disposable `git
  worktree` and the literal `pcae phase complete` subprocess (uncaught
  `SessionStoreCorruptError`, exit 1); confirmed the same fixture against
  current repaired source completes cleanly (exit 0, disclosed
  `application_error`). 29 fresh, independently-authored tests (no
  fixture/function imported from 3C.3.1's own suite) re-derive the
  unrelated-vs-relevant corruption semantics, the malformed-record/
  filesystem-error matrix, ordering-attack resistance, restart/resume,
  and the Plan B+ happy/rejection paths. Independently re-adjudicated
  duplicate-`subject_ref` from the primary-source contract as
  NON-BLOCKING/ACCEPTED-DEBT (unrepaired, consistent with 3C.3). Recorded
  one documentation-precision finding (not blocking): the repair's
  "unrelated corruption isolation" is, by direct code reading, "a real
  match anywhere always wins; absent that, any corruption anywhere fails
  closed regardless of true relevance" — safe, just more conservative
  than 3C.3.1's own framing implied. Fast Green: 8690 passed / 337 failed
  / 5 skipped / 9 errors, all failures/errors confirmed confined to
  pre-existing, unrelated HATP/HMIC/Class-B/HBDC host-specific suites —
  zero attributable regressions. No production source modified.
  **`B-149O.20L.7O.3C.3-1`: CLOSED.** **PLAN B+ CAPABILITY CONSUMPTION:
  INDEPENDENTLY VERIFIED.** Recommended next phase: 149O.20L.7O.3C.4
  (release scope/version/reproducible-build hardening).
- Transitioned active task from Idle: awaiting next governed phase (post-149O.20L.7O.3C.3.1) to Phase 149O.20L.7O.3C.3.2: Auto-Publish Corrupt-Store Repair Independent Verification; session refreshed and governance continuity revalidated.
- Transitioned active task from Phase 149O.20L.7O.3C.3.1: Auto-Publish Corrupt-Store Fail-Closed Repair to Idle: awaiting next governed phase (post-149O.20L.7O.3C.3.1); session refreshed and governance continuity revalidated.
- Transitioned active task from Idle: awaiting next governed phase (post-149O.20L.7O.3C.3) to Phase 149O.20L.7O.3C.3.1: Auto-Publish Corrupt-Store Fail-Closed Repair; session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3C.3.1** — Auto-Publish Corrupt-Store Fail-Closed
  Repair: repairs BLOCKING finding `B-149O.20L.7O.3C.3-1` (an unrelated,
  corrupt/unreadable Interactive Workflow session file anywhere in the
  store used to crash `pcae phase complete` with an uncaught
  `SessionStoreCorruptError`/`PersistenceUnavailableError`).
  `SessionApplicationService.find_session_by_subject_ref`'s full-scan
  loop now catches and translates per-record corruption instead of
  aborting the scan, keeps scanning deterministically, returns a genuine
  readable match unconditionally when one exists, and raises the
  translated application error (never a silent `None`) when no match
  exists and corruption was encountered; `auto_publish_confirmed_session`
  now wraps the session-lookup call in its existing
  `except ApplicationServiceError` handling. Two production files
  changed. 14 new tests including a mandatory literal subprocess-level
  `pcae phase complete` E2E; 3C.3's own crash-reproduction test updated
  in place to match repaired behavior. Duplicate-`subject_ref` ambiguity
  (3C.3's separate NON-BLOCKING finding) explicitly not repaired, carried
  forward. Status: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT
  CLOSED; recommended next phase is 149O.20L.7O.3C.3.2. Runtime
  unchanged. Release remains STOPPED.
- Transitioned active task from Phase 149O.20L.7O.3C.3: Independent End-to-End Capability Consumption Verification to Idle: awaiting next governed phase (post-149O.20L.7O.3C.3); session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3C.3** — Independent End-to-End Capability
  Consumption Verification: independently re-derived (not trusted)
  Phase 3C.2's Plan B+ governed-capability-consumption batch from
  current source, via direct diff/source reading, live execution of the
  real production service objects (no mocks), a fresh 22-test suite with
  its own fixtures, and repository-wide static re-scans of every
  non-bypass/no-self-CLI/architecture-policy claim. Confirmed: the real
  production entry point, the architecture-policy correction, Permission
  Broker ALLOW/DENY/fail-closed behavior, no-bypass, no self-CLI, human
  authority preservation across all nine non-`Confirmed` session states,
  and Repository Intelligence's deferral. Found one previously
  undisclosed **BLOCKING** defect: `auto_publish_confirmed_session`
  catches only the `ApplicationServiceError` hierarchy, but its
  session-lookup scan can raise `SessionStoreCorruptError`/
  `PersistenceUnavailableError` (a different, uncaught hierarchy) for
  any corrupted/unreadable session file anywhere in the store — even one
  unrelated to the phase being completed — and `run_phase_complete` has
  no exception guard around the call, so this crashes `pcae phase
  complete` for unrelated phases. Reproduced independently twice. Also
  found one NON-BLOCKING finding: duplicate-`subject_ref` sessions
  resolve by latest-`created_at` rather than failing closed. No
  production source modified (verification-only). Recommends a narrow
  repair phase (149O.20L.7O.3C.3.1) before any release-scope work.
- Transitioned active task from Idle: awaiting next governed phase (post-149O.20L.7O.3C.2) to Phase 149O.20L.7O.3C.3: Independent End-to-End Capability Consumption Verification; session refreshed and governance continuity revalidated.
- Transitioned active task from Phase 149O.20L.7O.3C.2: Governed Capability Consumption Integration to Idle: awaiting next governed phase (post-149O.20L.7O.3C.2); session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3C.2** — Governed Capability Consumption
  Integration (Plan B+): Interactive Workflow auto-detect + route,
  Publication Execution Ownership auto-invocation, CHGR downstream
  automatic consumption, and Permission Broker CHGR/publication-path
  gap closure are now production-consumed. New
  `commands/governance_auto_publication.py` auto-routes a `Confirmed`
  Confirmable Decision Session to publication from `pcae phase
  complete`, reusing the existing CLI composition root (no self-CLI
  subprocess). New `mutation_permission.evaluate_publication_permission`
  adapter, consulted from a new `commands/publication_permission_gate.py`
  before `PublicationCoordinator.execute()`, closes the one root/
  external-effect-adjacent action previously outside Permission Broker
  scope; the manual CLI path and the new automatic path both call the
  same gate function (non-bypassable). Mid-phase correction: a first
  draft placed the broker call inside
  `PublicationApplicationService.hand_off()` itself, which the
  repository's own pre-commit `pcae check` architecture-dependency hook
  correctly blocked (`interactive_workflow -> core is not allowed by
  policy`, a frozen Phase 143K boundary) — moved to the `commands` zone
  instead, with zero policy-file changes. Disclosed intentional
  behavior change: publication now requires an active PCAE task,
  mirroring commit/push/promotion's existing invariant. Repository
  Intelligence internal consumption was reconfirmed and **deferred**
  (not the mechanical, low-risk change 3C.1 assessed once `push.py`'s
  actual consumer shape was re-read). 22 new focused tests; a genuine
  `git stash -u` A/B of the full `fast_green` suite found 338
  pre-existing, unattributable failures at phase-entry HEAD (unrelated
  HATP/HMIC/Class-B territory) and zero newly-introduced functional
  failures, after updating five existing test files' fixtures for the
  disclosed behavior change. This phase does not self-certify the
  batch — 149O.20L.7O.3C.3 (independent end-to-end verification) is
  mandatory next. Runtime unchanged (Observed/observe/unavailable).
  Release remains stopped; no version change.
- Transitioned active task from Idle: awaiting human priority decision (post-149O.20L.7O.3C.1) to Phase 149O.20L.7O.3C.2: Governed Capability Consumption Integration; session refreshed and governance continuity revalidated.
- Transitioned active task from Phase 149O.20L.7O.3C.1: PCAE Capability Consumption Integration Assessment and Priority Proposal to Idle: awaiting human priority decision (post-149O.20L.7O.3C.1); session refreshed and governance continuity revalidated.
**Assessment**: Phase 149O.20L.7O.3C.1 stopped the planned v0.3.2
publication (Phase 3D) to assess capability *consumption*, not just
existence. Built a Capability Consumption Graph across all 16 areas
from Phase 3A's audit (30 items): 6 Already Consumed, 1 Partially
Consumed, 3 CLI-only, 10 Unconsumed Internal, 7 Trust-Blocked, 3
Not-Consumable. Headline finding: Interactive Workflow/CHGR — the most
mature governance capability — has zero automatic production callers
into its clean service layer; Repository Intelligence has zero
consumers outside its own CLI; Permission Broker has two small,
concrete gaps (rollback default path, CHGR publication path).
Produced three priority plans for human selection; recommended Plan A
(lowest-risk/fastest) as a starting point with Plan B (CHGR
auto-consumption) as the necessary follow-on. **No integration
implemented, no priority selected — human decision required.** v0.3.2
remains unreleased; the 3D artifact-reproducibility gap (`hatchling`
unpinned) is carried forward unresolved. See
`docs/PHASE_149O_20L_7O_3C_1_PCAE_CAPABILITY_CONSUMPTION_INTEGRATION_ASSESSMENT_AND_PRIORITY_PROPOSAL.md`.
