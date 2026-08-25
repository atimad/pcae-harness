# Changelog

## Unreleased

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
