# Changelog

## Unreleased

- **Phase 149O.20L.7O.3O.1** — PCAE v0.4.3 Public Release
  (publication-only, verification): independently re-verified `3O`'s
  frozen `v0.4.3` candidate (`63580893`) — zero release-facing drift
  since candidate freeze, version confirmed `0.4.3`, `v0.4.2`
  unchanged, frozen wheel/sdist bytes recovered from disk and
  re-hashed exact-match (`sha256:e42ca72c...`/`sha256:8a088983...`),
  fresh wheel/sdist installs both pass version check and golden path,
  rollback-evidence-visibility smoke (dry-run, real-rollback-no-prior-
  dry-run, divergence-block) reproduced identically on the installed
  wheel, regression suites 212/214 passed (2 pre-existing `rg`-tooling
  environment gaps, non-attributable, same as `3O`). BLOCKING = 0,
  MUST-FIX = 0. No explicit human publication authorization was
  present in session, so no tag was created/pushed, no GitHub Release
  was created, no artifact was uploaded. PyPI: NOT PUBLISHED. Phase
  stops at the authorization checkpoint per its own governing brief;
  awaiting human authorization to proceed.
- **Phase 149O.20L.7O.3N.2** — Deep Repository-Wide Capability
  Discovery and Consumption-Gap Audit (read-only, no `src/pcae`
  modified): bottom-up (not architecture-chapter-organized) sweep of
  all 114 `core/*.py` and 60 `commands/*.py` modules (416 `.py` files
  total), triggered by a concern that "prompt writing" might be a
  missed mature capability. Found prompt writing is two distinct
  subsystems: `build_bootstrap_prompt` (`core/context.py`) is real and
  already production-consumed by `pcae session bootstrap`; a separate
  "Phase 45F-45O" prompt-generation/adaptation/validation chain in
  `core/agent.py` is self-declared non-production (hardcoded stale
  data, zero non-CLI callers) and fails the maturity bar for a
  candidate. No other genuine S/M consumption-gap candidate found.
  Mature S/M consumption program **reconfirmed exhausted**, this time
  via bottom-up audit rather than chapter recall, with an explicit
  scope-honesty disclosure of what was and wasn't exhaustively swept.
  Recommends proceeding with `149O.20L.7O.3O.1` (v0.4.3 publication),
  not begun (requires separate human authorization).
- **Phase 149O.20L.7O.3O** — PCAE v0.4.3 Release Hardening: prepared a
  frozen, reproducible `v0.4.3` release candidate (commit `63580893`)
  shipping the human-selected RELEASE NOW decision (`3M`'s rollback
  evidence-visibility change as a narrow patch, unbundled). Version
  bumped to `0.4.3` in `pyproject.toml`/`src/pcae/__init__.py`.
  `docs/RELEASE_NOTES_V0_4_3.md` created (theme: Rollback Evidence
  Visibility; states rollback preparation was already automatic before
  `v0.4.3`). Two independent clean-clone builds produced byte-identical
  wheel/sdist (`sha256:e42ca72c...`/`sha256:8a088983...`). Installed
  both artifacts into fresh venvs (version `0.4.3` confirmed, golden
  path passed). Installed-wheel rollback evidence-visibility smoke
  (dry-run, real ALLOW with no prior dry-run, divergence-block) all
  passed. Fast Green: 0 attributable regressions (PASS verdict); two
  `3M.1` tests blocked only by an environment-only missing `rg` binary,
  manually re-verified and independently confirmed non-attributable.
  BLOCKING = 0, MUST-FIX = 0. Mature S/M consumption program reconfirmed
  exhausted, not reopened. Publication NOT PERFORMED (no tag, no
  release, no upload) — requires separate human authorization.
- **Phase 149O.20L.7O.3M.1** — independently verified the rollback
  preparation/evidence path against fixed pre-`3M` and current trees.
  Confirmed real rollback already computed and consumed `file_plan` and
  live divergence evidence before `3M`, with no manual dry-run
  prerequisite; `3M` changes immediate result/CLI visibility only.
  Verified evidence is mechanically consumed but non-authoritative for
  permission, remains repository-local/current-state-derived, matches the
  persisted RER on every post-evidence terminal outcome, and preserves
  HATP/PB ordering, the explicit human trigger, idempotency, and runtime.
  No distinct AG5 readiness artifact exists; promotion-time persistence
  was correctly rejected as requiring a new freshness/identity/lifecycle
  contract. Added a fresh 26-test verification suite; no production source,
  schema, version, tag, release, or article change. Candidate A is
  reclassified as already functionally complete before `3M`; `3M` adds an
  observability/usability improvement suitable for bundling or a human-
  decided patch release.
- Transitioned active task from Idle: awaiting next governed phase (post-149O.20L.7O.3M) to Phase 149O.20L.7O.3M.1: Independent End-to-End Rollback Readiness / Evidence Consumption Verification; session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3M** — Rollback Readiness / Evidence Automatic
  Consumption Architecture and Integration: re-derived the current
  rollback architecture from source (not inherited summaries) and
  found that the "prepare evidence → consume internally → stop if
  invalid → Permission Broker → effect" automation this phase's brief
  targets was already the exact production behavior of a real (non-
  `--dry-run`) `pcae rollback --per-id X` invocation, released in
  v0.4.1 (`149O.20L.7O.3F`) — `file_plan`/`divergence_check` are
  computed unconditionally regardless of `--dry-run` and already gate
  the divergence short-circuit before either authority gate. No
  existing typed "readiness" concept was found anywhere in `src/pcae`
  (re-confirmed exhaustively); a new one was correctly not invented. A
  materially larger candidate — proactively persisting a readiness
  artifact at `pcae promote`-completion time — was considered and
  rejected as requiring a new freshness/identity contract this phase
  does not have authority to invent (staleness hazard: repository
  state can drift between promotion and an eventual rollback). This
  phase's one narrow, additive production change: surface the
  already-computed, already-consumed, already-persisted evidence
  (`file_plan`/`divergence_check`) directly in every terminal result
  `build_rollback_execution` returns (`src/pcae/core/agent.py`) and
  print it in `pcae rollback`'s human-readable output
  (`src/pcae/commands/agent.py`) — closing the gap where an operator
  previously needed a second command (`pcae rollback-execution show`)
  to see evidence that had already gated their own command's outcome.
  No new type, schema, or persistence added; Permission Broker
  sequencing, HATP isolation, human authority, and runtime
  (`Observed`/`observe`/`unavailable`) all unchanged and independently
  re-verified. New 18-test suite
  (`tests/test_phase_149o_20l_7o_3m_rollback_readiness_evidence_automatic_consumption.py`),
  all passing; rollback/Permission Broker/mutation-permission
  regressions (562 tests combined) and v0.4.2 RI-attachment smoke (46
  tests) all pass unweakened; 0 attributable Fast Green regressions.
  Recommends `149O.20L.7O.3M.1` (independent end-to-end verification),
  not begun.

- **Phase 149O.20L.7O.3L** — PCAE v0.4.2 Release Hardening: prepared a
  frozen, reproducible `v0.4.2` release candidate (commit `bc7935f4`)
  implementing `3K`'s selected Option B (ship `3J`'s attachment-only RI
  integration as a narrow patch). Version bumped to `0.4.2` in
  `pyproject.toml`/`src/pcae/__init__.py`; wrote
  `docs/RELEASE_NOTES_V0_4_2.md` using "AUTOMATIC RI CONTEXT
  ATTACHMENT" terminology and explicitly stating true RI-backed
  Advisory reasoning is not implemented. Two independent clean-clone
  builds (`hatchling==1.32.0`) produced byte-identical wheel and sdist
  (SHA-256 verified, `cmp` byte-for-byte identical); no contamination.
  Installed both artifacts into fresh venvs (version `0.4.2` confirmed,
  CLI functional). Installed-artifact Advisory Mode RI-attachment
  smoke (fresh/missing/malformed/stale snapshot) all passed: automatic
  attachment with no manual `pcae advisory-context build` prerequisite,
  truthful fail-soft, read-only (RI snapshot SHA-256 unchanged before/
  after `pcae advisory check`), and every authority field
  (`broker_decision`/`advisory_decision`/all `would_*`/
  `authorization_granted`/`execution_authorized`) empirically identical
  regardless of RI presence, absence, or validity. `pcae runtime
  inspect` unchanged (`Observed`/`observe`/`unavailable`). 3J's 18-test
  suite and 3J.1's 28-test independent suite both pass unweakened (46/46).
  Fast Green A/B against pre-phase baseline (both runs executed with
  matching cwd/rootdir to avoid a cwd-sensitive-test artifact discovered
  mid-phase): 336 failed/8567 passed/11 skipped/13 errors (baseline) vs.
  335 failed/8568 passed/11 skipped/13 errors (candidate); exactly one
  candidate-only failure, the expected self-referential
  `test_head_equals_origin_main` tripwire (resolves on push, not
  source-caused); zero attributable regressions. F1/F2 carried forward,
  correctly classified non-blocking for attachment-only release.
  BLOCKING = 0, MUST-FIX = 0. No publication performed (no tag, no
  release, no PyPI upload) — human authorization required first.
  Recommends `149O.20L.7O.3L.1` (publication), not begun.
- **Phase 149O.20L.7O.3K** — Post-RI Attachment Architecture and
  Release Decision (decision-only, no `src/pcae` modified). Re-derived
  from current source/contracts, not inherited conclusions, whether
  true RI-backed Advisory reasoning consumption is now safe to build.
  Found: the `AdvisoryProvider`/`AdvisoryContextPackage` framework
  (115P-115Z) remains fully mock-only, disconnected from production —
  zero non-test callers anywhere in `src/pcae`; Phase 122A §3.4 itself
  requires an explicit 115W-contract amendment before Repository
  Intelligence content may occupy an `AdvisoryContextPackage` section,
  so true consumption is architecture/contract-scale work. Effort
  reclassified from 3I's "S" (which scoped only 3J's attachment work)
  to **L**, given the missing contract amendment, the absent real
  (non-mock, non-human-relay) provider, the absent production entry
  point, and the F1 symlink-provenance gap needing repair first.
  Recommends **Option B**: release 3J's already-verified
  attachment-only integration as a narrow patch (`v0.4.2`-plausible)
  with corrected release language, and reprioritize Candidate A
  (rollback readiness/evidence) as the next capability ahead of any
  future true-reasoning-consumption attempt. The 122A-scoped
  reasoning-consumption gap remains open. Human decision required;
  no next phase begun.
- **Phase 149O.20L.7O.3J.1** — Independent End-to-End Repository
  Intelligence / Advisory Consumption Verification (verification-only,
  no `src/pcae` modified). Independently re-derived 3J's claims via
  fresh disposable-repository tests and a new 28-test suite (0 shared
  code with 3J's own tests). Confirmed: automatic consumption with no
  manual CLI prerequisite; read-only acquisition (filesystem hash/mtime
  unchanged); missing/malformed/incompatible-schema/corrupt RI all fail
  soft with distinct, truthful `unavailable_reason`; fail-soft judged
  CORRECT (RI was never a pre-3J Advisory-decision input); authority
  fields (`broker_decision`/`advisory_decision`/`would_*`/
  `authorization_granted`/`execution_authorized`) empirically and
  structurally invariant to RI presence; Permission Broker isolation
  bidirectional; no model/network/runtime expansion; Fast Green A/B: 0
  attributable regressions (336 failed/9 errors/5 skipped identical
  with vs. without this phase's suite; only delta +28 new passing).
  Two non-blocking findings: (1) a foreign RI snapshot at the canonical
  path via symlink is disclosed only as generic staleness once the
  target repo has a commit, undisclosed if it has none; (2) 3J's
  "Advisory production consumption" framing targets `core/advisory.py`
  ("Advisory Mode", no reasoning step) rather than the differently-
  scoped `AdvisoryProvider`/`AdvisoryContextPackage` reasoning
  framework that Phase 122A's architecture named as the intended RI
  consumer (still untouched/mock-only) — RI is genuinely **attached**,
  not **consumed** by reasoning, in the subsystem 3J modified. Zero
  Blocking findings. Recommends `149O.20L.7O.3K`.
- **Phase 149O.20L.7O.3J** — Repository Intelligence → Advisory
  Production Consumption Integration: wired the real production
  Advisory decision path (`core/advisory.py::build_advisory()`, behind
  `pcae advisory check`) to automatically consume the existing
  Repository Intelligence Advisory-context bridge
  (`build_advisory_context()`), previously CLI-only. One production
  file changed. Read-only-query acquisition (`.pcae/repository-
  intelligence/latest.json`, no regeneration); fail-soft for missing/
  invalid/stale RI state; staleness disclosed via the snapshot's own
  recorded commit vs. current HEAD, no new freshness policy invented.
  Structurally non-authoritative: RI context never influences the
  Permission-Broker-derived verdict (test-verified). No model/network
  dependency added; manual `pcae advisory context build` CLI unchanged.
  18 new tests, 0 attributable Fast Green regressions (16 new failures
  are pre-existing "no src/pcae file changed" structural tripwires).
  Runtime unchanged. Recommends `149O.20L.7O.3J.1` independent
  verification, not begun.
- **Phase 149O.20L.7O.3I** — Post-v0.4.1 Deferred Capability
  Consumption Priority Reassessment: read-only strategic reassessment
  of the three deferred mature capability-consumption candidates
  (rollback readiness/evidence auto-generation, runtime preflight
  disclosure, Repository Intelligence + Advisory-context consumption)
  against actual post-v0.4.1 source. Confirmed zero production source
  changes since the `v0.4.1` tag. Revised Candidate C's effort down
  from M/"v0.5.0-scale" to S after verifying its Advisory-context
  bridge (`advisory_context_builder.py`) is already fully built and
  tested, missing only a single caller-side wire from
  `core/advisory.py`'s decision path. Recommended priority: C > A > B.
  No integration implemented, no version changed, no priority selected
  unilaterally — human priority selection required. Runtime unchanged.
- **Phase 149O.20L.7O.3H.1** — PCAE v0.4.1 Public Release: publicly
  released PCAE v0.4.1 under explicit human authorization. Created
  annotated tag `v0.4.1` pinned to release-candidate commit `9869cb65`
  (not `HEAD`), pushed it, created the public GitHub Release
  (`--latest`), and uploaded the exact frozen wheel/sdist (hashes
  recomputed immediately pre-upload; no rebuild at publication time).
  Verified downloaded public assets byte-match the local frozen
  artifacts (filename, size, SHA-256). Independently re-verified the
  frozen `3H` candidate first (3H's own artifact bytes were not
  preserved between phases; rebuilt via two independent clean clones
  and reconfirmed byte-identical to 3H's frozen record); re-ran the
  19-check installed-artifact rollback Permission Broker +
  `HATP_MANDATORY`-isolation + human-trigger smoke suite against both
  the pre-publication and public wheel/sdist installs — 19/19 PASS,
  identically. All source-level regression sweeps (Permission Broker
  broad sweep, Plan B+/corrupt-store, intake/Codex-Ox, 3F/3F.1/AG5/18D
  focused bucket, packaging) matched 3H's documented results exactly.
  `v0.4.0` tag/release/assets confirmed unchanged post-publication.
  Runtime unchanged (`Observed`/`observe`/`unavailable`). PyPI **not
  published**. Article remains stopped. BLOCKING: 0, MUST-FIX: 0.
- **Phase 149O.20L.7O.3H** — PCAE v0.4.1 Release Hardening: prepared a
  frozen, reproducible v0.4.1 release candidate (commit `9869cb65`).
  Version bumped to 0.4.1; release notes written
  (`docs/RELEASE_NOTES_V0_4_1.md`). Two independent clean-clone builds
  produced byte-identical wheel and sdist artifacts using the
  unmodified v0.4.0 reproducible-build process. Clean wheel/sdist
  installs verified (version, CLI, golden path). Installed-artifact
  rollback Permission Broker smoke suite (dry-run/ALLOW/DENY/broker-
  failure/malformed-result/HATP_MANDATORY isolation) passed 15/15 on
  both artifacts. Full Fast Green A/B against an isolated pre-bump
  baseline: zero attributable regressions. v0.4.0 tag/release/assets
  confirmed unchanged. No publication performed; recommends
  149O.20L.7O.3H.1 (publication-only, human-authorization-gated) next.
- **Phase 149O.20L.7O.3G** — Post-Rollback Permission Integration
  Release and Next-Capability Decision: read-only release-scope /
  next-capability decision phase. Confirmed the post-v0.4.0
  production delta is exactly the 3F rollback Permission Broker
  integration (`core/agent.py`, `core/mutation_permission.py`) and
  nothing else; re-verified Permission Broker coverage is complete
  across every currently audited root-mutating command. Freshly
  reassessed Plan A (runtime preflight disclosure, rollback
  readiness/evidence auto-generation) and found neither tightly
  coupled to the shipped rollback integration. Recommended **Option
  A — ship v0.4.1 now**, over Option B (bundle Plan A first) and
  Option C (defer for a larger v0.5.0-scale connected-intelligence
  batch). No production source modified; no version changed; no
  publication performed. Human priority selection required before
  the next phase (release hardening) begins.
- Transitioned active task from Phase 149O.20L.7O.3F.1: Independent End-to-End Rollback Permission-Boundary Verification to Idle: awaiting next governed phase (post-149O.20L.7O.3F.1); session refreshed and governance continuity revalidated.
- **Phase 149O.20L.7O.3F.1** — Independent End-to-End Rollback
  Permission-Boundary Verification: verification-only phase, zero
  Blocking findings. Independently re-derived (fresh source
  reconstruction, fresh 19-test suite, full existing regression
  re-runs, two-sided Fast Green A/B against an isolated pre-3F
  worktree) that 149O.20L.7O.3F's rollback default-path Permission
  Broker gate is genuinely non-bypassable, fail-closed on DENY/
  broker-failure/malformed-result, does not alter runtime capability,
  does not weaken existing policy via its `EXECUTION_CLASS_MUTATION`
  choice, and does not break any consumer of
  `RollbackExecutionRecord.status`. Zero attributable functional
  regressions. No `src/pcae/` file modified. Recommends
  149O.20L.7O.3G next.
