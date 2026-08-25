# Changelog

## Unreleased

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
