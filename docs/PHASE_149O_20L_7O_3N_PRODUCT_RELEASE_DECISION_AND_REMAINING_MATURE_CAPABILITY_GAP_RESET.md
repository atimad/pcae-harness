# Phase 149O.20L.7O.3N — Product/Release Decision and Remaining Mature Capability Gap Reset

**Status:** READ-ONLY DECISION PHASE — COMPLETE. NO `src/pcae` MODIFIED.

## Objective

Make two decisions without implementing either: (1) whether the 3M rollback-evidence-visibility
delta should ship as `v0.4.3`, be bundled with the next capability, or be deferred/reverted; and
(2) reconstruct, from current source, which already-built PCAE capability has a real remaining
production-consumption gap, replacing the historical candidate ranking with one grounded in
post-v0.4.2 state (Plan B+ orchestration connected, Permission Broker rollback-path complete, RI
attached-but-not-reasoning, rollback evidence already automatic).

## v0.4.2 Baseline

- Tag `v0.4.2` = `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`.
- Current baseline check (this phase, pre-work): `git status --short` clean; `origin/main..HEAD` =
  0; `HEAD` = `origin/main` = `5daf5ae386a8f1080178e367e05647ee0e2a4332`.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent.
- `pcae runtime inspect`: `Runtime state: Observed`, `Execution capability: unavailable`,
  `Maximum plugin capability: observe`, `Registry status: empty`, `Plugin count: 0` — unchanged.
- `pcae doctor task-memory`: pre-existing warnings only (stale `tasks/done/` entries not listed in
  `tasks/DONE.md`, spanning phases back to 149O.1H) — historical debt, not caused by or related to
  3M/3N.
- `pcae push check`: nothing to push (mode `nothing_to_push`).

## Post-v0.4.2 Delta (v0.4.2..HEAD)

`git diff --name-status v0.4.2..HEAD`: 33 files changed, all from phases 3L, 3L.1, 3M, 3M.1.
Category split:

- **Product behavior (`src/pcae`):** exactly 2 files —
  `src/pcae/core/agent.py` (+23/-0) and `src/pcae/commands/agent.py` (+13/-0). Both are 3M's
  evidence-visibility change.
- **Tests:** `tests/test_phase_149o_20l_7o_3m_rollback_readiness_evidence_automatic_consumption.py`
  (349 lines), `tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py`
  (632 lines).
- **Docs:** 3 new phase documents (3L, 3M, 3M.1), `RELEASE_NOTES_V0_4_2.md` header fix.
- **Phase lifecycle / status metadata:** `.pcae/phase-completion-metadata.json`,
  `.pcae/phase-completion-report.md`, `.pcae/fast-green-attribution/*` (6 new artifacts),
  `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DECISIONS.md`, `tasks/DONE.md`,
  `tasks/active/*`, `tasks/done/*` (task-lifecycle churn across 3L→3M.1).

**A hypothetical `v0.4.3` would contain exactly one product change: the 3M evidence-visibility
patch to `core/agent.py`/`commands/agent.py`.** No other production behavior has changed since
`v0.4.2` shipped.

## 3M / 3M.1 Corrected Interpretation (independently re-confirmed from primary diff evidence)

Read directly from `git diff v0.4.2..HEAD -- src/pcae/core/agent.py`:

- `file_plan` and `divergence = _rer_check_divergence(...)` are computed **unconditionally**,
  before the `if dry_run:` branch, for every non-early-error invocation of
  `build_rollback_execution`.
- `divergence` already gates the divergence-conflict short-circuit (pre-existing code, untouched
  by 3M).
- 3M's only change: assemble `_evidence_summary = {"file_plan": file_plan, "divergence_check":
  divergence}` and splice it (`**_evidence_summary`) into terminal result dicts that previously
  omitted it, plus one non-dry-run branch gaining an explicit `"file_plan": file_plan` key.
- `src/pcae/commands/agent.py`'s diff is two additive `print()` statements guarded by
  `if result.get(...) is not None`, mirroring the pre-existing `--dry-run` branch's presentation.

This independently reconfirms the corrected characterization the phase brief supplied:

| Aspect | Status |
|---|---|
| Rollback preparation/evidence computation | Already automatic pre-3M |
| Rollback evidence internal consumption (gates divergence short-circuit) | Already present pre-3M |
| 3M change | Evidence visibility / immediate result surfacing only |
| New authoritative readiness type/artifact/state/cache | Not implemented, not justified |

No further investigation was needed to override this characterization — the diff is unambiguous
and matches `PROJECT_STATUS.md`'s own 3M/3M.1 entries verbatim in substance.

## 3M Standalone Product Value

| Capability | Pre-3M | Post-3M | Actual user benefit |
|---|---|---|---|
| file-plan computation | Automatic, unconditional | Unchanged | None (no behavior change) |
| divergence computation | Automatic, unconditional | Unchanged | None |
| internal evidence consumption | Already gates short-circuit | Unchanged | None |
| dry-run requirement | Not required (confirmed by 3M.1) | Unchanged | None |
| CLI evidence visibility | Required a second command (`rollback-execution show`) | Printed inline on the same invocation | Saves one follow-up command per rollback attempt |
| terminal result visibility | Evidence sometimes absent from returned dict | Evidence present on all post-evidence terminal paths | Programmatic callers of `build_rollback_execution` no longer need a second lookup |
| permission behavior | Permission Broker sequencing unchanged | Unchanged | None |
| authority behavior | HATP isolation unchanged | Unchanged | None |

Classification: **OBSERVABILITY / DEBUGGABILITY**. Not governance (no new boundary), not
automation (nothing new is computed), not a UX redesign (same commands, same flags, additive
output only).

## Release-Worthiness Scoring (3M delta)

| Criterion | Score (1-5) | Basis |
|---|---|---|
| Standalone user value | 2 | Saves one follow-up CLI call; no new capability |
| Governance value | 1 | No new boundary, gate, or authority change |
| Autonomy increase | 1 | Nothing newly automated — same automatic computation as before |
| Release urgency | 1 | No bug fixed, no compatibility break, no security implication |
| Regression risk | 1 (low risk) | Purely additive dict keys / print lines; 42/44 targeted tests pass (2 failures are environmental — missing `rg` binary, not code regressions) |
| Release overhead | 3 | Tagging, changelog, release notes, GitHub Release process for a 36-line diff, so soon after `v0.4.2` |

## Release Option A — Ship v0.4.3 now

Rationale for: independently verified (3M.1), backward-compatible, small/low-risk, genuinely
useful for a rollback operator's day-to-day loop.

Downside: standalone delta is 36 lines of additive printing across two files with zero new
governance surface. Shipping a patch release for output-formatting alone, one release after
`v0.4.2`, sets an aggressive release-cadence precedent for changes with no new consumption
boundary. Semantic fit for a version bump is weak — this is closer to a changelog line than a
release.

**Assessment: semantically thin justification for a standalone release.**

## Release Option B — Bundle with next meaningful capability

Leaving `main` one small, independently-verified commit ahead of `v0.4.2` is safe: `git status`
clean, no compatibility risk, no authority change, Fast Green attribution evidence already
recorded for the change. Likely delay is bounded by however long the next capability phase takes
(historically S/M-effort phases in this track have landed in 1-3 sub-phases). Bundling produces a
clearer release narrative ("v0.4.3: rollback evidence visibility + <next capability>" reads as one
coherent operator-facing improvement) rather than two near-back-to-back patch releases for
increasingly thin deltas. The next capability, once selected, can be independently verified the
same way 3M was (a `.1` verification sub-phase), preserving the established governance rhythm.

**This is the default recommendation given 3M's LOW standalone release value (Section:
Release-Worthiness Scoring).**

## Release Option C — Revert/defer

Not warranted: the change causes no confusion (it mirrors the existing `--dry-run` branch's
presentation format), has clear if modest value, adds no compatibility burden (additive keys
only, no schema change), and does not materially expand output beyond what an operator already
had to fetch via a second command. Per the phase brief, C should not be selected merely to keep
releases tidy, and no evidence here supports selecting it on the merits either.

**Assessment: Option C rejected.**

## Current Consumption Baseline (post-v0.4.2)

Established from `pcae runtime inspect`, prior verified phases (3F, 3J/3J.1, 3K, 3M/3M.1), and
direct source checks this phase:

- Plan B+ governance orchestration: connected (per phase-brief premise, consistent with
  `pcae phase-report show --latest`'s completed-phase list including the full orchestration
  architecture tracks).
- Permission Broker: complete across currently audited root-mutating paths, including the
  rollback default path (3F, re-confirmed unchanged by 3M/3M.1's diffs — no `permission_broker`
  reference touched).
- Repository Intelligence: automatically attached to Advisory Mode output (`core/advisory.py`,
  3J/3J.1) — genuinely read-only, non-authoritative, structurally isolated from
  `broker_decision`/`advisory_decision`. True reasoning consumption (the `AdvisoryProvider`/
  `AdvisoryContextPackage` framework named in Phase 122A §3.4) remains mock-only/disconnected,
  requiring an explicit 115W contract amendment (3K finding, not re-litigated here — no source
  change since 3K to revisit it).
- Rollback preparation/evidence: already automatic pre-3M (independently re-confirmed above).
- Runtime static facts: already consumed at session bootstrap, phase-report generation, and
  finalization (3I finding); registry remains architecturally empty (0 plugins) — confirmed live
  via `pcae runtime inspect` this phase (`Registry status: empty`, `Plugin count: 0`).

## Already-Closed Gaps (excluded from candidate queue)

| Capability | Status | Evidence |
|---|---|---|
| Interactive Workflow / CHGR | Production-consumed, auto-routed | Historical 3A/3B verification (full create→publish CLI sequence exercised from a wheel install); no source change since to reopen |
| Publication Execution Ownership | Production-consumed | Named-complete in `pcae phase-report show --latest`'s architecture-status list (144A-144J); no contrary evidence found |
| Permission Broker | Currently audited root-mutating paths covered | 3F rollback integration + re-confirmed untouched by 3M/3M.1 |
| Rollback preparation/evidence | Already automatic pre-3M | This phase's own diff re-derivation |
| Runtime static facts | Already consumed where currently meaningful | 3I finding, unchanged |

No duplicate integration proposed for any of these.

## Runtime Enforcement

Historical grade (3A): F — "zero consumers, design-only." `pcae runtime inspect` this phase
confirms the registry is still empty by architecture (`Registry status: empty`, `Plugin count:
0`), consistent with 3I's finding that non-consumption is intentional because execution capability
remains `unavailable`. No safe non-effectful consumption opportunity was identified beyond what
3I already assessed (three real workflows already consume static facts).

**Classification: INTENTIONALLY DEFERRED UNTIL EXECUTION.** Not a candidate.

## Shell Gate

Historical grade (3A): F for enforcement (simulation-only, no interception hook), D for its audit
corpus. No source evidence found this phase that this has changed — Shell Gate is not referenced
in any 3F-3M diff or phase summary. Automatic consumption would mean moving from simulation to
enforcement, which is an authority/enforcement change explicitly out of scope for a quick
integration.

**Classification: TRUST BLOCK / intentionally deferred.** Not a candidate; remains disabled per
No-Go.

## Advisory Governance Framework

The Advisory Governance Pilot/Operational Adoption/Certification track (138-142) is listed
complete in the architecture-status ledger. Distinct from RI reasoning (3K), this is the
policy/certification framework itself. No fresh evidence this phase locates a bounded,
non-model, non-authority consumer edge still missing — this would require a dedicated read of the
138-142 phase set beyond this phase's budget.

**Classification: NOT INDEPENDENTLY RE-VERIFIED THIS PHASE — carried forward as an open question,
not scored as a candidate** (criterion 21 requires an exact identifiable missing edge; none was
established with confidence here).

## Repository Decision / Explainability

The Repository Decision & Explainability Framework (115A-115Z) is listed complete. 3K confirms
`advisory_repository_skills.py`/`advisory_context_package.py` remain mock-only/disconnected — but
that is the RI-reasoning framework, a different component. Whether the Decision/Explainability
framework itself (review/promotion/advisory/mutation consumers) has a real bounded consumer beyond
its own CLI/query surfaces was not independently re-derived this phase (would require dedicated
source reading of `src/pcae` decision-record/review modules).

**Classification: NOT INDEPENDENTLY RE-VERIFIED THIS PHASE.**

## RI Sub-Capabilities (Historical Memory, Dependency Graph, Change Impact, Cross-Artifact, Unified Query)

Per the phase brief's own instruction (Section 15) and the 3A historical grade (C/F,
"self-labeled prototypes," consumed only through RI's own query/context surface), these are not
separately listed as distinct gaps. No source evidence this phase shows they have become
independently disconnected from the RI query/context path that 3J/3J.1 verified.

**Classification: NO GAP (subsumed under RI attachment, already assessed under 3K/3J.1).**

## Rollback Residual Gaps

Beyond the file_plan/divergence evidence (now surfaced by 3M), `src/pcae/commands/agent.py`
already exposes `run_rollback_execution_show`, `run_rollback_execution_list`, and
`run_rollback_execution_mark_interrupted` — i.e., rollback history/status/recovery-state
consumption already exists as production CLI surfaces (confirmed via `grep` this phase). No
evidence of a manual-orchestration-only reconciliation/recovery subsystem was found.

**Classification: NO GAP** beyond what 3M closed (visibility) and what already exists (history/
list/mark-interrupted).

## Authority / CLTR

Historical grade (3A): G — "migration unstarted," `pcae cltr migration status` self-reports
`production_authority: "legacy"`. `pcae authority inspect` is production-exposed as advanced
CLTR-tooling documentation (3A/3B), i.e., the underlying authority-evaluation service (aesic →
decision-session, graded A/B in 3A) is already consumed while the CLTR migration/cutover itself
remains deliberately deferred. This phase does not treat cutover as a quick-integration candidate,
per instructions.

**Classification: TRUST BLOCK on cutover; underlying service already consumed.**

## HATP / HMIC / Class-B

No prerequisite change since 149O.20L.7O.2N.2 (last verified narrow repair) or 3K's own
Advisory-track findings. Remains trust-blocked (hardware-credential/Trust-Enrollment territory,
historically graded F/E in 3A for production-reachable paths).

**Classification: TRUST BLOCK.** Not ranked highly despite implementation maturity, per
instructions.

## Backend / Provider

`pcae runtime inspect` confirms `Registry status: empty`, `Execution capability: unavailable` —
architecturally empty by design, consistent with 3A's F grade for execution across every provider
(signed non-executing proof, not merely unconfigured). No non-execution provider capability was
identified as mature-and-disconnected this phase; per instructions, execution/provider
integration is out of scope regardless.

**Classification: NO GAP eligible for this phase's candidate criteria** (any real integration here
would touch execution activation, explicitly No-Go).

## Audit / Explainability Consumption

Audit/evidence persistence is graded A in the 3A historical audit (released). Whether audit
evidence is produced-but-not-surfaced at additional lifecycle boundaries the way rollback evidence
was pre-3M was not independently re-derived this phase (would require a dedicated read of audit
persistence call sites analogous to the `build_rollback_execution` trace done for 3M). Flagged as
the **closest analog to another 3M-style visibility phase**, but not confirmed as a live gap.

**Classification: UNVERIFIED — potential OUTPUT/VISIBILITY GAP, not confirmed.**

## Consumption-vs-Visibility Classification Summary

| Capability | Classification |
|---|---|
| Rollback evidence (pre-3M) | NO GAP (was already TRUE CONSUMPTION, just OUTPUT/VISIBILITY GAP, now closed by 3M) |
| RI → Advisory attachment | NO GAP (attachment complete); RI → Advisory **reasoning** = CONTRACT GAP (115W amendment needed) + effort L |
| Permission Broker (rollback path) | NO GAP |
| Runtime Enforcement | AUTHORITY/ENFORCEMENT GAP, intentionally deferred (TRUST BLOCK pending execution capability) |
| Shell Gate | AUTHORITY/ENFORCEMENT GAP, TRUST BLOCK |
| CLTR cutover | AUTHORITY/ENFORCEMENT GAP, TRUST BLOCK (underlying service already consumed) |
| HATP/HMIC/Class-B | TRUST BLOCK |
| Backend/provider execution | TRUST BLOCK (execution activation, out of scope) |
| Advisory Governance Framework consumer edge | UNVERIFIED this phase |
| Repository Decision/Explainability consumer edge | UNVERIFIED this phase |
| Audit/explainability surfacing | UNVERIFIED this phase — potential OUTPUT/VISIBILITY GAP |
| RI sub-capabilities (Historical Memory, etc.) | NO GAP (subsumed under RI query/context) |

## Current Maturity Matrix

| Capability | Implemented | Verified | Exposed | Production-consumed | Auto-orchestrated | Remaining gap type | Candidate? |
|---|---|---|---|---|---|---|---|
| Rollback evidence (file_plan/divergence) | Yes | Yes (3M.1) | Yes (post-3M) | Yes | Yes | NO GAP | No |
| RI → Advisory attachment | Yes | Yes (3J.1) | Yes | Yes | Yes | NO GAP | No |
| RI → Advisory reasoning (122A) | No (mock-only) | N/A | No | No | No | CONTRACT GAP | No (effort L, needs 115W amendment) |
| Permission Broker (rollback) | Yes | Yes | Yes | Yes | Yes | NO GAP | No |
| Runtime Enforcement Coordinator | Yes (design) | Historical only | Partial | No | No | AUTHORITY/ENFORCEMENT GAP | No (trust-blocked) |
| Shell Gate | Yes (simulation) | Historical only | Partial | Simulation only | No | AUTHORITY/ENFORCEMENT GAP | No (trust-blocked) |
| CLTR / Authority Evaluation service | Yes | Yes | Yes (`authority inspect`) | Yes (underlying service) | Cutover: No | AUTHORITY/ENFORCEMENT GAP (cutover only) | No |
| HATP/HMIC/Class-B | Yes | Partial | Partial | No (production-reachable path absent) | No | TRUST BLOCK | No |
| Backend/provider execution | Yes (proven non-executing) | Yes | No | No | No | TRUST BLOCK | No |
| Advisory Governance Framework | Yes | Historical | Yes | Unverified this phase | Unverified | UNVERIFIED | Not scored |
| Repository Decision/Explainability | Yes | Historical | Yes (query/CLI) | Unverified this phase | Unverified | UNVERIFIED | Not scored |
| Audit/explainability lifecycle surfacing | Yes | Historical | Yes (own commands) | Partial | Unverified | UNVERIFIED / possible visibility gap | Not scored |
| Interactive Workflow / CHGR | Yes | Yes | Yes | Yes | Yes | NO GAP | No |
| Publication Execution Ownership | Yes | Yes | Yes | Yes | Yes | NO GAP | No |
| RI sub-capabilities (Historical Memory etc.) | Yes | Yes | Partial | Via RI query only | Via RI query only | NO GAP | No |

## Missing-Edge Matrix

| Capability | Production owner | Current consumer | Expected consumer | Exact missing edge | Effort | Authority risk |
|---|---|---|---|---|---|---|
| RI → Advisory reasoning | `advisory_repository_skills.py` / `advisory_context_package.py` | None (test-only) | `core/advisory.py` reasoning step (currently none exists) | 115W contract amendment + real provider + F1 provenance repair | L | Medium (new reasoning-influencing surface) |
| Advisory Governance Framework bounded consumer | 138-142 framework modules | Unverified | Unverified | Requires dedicated source audit before an edge can be named | Unknown | Unknown — not enough evidence to score |
| Repository Decision/Explainability bounded consumer | 115A-115Z modules | Own query/CLI surfaces | Unverified whether any lifecycle boundary (review/promotion) already calls it | Requires dedicated source audit | Unknown | Unknown |
| Audit/explainability lifecycle surfacing | Audit persistence layer | Own commands (`audit`, `audit-show`, etc.) | Possible: session bootstrap / phase-report / finalization (analogous to runtime static facts) | Requires dedicated call-site trace analogous to 3M's `build_rollback_execution` re-derivation | S-M (if confirmed) | Low (would mirror 3M's pattern: visibility, non-authoritative) |
| Runtime Enforcement execution | Coordinator (design-only) | None | N/A while execution unavailable | Execution capability activation | Out of scope | High — explicitly No-Go |
| Shell Gate enforcement | Simulation/audit corpus | Audit only | N/A | Interception hook + enforcement mode | Out of scope | High — explicitly No-Go |
| CLTR cutover | Legacy authority path | aesic → decision-session (already consumed) | Full migration | Migration execution, not incremental wiring | Out of scope for "quick integration" | High — explicitly deferred |

No entry in this matrix satisfies all of criterion 21 (implemented + verified + real consumer +
exact missing edge + no new authority + no execution activation + S/M effort + independently
E2E testable) with currently available evidence. The **audit/explainability lifecycle surfacing**
row is the closest analog to 3M's pattern but requires a dedicated investigation phase before it
can be scored as a genuine candidate — it is not yet confirmed to have a missing edge at all.

## Candidate Ranking

No item in this phase's investigation met the full candidate bar (criterion 21) with confirmed
evidence. The strongest *unconfirmed* lead is audit/explainability lifecycle surfacing (potential
S-M, low authority risk, 3M-pattern-analogous) — it is not scored because its missing edge is not
yet established, only suspected.

| Rank | Candidate | User value | Governance value | Autonomy gain | Maturity | Effort | Authority safety | E2E testable | Release differentiation |
|---|---|---|---|---|---|---|---|---|---|
| — | (none confirmed) | — | — | — | — | — | — | — | — |

**No NO-GAP items are scored, per instructions.**

## Plan A — Quickest genuine consumption gain

**No confirmed S/M consumption-gap candidate exists as of this phase.** The nearest lead
(audit/explainability lifecycle surfacing) requires its own investigation phase
(149O.20L.7O.3N.1-style, source-tracing audit call sites the way 3M/3M.1 traced rollback evidence)
before it can be selected or rejected with confidence.

## Plan B — Highest governance value below execution activation

No confirmed candidate below execution activation was established this phase with a named exact
edge. Advisory Governance Framework and Repository Decision/Explainability both remain
UNVERIFIED — either could plausibly hold a governance-value candidate, but neither was traced to
an exact missing edge here.

## Plan C — Larger strategic capability

RI → Advisory true reasoning consumption (122A-scoped) remains the largest strategically important
item, but is explicitly CONTRACT GAP + effort L, requiring the 115W contract amendment, a real
provider, and F1 provenance hardening before it is safe. Not a quick-integration candidate; would
require its own architecture phase, as 3K already concluded and this phase found no new evidence
to revise.

## Release / Roadmap Paths

- **Path 1 (release v0.4.3 now → next capability):** Available but weakly justified — Option A's
  scoring (Section: Release-Worthiness) shows low urgency/value for a standalone release.
- **Path 2 (bundle 3M with next capability → next release):** **Recommended default**, consistent
  with Option B's assessment above, since no next capability has yet been selected or verified.
- **Path 3 (no worthwhile mature integration remains → architecture/new-capability work):**
  Partially applicable — no confirmed quick-integration candidate exists, but this phase could not
  fully rule out audit/explainability, Advisory Governance Framework, or Repository
  Decision/Explainability as sources of a genuine quick gap; those require a follow-up
  investigation phase, not immediately jumping to large architecture work.

## Fast Green Infrastructure Debt

Carried forward, unrepaired: the state-sensitive pushed-status / fixed-commit `git diff`
self-check issue documented across prior phases (fixed-commit diffs necessarily fire "0 files
changed" false positives for any legitimate source-modifying phase; pushed_status field requires
hand-syncing across three artifacts). No new instance encountered this phase (read-only, no
commits requiring fast_green attribution beyond phase-lifecycle bookkeeping).

**Classification: NON-BLOCKING INFRASTRUCTURE DEBT.** No evidence this phase elevates it — does
not warrant a dedicated hardening phase ahead of capability work, but remains a candidate for one
eventually.

## Task-Memory Historical Debt

`pcae doctor task-memory` reports numerous pre-existing warnings (`tasks/done/` entries not listed
in `tasks/DONE.md`, spanning back to 149O.1H). Not repaired in 3N per instructions. Recorded here
for visibility; a dedicated task-lifecycle-hardening phase would be the appropriate venue.

## Recommendation

**RECOMMENDED IMMEDIATE ACTION: BUNDLE 3M WITH NEXT GENUINE CAPABILITY** (Path 2). 3M's standalone
release value is LOW (Section: Release-Worthiness Scoring); no confirmed quick-integration
capability candidate currently exists to bundle it with. The most responsible next step is a
narrow follow-up investigation phase (analogous to 3I/3M's re-derivation method) tracing audit/
explainability lifecycle surfacing, Advisory Governance Framework consumer edges, and Repository
Decision/Explainability consumer edges to either confirm a genuine S/M consumption-gap candidate
or rule them out — **not** proceeding directly to the RI-reasoning contract-scale work (Plan C),
which remains L-effort and contract-blocked.

## Human Decision Required

1. **Release action:** confirm Path 2 (bundle) vs. Path 1 (ship v0.4.3 now) vs. some other
   sequencing.
2. **Next-phase selection:** authorize a narrow read-only investigation phase into
   audit/explainability, Advisory Governance Framework, and Repository Decision/Explainability
   consumer edges (this phase's top lead), or direct a different next step (e.g., proceed directly
   to the RI-reasoning contract-scale work despite its L effort, or select something else
   entirely).
3. No phase has been started to act on either decision; `HUMAN PRIORITY/RELEASE SELECTION
   REQUIRED`.
