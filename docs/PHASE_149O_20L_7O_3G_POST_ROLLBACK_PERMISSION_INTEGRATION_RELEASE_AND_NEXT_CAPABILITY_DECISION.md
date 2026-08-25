# Phase 149O.20L.7O.3G — Post-Rollback Permission Integration Release and Next-Capability Decision

**Status:** COMPLETE
**Phase type:** READ-ONLY RELEASE-SCOPE / NEXT-CAPABILITY DECISION. No production source, contract, schema, CLI, or packaging-configuration file was modified. No version was changed. No publication occurred.
**Phase-entry commit:** `6363eb0d` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## 1. Objective

Decide, on freshly re-derived evidence (not the condensed phase summaries), whether the independently verified rollback-path Permission Broker integration (149O.20L.7O.3F / 3F.1) should ship immediately as a narrow `v0.4.1` quick release, or be combined first with one or more previously deferred low/medium-risk capability-consumption improvements ("Plan A" from 3E). Do not implement anything. Do not publish. Do not change version.

## 2. Public v0.4.0 baseline

Verified at phase entry:

```
git status --short              => (empty, clean)
git status --branch --short     => ## main...origin/main
git rev-list --count origin/main..HEAD => 0
git rev-parse HEAD               => 6363eb0d012896bf13999fc3ba29bac666c354c0
git rev-parse origin/main        => 6363eb0d012896bf13999fc3ba29bac666c354c0
git rev-parse v0.4.0^{commit}    => ea3f731ef50ea16985fd4a0562f0c091bb8109b2
pcae health                      => healthy
pcae check                       => passed
pcae status coherence            => coherent
pcae doctor task-memory          => warnings only (pre-existing tasks/DONE.md sync-debt, unrelated legacy debt)
pcae push check                  => nothing_to_push
pcae runtime inspect              => Observed / observe / unavailable (unchanged)
pcae notify status                => Telegram configured, enabled, ready
pcae phase-report show --latest  => Phase 149O.20L.7O.3F.1, status completed, report complete
pyproject.toml version            => 0.4.0 (unchanged)
src/pcae/__init__.py __version__  => 0.4.0 (unchanged)
```

`v0.4.0` (`ea3f731e`) remains the public release tag, untouched. HEAD is 24 commits ahead of the tag — all post-release lifecycle (3D publication bookkeeping, 3E reassessment, 3F implementation, 3F.1 verification, and their respective task-lifecycle open/close/report commits).

## 3. Post-v0.4.0 production delta

```
git diff --name-status v0.4.0..HEAD -- src/pcae/
M   src/pcae/core/agent.py
M   src/pcae/core/mutation_permission.py
```

Exactly two production files changed since `v0.4.0`, both from 3F (§20 of the 3F phase doc), zero further `src/pcae/` change from 3F.1 (verification-only, independently re-confirmed via this phase's own re-run of the same diff scope). Full `git diff --stat v0.4.0..HEAD` (24 files, +3298/−279) breaks down as:

| Category | Files | Notes |
|---|---|---|
| Production source | 2 | `core/agent.py`, `core/mutation_permission.py` — the rollback broker adapter and its call site |
| Tests | 3 | 2 new test files (3F's 21 tests, 3F.1's 19 tests); 1 comment-only edit to an existing fixture-sharing file |
| Phase docs | 4 | 3D, 3E, 3F, 3F.1 phase documents (this repository's own audit trail) |
| Lifecycle metadata | 11 | `.pcae/phase-completion-{metadata.json,report.md}`, `tasks/*` (DONE.md, active/done task files) |
| Generated/reporting | 2 | `PROJECT_STATUS.md`, `CHANGELOG.md` |
| RELEASE_NOTES / other | 2 | (3D's own release-notes artifact, already present pre-3E; not part of this delta) |

**Conclusion:** the rollback default-path Permission Broker integration is the only production-behavior change since `v0.4.0`. No other change materially alters product behavior — the remainder is documentation, tests, and lifecycle bookkeeping that ships with every phase regardless of release cadence.

## 4. Permission Broker completeness status

Freshly re-verified this phase (not trusted from 3F/3F.1's own claims):

```
grep -n "evaluate_rollback_permission" src/pcae -r --include="*.py"
  → core/mutation_permission.py:619   (definition)
  → core/agent.py:94356               (sole production call site, inside build_rollback_execution's default-path branch)

grep -rn "create_rollback_approval_decision" src/pcae --include="*.py"
  → core/rollback_approval_evidence.py:924  (definition)
  → core/rollback_approval_evidence.py:1697 (__all__ export)
  → zero production callers (re-confirmed; the carried-forward dead-code finding from 3E/3F/3F.1 is still dead)

grep -rn "PublicationCoordinator().execute\|PublicationCoordinator(root).execute" src/pcae --include="*.py"
  → zero hits outside the governed publish_with_permission_gate path
```

Recheck of the three named consumers:

| Consumer | Permission Broker consumed? | Bypass? |
|---|---|---|
| `pcae push` | YES (`commands/push.py::_evaluate_push_permission`) | None found |
| Publication (`governance-record publish`, auto-publish path) | YES (`publish_with_permission_gate` → `evaluate_publication_permission`) | Dead-code-only (`create_rollback_approval_decision`, zero callers) |
| `pcae rollback` default path | YES (newly, `evaluate_rollback_permission`, single call site) | None found |

No new bypass was discovered. This phase can support the claim:

```
All currently identified real production mutation/effect paths that
should consume Permission Broker now do so.
```

This is scoped to the mutation surface actually audited across 3C.1/3E/3F/3F.1/this phase (push, commit, promotion, alternate-push, publication, rollback default path) — it is **not** a claim that every conceivable future mutation path is covered, and it does not extend to the separate `HATP_MANDATORY`-gated AG3/AG5 evaluation (pre-existing, untouched, trust-blocked from re-audit this phase). Within that audited scope, Option A may be framed as "Permission Broker coverage complete."

## 5. Option A — Ship v0.4.1 now

**Scope:** rollback default-path Permission Broker consumption integration; associated `aborted_permission_denied` fail-closed terminal-state support. No additional capability integrations.

**Semantic fit (v0.4.1 patch-level questions):**

- Backward compatible? Yes — ALLOW preserves prior behavior exactly; only a previously-unguarded path now gates.
- Narrow governance hardening? Yes — one adapter, one call site, reusing an existing pattern (§6 of 3F).
- No new user-facing conceptual workflow? Confirmed — `pcae rollback --per-id X` syntax and semantics are unchanged; only a denial outcome (rare, POL-001-triggered) is new.
- No authority model change? Confirmed — human trigger (`--per-id`) unchanged, HATP_MANDATORY branch byte-identical.
- No execution capability increase? Confirmed — runtime independently reverified unchanged (Observed/observe/unavailable) before/after an ALLOW rollback (3F.1 §23).
- No new contract/schema? Confirmed — reuses existing `ACTION_ROLLBACK`/`EXECUTION_CLASS_MUTATION` vocabulary, existing `_RER_VALID_STATUSES` frozenset extension mechanism (precedented by `aborted_hatp_mandatory_denied`).
- No major CLI redesign? Confirmed — zero CLI surface change.

All six questions favor patch-level classification. **v0.4.1 is a strong candidate on semantic-versioning grounds alone.**

**User value of shipping now:** centralized rollback permission enforcement; fail-closed behavior on DENY/broker-failure/malformed-result; consistent Permission Broker coverage across all root-mutating effect paths (push, commit, promotion, publication, rollback); a completed, closed-out governance-coverage narrative that is independently verifiable by anyone inspecting the public release. This is real, externally observable governance value — not internal-only refactoring — because it changes the actual security posture of a real user-facing command (`pcae rollback`) in a way documented in release notes and testable by a user (attempt a rollback with no active task and observe the new fail-closed denial instead of silent unguarded execution).

**Risk of waiting:** `v0.4.0` remains public without rollback default-path broker coverage for as long as release is deferred; the unreleased `main` branch already contains materially stronger governance guarantees than the latest stable release, which is itself a governance-transparency gap (the repository's own documented security posture and its shipped artifact diverge). Any further batching (Plan A or Plan C) reopens scope and pushes the release date out by at least one additional bounded implementation + independent-verification cycle (per this repository's own established two-phase discipline, e.g. 3F→3F.1), with attendant verification burden compounding rather than simply adding.

## 6. Option B — Add Plan A before release

**Candidate scope from 3E:** (1) runtime preflight disclosure / capability-aware preflight; (2) rollback readiness/evidence auto-generation.

See §8/§9/§10 below for fresh reassessment of both against the current, post-3F state. **Conclusion reached in §11: neither candidate is tightly coupled to the rollback broker integration, both are independently deliverable at any later time, and bundling either would add a full implementation + independent-verification cycle without closing any prerequisite the shipped integration currently lacks.** Option B is evaluated as a coherent but non-preferred path.

## 7. Option C — Defer quick release and move to larger connected-intelligence work

**Potential future scope:** Repository Intelligence internal consumption; Advisory-Context wiring (Plan C from 3E).

No fresh deep re-audit was performed this phase (per the governing instruction, §13); this phase relies on 3E's fresh-as-of-3E classification, cross-checked only for whether anything since 3E changed its inputs. `git diff --name-status v0.4.0..HEAD -- src/pcae/repository_intelligence/ src/pcae/advisory/` (re-run this phase) shows zero changes to either subsystem since `v0.4.0` — 3E's classification (Effort M, Authority risk LOW, likely `v0.5.0`-scale) has no evidence of having become stale. Classified likely **v0.5.0-scale**, per 3E §20/§23. Not implemented, not deeply re-investigated.

## 8. Runtime preflight reassessment

Re-checked against current (post-3F) source, not merely restated from 3E:

- `grep -rl "runtime_registry\|RuntimeRegistry" src/pcae` (re-run): same consumer set as 3E found — `cli.py`, `core/runtime_context.py`, `core/runtime_introspection.py`, `core/runtime_snapshot.py`, `core/phase_reports.py` (reporting), `core/evidence_providers.py` (evidence enrichment), `commands/runtime_inspect.py`, `commands/agent.py` (CLI wiring). No `*preflight*.py` module imports the registry (re-grepped, zero hits, unchanged from 3E).
- The rollback default-path gate added by 3F does **not** consume runtime state at all — `evaluate_rollback_permission`'s request construction (mutation_permission.py:619) references no runtime/registry symbol; confirmed by direct read this phase.
- 3F.1 independently proved permission and runtime capability are orthogonal (§23: "permission != capability, independently reverified") — the newly-shipped gate neither needs nor benefits from runtime preflight disclosure to function correctly.
- The registry remains architecturally empty (0 plugins) — unchanged since 3E; a preflight check today can only disclose "unavailable" truthfully, not route among real options.

**Exact consumer:** none current — no workflow (rollback or otherwise) requires runtime capability information to make its current decision.
**Missing edge:** unchanged from 3E — a `registry_health()`/`list_plugins()` call inside a `*preflight*.py` module, which does not exist.
**Effort:** S (unchanged from 3E — reuses existing pure metadata queries).
**Authority risk:** LOW (informational only; unchanged from 3E).
**User benefit:** low and untargeted — there is no current workflow whose behavior this would change; it would add disclosure text a human does not currently need to see inline, since `pcae runtime inspect` already answers the same question on demand.

**Classification: deprioritize.** No meaningful current consumer exists; this candidate's value is unchanged from 3E and is not increased by the rollback integration having shipped.

## 9. Rollback readiness/evidence reassessment

Reconstructed the current rollback flow after broker integration (fresh read of `build_rollback_execution` at current HEAD):

```
pcae rollback --per-id X [--dry-run]
  → PER/ECP lookup, eligibility, divergence checks   [unchanged]
  → dry_run? → return (readiness/evidence preview, zero mutation, zero broker call)  [unchanged by 3F]
  → RER created; divergence blocking? → return        [unchanged]
  → HATP_MANDATORY? → evaluate_for_real_effect()       [unchanged]
  → else → evaluate_rollback_permission()               [NEW, 3F]
       → ALLOW → restore/remove loop
       → DENY/failure → aborted_permission_denied, zero mutation
```

The operator still must manually invoke `pcae rollback --per-id X --dry-run` to obtain readiness/evidence before any real rollback — this is unchanged by 3F/3F.1; the broker gate sits strictly after the dry-run early-return (3F §15, re-confirmed this phase by direct read: the dry-run branch returns before reaching either the `HATP_MANDATORY` check or the new gate). No automatic generation at promotion time exists.

**Can PCAE safely auto-generate/consume this without changing rollback authority or execution semantics?** Yes, architecturally, exactly as 3E concluded (§9 of 3E) — `build_rollback_execution(..., dry_run=True)` is already the safe, read-only mechanism; no new execution surface would be created, and this phase's fresh read confirms nothing about the 3F/3F.1 diff altered that dry-run branch's position or behavior.

**Exact missing edge:** a promotion-completion hook (in `pcae promote`'s completion path) that invokes the existing dry-run code path and persists its output alongside the ECP/PER record. This edge is unrelated to the rollback default-path broker gate — it triggers off promotion completion, not off rollback dispatch.
**Current manual choreography:** operator cold-starts `pcae rollback --per-id X --dry-run` only after a promotion later needs reversing.
**Target automatic behavior:** `pcae promote` auto-generates and stores dry-run rollback readiness/evidence at promotion time, informational and non-blocking.
**Effort:** S-M (unchanged from 3E).
**Failure semantics:** generation failure must not block promotion completion — fail-soft, matching the existing `auto_publish_confirmed_session` non-blocking precedent.
**Idempotency:** regenerable without side effect (dry-run, no persisted mutation to the rollback target itself).
**Authority risk:** LOW (dry-run only, no execution implication — unchanged from 3E).

**Classification:** unchanged real candidate, but its trigger point (promotion completion) and value proposition (pre-staging evidence for a possible future rollback) are entirely independent of whether the rollback dispatch path itself is broker-gated.

## 10. Coupling analysis

**Rollback readiness/evidence ↔ rollback broker integration:** NOT tightly coupled. The readiness/evidence candidate's trigger is promotion completion; the broker integration's effect is on rollback dispatch. 3E's own dependency graph (§16 of 3E) already classified these as "independent (pairs naturally with, but does not require...)" — this phase's fresh re-derivation reaches the same conclusion via direct code inspection, not by trusting 3E's prior text. Thematically related (both concern "rollback"), but delivering one does not simplify, require, or unblock the other. Per §16 of the governing instruction ("if tightly coupled and small: Option B becomes stronger; if independent: do not delay v0.4.1 merely to bundle it"), this favors **not bundling**.

**Runtime preflight ↔ rollback path:** NOT required or useful. §8 above and 3F.1 §23 both independently confirm the rollback path (broker-gated or not) functions correctly and completely without any runtime-capability information; runtime remains `unavailable` throughout, and rollback semantics do not reference it. Per §12 of the governing instruction, this favors **not bundling merely for thematic completeness**.

**Conclusion:** neither Plan A item is a small, tightly-coupled prerequisite the shipped rollback integration is missing. Both are freestanding capabilities that happen to share a topical label ("rollback") with 3F/3F.1's work without sharing an implementation dependency.

## 11. Release-size comparison

| Option | Scope | Risk | Effort | Verification burden | User value | Likely version |
|---|---|---|---|---|---|---|
| A: immediate v0.4.1 | Rollback broker gap closure only (already implemented + independently verified) | LOW (already verified, zero further change) | None remaining (release-hardening only) | Release-hardening pass only (reuse v0.4.0 process) | Real, immediate, externally observable governance-completeness gain | v0.4.1 |
| B: add Plan A first | + runtime preflight disclosure (S) + rollback readiness/evidence auto-gen (S-M) | LOW authority risk per item, but adds a full new bounded-implementation + independent-verification cycle before any release | S + S-M (aggregate S-M, per 3E §18) | New E2E verification phase(s) required (3C.3-style precedent) before release | Marginal — preflight has no current consumer (§8); readiness/evidence has real but conditional value (§9), unrelated to what's already shipped | v0.4.1 (if kept small) or v0.5.0 (if framed as a batch) |
| C: wait for connected-intelligence batch | RI→push/phase + Advisory-Context wiring | LOW authority risk but materially larger scope, new internal architecture (snapshot freshness policy) not yet designed | M (revised up from 3C.1's S-M by 3E §5) | Full batch-level E2E verification, new fail-soft/staleness test category | Real but not needed to realize the rollback gain already achieved | v0.5.0 |

## 12. Decision matrix

| Criterion | Option A: v0.4.1 now | Option B: Plan A first | Option C: broader batch |
|---|---|---|---|
| Standalone user value | High — closes last broker gap, real fail-closed behavior change | Marginal incremental value over A (preflight: none; readiness/evidence: conditional) | High long-term, but does not depend on shipping now |
| Governance value | Completes Permission Broker coverage across all audited root-mutating commands | Same as A plus informational disclosure/evidence pre-staging | Adds a different kind of value (informational context), not governance-boundary coverage |
| Product risk | None remaining — change already independently verified, zero attributable regressions | None per-item, but release delay itself is a risk (v0.4.0 stays weaker than main) | Same, magnified by longer delay |
| Implementation effort | Zero (done) | S-M aggregate, not yet started | M, not yet started |
| Authority risk | None remaining (verified MODERATE-then-cleared by 3F/3F.1) | LOW per item | LOW |
| Release delay | None | At least one bounded implementation + independent-verification cycle | At least one larger implementation + independent-verification cycle, plus new architecture design (snapshot freshness) |
| E2E verification burden | Already discharged (3F + 3F.1) | New, batch-level (3C.3-precedent) required before release | New, larger, with a new test category (fail-soft/staleness) required |
| Semantic version | v0.4.1 (patch — see §5) | v0.4.1 (if scoped tightly) or v0.5.0 (if framed as a batch) | v0.5.0 |
| Strategic coherence | Clean, bounded, closes a well-defined finish line (100% broker coverage) | Coherent but bundles two thematically-labeled, mechanically-independent capabilities into one release for no coupling reason | Coherent as the next big step, but not a reason to hold back an already-finished, already-verified improvement |

## 13. Semantic-version analysis

Per §5's six-question test, the shipped delta is unambiguously patch-level: backward compatible, no new conceptual workflow, no authority-model change, no execution-capability increase, no new contract/schema, no CLI redesign. **v0.4.1** is the correct classification for Option A. Option B could remain v0.4.1 if scoped tightly (both Plan A items are also individually patch-level per the same six questions — informational/evidence-only, no new conceptual workflow), but 3E itself flagged that bundling multiple capabilities under one narrative could motivate a v0.5.0 framing; this phase does not need to resolve that hypothetical since Option B is not selected. Option C is v0.5.0 — it introduces new internal architecture (snapshot freshness/auto-regeneration policy) absent from v0.4.0, which is a materially larger scope than a patch.

## 14. Build/release implications

`v0.4.0`'s bound/reproducible build infrastructure was verified unchanged this phase: `git diff --name-status v0.4.0..HEAD` shows no touch to `pyproject.toml`, packaging configuration, or the reproducible-build hardening introduced in `149O.20L.7O.3C.4`. Not modified in this phase. If Option A is selected (as recommended, §15), the next phase (release hardening for v0.4.1) should reuse the exact `v0.4.0` release build process without modification, consistent with the governing instruction's §19.

## 15. Recommended option

**RECOMMENDED: OPTION A — SHIP v0.4.1**

**Rationale:** The rollback default-path Permission Broker integration is independently verified (3F.1, zero Blocking findings), patch-level by every semantic-versioning criterion (§5, §13), and closes the final identified production-coverage gap across the entire audited root-mutation surface (§4). Neither Plan A candidate is a small, tightly-coupled prerequisite this integration is missing (§10) — both are freestanding, and bundling either would add a full bounded-implementation-plus-independent-verification cycle for marginal or currently-nonexistent user value (§8, §9) while leaving `v0.4.0` publicly weaker than `main` for longer with no offsetting benefit. Plan C is out of scope by its own effort/architecture-maturity profile (§7, §11) and does not meet the high bar §17 of the governing instruction sets for deferring an already-finished improvement.

## 16. Human decision requirement

Per the governing instruction (§27), immediate `v0.4.1` being recommended does **not** authorize starting release hardening automatically.

```text
HUMAN PRIORITY SELECTION REQUIRED
```

The human must explicitly select before any next phase begins:

- Authorize Option A: begin **149O.20L.7O.3H — v0.4.1 Release Hardening** (reusing the v0.4.0 release build process, per §14), OR
- Authorize Option B: begin the smallest bounded Plan A integration phase (runtime preflight disclosure and/or rollback readiness/evidence auto-generation), followed by mandatory independent E2E verification, then release hardening, OR
- Authorize Option C: begin larger connected-intelligence integration planning/implementation instead, OR
- Select a different next step not enumerated above.

## 17. Exact next phase per option

- **If Option A selected:** next phase is release hardening for `v0.4.1` (reusing the `v0.4.0` release build process, §14/§19).
- **If Option B selected:** next phase is the smallest bounded integration phase for the selected Plan A subset, followed by mandatory independent E2E verification, then release hardening.
- **If Option C selected:** next phase is larger connected-intelligence integration planning/implementation (RI→push/phase wiring and/or Advisory-Context wiring).

None of these next phases were begun in 3G.

## 18. Deferred work

Unchanged from 3E, not implemented or newly investigated in this phase beyond the fresh reassessment in §8/§9: runtime preflight disclosure (Plan A), rollback readiness/evidence auto-generation (Plan A), Repository Intelligence → push/phase wiring (Plan C), Advisory-Context → Advisory core wiring (Plan C), Runtime Enforcement consumption (trust-blocked, §10 of 3E, not reopened this phase).

## 19. No-Go confirmations

No production source file was modified this phase. No Permission Broker policy was invented or altered. No version was changed — `pyproject.toml`/`src/pcae/__init__.py` remain at `0.4.0`, `v0.4.0` tag (`ea3f731e`) untouched. No publication occurred. No tag was created. No artifact was uploaded. No build tooling was modified. No rollback authority was altered. No runtime execution capability was enabled — `Observed/observe/unavailable` unchanged throughout (re-verified via `pcae runtime inspect` at phase entry and this section). No HATP/HMIC/Class-B authority was touched or re-audited. No CLTR cutover occurred. No backend/model execution was added. No Dell host was mutated. No inspection of `~/repos/pcae-deepseek-research` occurred. The article remains STOPPED — not read, not modified, not published.

## 20. Testing

Read-only decision phase. Evidence gathered via: `git status`/`git log`/`git rev-parse`/`git diff --name-status`/`git diff --stat` (read-only); `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report show --latest` (all read-only, side-effect-free); direct reads of `docs/PHASE_149O_20L_7O_3F_*.md`, `docs/PHASE_149O_20L_7O_3E_*.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `pyproject.toml`, `src/pcae/__init__.py`; targeted `grep -rn`/`grep -rl` re-verification of every consumer/bypass claim against current HEAD (not trusted from prior phase reports without re-checking). No broad regression suite (`pytest -m fast_green`) was run — not needed to resolve any uncertainty in this decision, per the governing instruction's §20.

## 21. Verdict

```text
POST-ROLLBACK RELEASE DECISION:
COMPLETE

PUBLIC BASELINE:
v0.4.0

ROLLBACK PERMISSION BROKER INTEGRATION:
INDEPENDENTLY VERIFIED

PERMISSION BROKER PRODUCTION COVERAGE:
COMPLETE ACROSS ALL CURRENTLY AUDITED ROOT-MUTATING COMMANDS
(push, commit, promotion, alternate-push, publication, rollback
default path) -- not a claim beyond this audited scope; HATP_MANDATORY
path remains separately and independently gated, untouched.

OPTION A:
v0.4.1 now -- patch-level, zero remaining implementation, real
governance-completeness gain, no coupled prerequisite missing.

OPTION B:
Plan A first -- coherent but not coupled; adds a full
implementation + independent-verification cycle for marginal or
currently-nonexistent value.

OPTION C:
Broader connected-intelligence batch -- v0.5.0-scale, not
release-worthy immediately given Option A's real standalone value.

RECOMMENDED:
OPTION A -- SHIP v0.4.1

RECOMMENDED VERSION:
v0.4.1

IMPLEMENTATION:
NOT STARTED

PUBLICATION:
NOT PERFORMED

RUNTIME:
Observed / observe / unavailable

ARTICLE:
STOPPED
```

Stop after 3G. Do not begin the selected next phase automatically.
