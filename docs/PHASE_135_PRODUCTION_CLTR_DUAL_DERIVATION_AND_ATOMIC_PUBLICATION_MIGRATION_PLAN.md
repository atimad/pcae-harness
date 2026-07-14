# Phase 135M — Production CLTR Dual-Derivation and Atomic Publication Contract / Migration Plan

**Phase classification:** architecture, contract, migration planning, cutover-readiness definition.
**Not:** implementation, dual-derivation activation, atomic-publication implementation, authority cutover, legacy-authority demotion, legacy-authority retirement.

**Binding semantic authority:** CLTR-001 v1.0 (frozen, 135B; verified 135C, 135D, 135G).
**Production wire contract:** CLTR-SCHEMA-001 v1.0.1 (frozen 135I; amended 135J).
**Latest completed phase:** 135L — Production CLTR Shadow Integration Independent Verification (VERIFIED WITH NON-BLOCKING FINDINGS; zero Blocking findings; commits `5f1234f968f3a3e50ae490229430ea3c20f6df5d`, `977bb1436f73e0ce263d2715335a6fe088cb9a2c`).

No production lifecycle behavior changes in this phase. This document defines the safe path from verified shadow observation to eventual legacy authority retirement; it does not walk that path.

---

## 1. Executive summary

Track 135 has frozen a semantic contract (CLTR-001 v1.0), a wire contract (CLTR-SCHEMA-001 v1.0.1), and a verified, non-authoritative shadow production integration (135K, independently verified by 135L) that observes every one of the four production finalization entry points without altering their outcome, blocking their completion, or claiming conformance it cannot verify. Legacy lifecycle derivation — the canonical phase report, completion metadata, Architecture Status, checkpoint, marker, and receipt mechanisms already in production — remains the sole lifecycle authority today, exactly as it was before Track 135 began.

135M is the phase that must answer the question 135L explicitly deferred: *what is the governed, single-authority path from here to a state where one atomic publication transaction produces both the legacy representations and the canonical CLTR record, and eventually a state where CLTR alone is authoritative and legacy derivation is retired?* This document freezes that path as a contract — terminology, an explicit authority-stage model, entry/exit gates per stage, a shared dual-derivation input contract, a comparison contract, an atomic-publication target design, a rollback/roll-forward architecture, a feature-flag and cutover-approval model, and a staged implementation sequence — without implementing any of it.

135M dispositions all four 135L Non-Blocking findings explicitly (§4), all four inherited 135K limitations, and all four inherited 135J Non-Blocking findings, reclassifying any of them that become authority-relevant to a specific migration stage as a Blocking prerequisite for that stage (not for today).

**Conclusion:** This document freezes a complete, internally consistent, single-authority migration contract with no unresolved Blocking gap for the planning phase itself. It recommends **135N — Production CLTR Dual-Derivation and Migration Contract Verification** as the next phase, which must independently re-derive and verify this contract before any dual-derivation implementation begins (§56).

---

## 2. Migration objective

Move, over multiple independently governed phases, from:

```
Legacy production lifecycle derivation
        +
Verified non-authoritative shadow CLTR   (current state, post-135L)
```

toward:

```
Dual deterministic derivation
        ↓
Cross-derivation comparison
        ↓
One atomic lifecycle publication transaction
        ↓
Staged CLTR authority adoption
        ↓
Legacy authority demotion
        ↓
Legacy authority retirement
```

while preserving the core architectural principle established in 135A and never weakened since (135A §1; CLTR-001 §4.1): **one governed lifecycle transition → one canonical transition authority → one atomic publication boundary → many deterministic derived representations.** During migration, two derivation paths may temporarily coexist for comparison. Dual derivation must never become dual authority: at every migration stage defined in §6, exactly one component is the lifecycle authority, and every other representation — including CLTR itself, until Stage 3 — is explicitly derivative, observational, or comparison evidence.

This document is the contract and plan. It is not the implementation.

---

## 3. Current verified starting state

Confirmed by direct inspection during this phase (§ Initial Inspection results, reproduced here as of 2026-07-14):

- Repository clean; `origin/main..HEAD` = 0 at phase start.
- `pcae health`: healthy. `pcae check`: passed. `pcae doctor task-memory`: two pre-existing warnings (135L's own `tasks/done/` entries not yet listed in `tasks/DONE.md` — a bookkeeping gap this phase closes in §"Governance results", not a CLTR defect). `pcae push check`: clean, `nothing_to_push`, `Lifecycle review: missing` (advisory field, not itself a CLTR finding). `pcae runtime inspect`: Runtime state Observed, maximum capability observe, execution capability unavailable, Permission Broker `execution_unavailable`.
- Telegram: configured, enabled, outbound-only, `notify_default: disabled`, `notify_enabled: True` — dispatch occurs only through `pcae phase complete` under governed finalization, not automatically.
- `pcae phase-report reconcile --phase-id 135L`: `Status: reconciled`, `Promoted generations: 1`, `Marker: already_dispatched`, `Checkpoint: completed`, `Receipt: finalized`, `Mutation: none (inspection only)` — 135L's own finalization is confirmed sound and closed; no repair required.
- `CLTR-SCHEMA-001` remains v1.0.1. `CLTR-001` remains v1.0. Shadow CLTR remains non-authoritative. `PCAE_CLTR_SHADOW_ENABLED` remains the only CLTR-related flag in production, default unset/false (135K §17).
- No active governed phase prior to this one; the idle placeholder task (`20260714-0837-idle-awaiting-next-governed-phase`) is the task this phase supersedes.

135M performed no repair to `src/pcae/cltr`, `src/pcae/core/finalization_transaction.py`, or any other production source or production test file. All governance commands used in this phase were read-only (`pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report show --latest`, `pcae phase-report reconcile --phase-id 135L`).

---

## 4. Exact 135L Non-Blocking finding dispositions

Each of 135L's four Non-Blocking findings (`docs/PHASE_135_PRODUCTION_CLTR_SHADOW_INTEGRATION_INDEPENDENT_VERIFICATION.md` §45) is dispositioned individually below. None is silently carried forward undispositioned; each disposition below is binding on the phases named.

### F-135L-1 — `InvariantContext` live-comparison fields declared but unused

- **Exact description (verbatim):** "`InvariantContext`'s `live_repository_identity`/`live_branch_identity`/`live_repository_clean`/`live_head_revision` fields are declared but never populated (always default `InvariantContext()`) or read by any of the 37 evaluators — dead parameter threading, no evaluator branches on it."
- **Affected component:** `src/pcae/cltr/invariants.py`.
- **Current operational risk:** none observed. No evaluator conditions on these fields, so their emptiness cannot cause a false `pass`, `fail`, or `conformant` result today; the risk is purely that a future author might assume they are wired when they are not.
- **Affects dual derivation?** Yes — Stage 1 (§6) requires live repository/branch/revision facts to be part of the shared explicit transition-input package (§8), which is the correct place to populate these fields for the first time, not a direct write into `InvariantContext` from a second, independently reconstructed source.
- **Affects mismatch classification?** No, not directly — it affects an invariant evaluation input, not a comparison-result class.
- **Affects atomic publication?** No.
- **Affects authority cutover?** Indirectly — an invariant evaluator that silently ignores live repository/branch/revision facts cannot be relied upon as an authority-relevant check at Stage 3, so this must be resolved before Stage 3 begins, not merely before shadow observation continues.
- **Required disposition:** must resolve before dual-derivation implementation (Stage 1). The shared input assembler (§9) is the only permitted source for these values; `InvariantContext` must be populated from the assembled input package, never from an evaluator-local reconstruction.
- **Planned phase for resolution:** 135O (Shared Transition Input and Dual-Derivation Implementation).
- **Acceptance evidence:** a 135P (independent verification) test demonstrating that at least one of the 37 invariants exercises these fields against a shared input package value, and that a deliberately wrong value fails closed (does not silently pass).
- **Classification:** *may remain during shadow-only continued observation but must resolve before dual-derivation implementation begins* (Stage 1 entry gate, §7).

### F-135L-2 — unwired `adapter_sources` and `transition_id == phase_id` correction containment

- **Exact description (verbatim):** "The one real production call site never passes `adapter_sources`, so 11/15 representation adapters resolve `unverifiable` (never a false conformant) on every real production invocation today; separately, `transition_id == phase_id` means a same-phase content correction (e.g. partial→success reconciliation) is contained as `publish_failed` rather than published, silently discarding the corrected shadow observation (fails closed, no corruption)."
- **Affected component:** `src/pcae/cltr/adapters.py`, `src/pcae/cltr/persistence.py`, `src/pcae/core/finalization_transaction.py` wiring.
- **Current operational risk:** none for correctness (fails closed both ways: `unverifiable` is honest, and a discarded correction is a lost observation, not a corrupted one). Operational cost: shadow evidence today under-covers 11 of 15 representation kinds and cannot yet observe same-phase re-finalization (e.g. partial→success recovery) at all.
- **Affects dual derivation?** Yes, directly and centrally. Stage 1 (§6) requires real comparison sources wired for all 15 kinds (per CLTR-SCHEMA-001 §21.4's already-frozen per-kind mode assignment) as an entry condition, and requires an explicit decision on `transition_id` identity (§8, §17) before dual derivation can produce meaningful comparison evidence rather than 11/15 `unverifiable` results.
- **Affects mismatch classification?** Yes — until wired, most comparison result classes (§12) other than `unverifiable` cannot occur for 11 of 15 kinds, which would bias evidence collection (§15) toward the four kinds that already resolve.
- **Affects atomic publication?** Yes — the `transition_id == phase_id` identity collapse is exactly the split-brain risk category addressed in §17 and §19: a same-phase correction must be a *new* transition identity in the shared input package (§8), not a silent identity reuse that a persistence layer must awkwardly contain.
- **Affects authority cutover?** Yes — Stage 3 cannot begin while any representation kind's adapter is structurally unwired; §7's Stage 3 entry gate requires evidence across all 15 kinds.
- **Required disposition:** must resolve before dual-derivation implementation (Stage 1) for adapter wiring; the `transition_id` identity question must be resolved as part of the shared input contract (§8) before Stage 1 begins, since Stage 1's evidence quality depends on it.
- **Planned phase for resolution:** 135O for adapter wiring and `transition_id` identity design; 135N (this contract's own verification phase) must first confirm the identity design proposed in §8.3 is sound before 135O implements it.
- **Acceptance evidence:** a 135P test suite demonstrating live comparison sources produce a non-`unverifiable` result for at least one instance of each of the 15 representation kinds under a deterministic fixture, and a same-phase correction (partial→success) produces two distinct transition identities with two distinct, non-colliding shadow generations.
- **Classification:** *must resolve before dual-derivation implementation.*

### F-135L-3 — 135K's own re-promoted report causing a reconciliation conflict

- **Exact description (verbatim):** "135K's promoted canonical report was re-promoted under the same `phase_id` by a later closure-documentation bookkeeping task, producing a `phase_name` display anomaly and a genuine `pcae phase-report reconcile` conflict (checkpoint/marker digest mismatch against the newest promoted generation)."
- **Affected component:** PFR/task-lifecycle tooling (`phase_reports.py`) — explicitly outside `src/pcae/cltr`.
- **Current operational risk:** cosmetic/reconciliation-only; does not affect CLTR shadow correctness, does not affect any of the four entry points' finalization behavior. 135L declined to repair this because doing so would have required touching production reports/checkpoints/markers, which was outside 135L's shadow-only boundary.
- **Affects dual derivation?** No — this is a legacy bookkeeping tooling gap (re-promotion under an identical `phase_id` by a follow-on task), not a CLTR representation defect.
- **Affects mismatch classification?** No.
- **Affects atomic publication?** Indirectly informative — it is a concrete, already-observed instance of the exact "same generation identity re-published by an unrelated later action" hazard that §18 (publication pointer contract) and §19 (split-brain prevention) must guard against for the *future* atomic generation, even though today's occurrence is in legacy tooling, not CLTR.
- **Affects authority cutover?** No direct effect, but it is instructive precedent: any future closure-documentation task that touches a promoted generation after the fact must be prohibited once CLTR generations are the atomic publication target (§16).
- **Required disposition:** *accepted long-term limitation, tracked as separate governance follow-up, not 135M/135N/135O scope.* It is explicitly out of migration-contract scope because it is a legacy-tooling defect, not a CLTR-authority defect.
- **Planned phase for resolution:** unscheduled; recommended as an independent governance-hygiene phase outside Track 135's dual-derivation sequence, as 135L itself recommended.
- **Acceptance evidence:** not applicable to Track 135's migration sequence; whichever future phase addresses it should demonstrate `pcae phase-report reconcile` returns `reconciled` for the affected historical phase without rewriting history.
- **Classification:** *accepted long-term limitation* (explicitly not reclassified as migration-Blocking, because it does not touch CLTR authority, dual derivation, comparison, or publication).

### F-135L-4 — placeholder `repository_identity`/`branch_identity` in production wiring

- **Exact description (verbatim):** "`repository_identity`/`branch_identity` in the one real production call site are set to `phase_id`/the literal `\"main\"` rather than actually-observed repository/branch values."
- **Affected component:** `src/pcae/cltr` production wiring (`src/pcae/core/finalization_transaction.py`).
- **Current operational risk:** none today — no downstream conformance decision currently depends on these two fields' real-world accuracy, per 135L's own finding text.
- **Affects dual derivation?** Yes — the shared input contract (§8) requires "same source revision," "same explicit commit ownership," and by extension the same actually-observed repository/branch identity, consumed by both derivation paths from one assembled package (§9), not hardcoded per call site.
- **Affects mismatch classification?** Not today (no comparison currently keys on these fields with real variation), but it would become authority-relevant the moment any comparison result class depends on repository/branch identity matching (e.g., a future multi-repository or multi-branch deployment).
- **Affects atomic publication?** No direct effect for a single-repository, single-branch deployment; would become relevant if the deployment topology changes.
- **Affects authority cutover?** Must be resolved before Stage 3, because CLTR becoming sole lifecycle authority means its recorded repository/branch identity must be actually observed, not asserted.
- **Required disposition:** *may remain during dual derivation but must resolve before cutover.* Placeholder values are acceptable for shadow and Stage 1/Stage 2 rehearsal (where legacy remains authoritative and CLTR's own identity fields are not yet load-bearing), but must be replaced with the shared input assembler's actually-observed values (§9) no later than the Stage 3 contract phase (135S).
- **Planned phase for resolution:** 135O may wire real values opportunistically as part of the shared input assembler; 135S (Stage 3 contract freeze) must gate on it explicitly regardless.
- **Acceptance evidence:** a 135T (Stage 3 verification) test confirming `repository_identity`/`branch_identity` in a produced CLTR record match `git remote get-url origin` / current branch at assembly time, not a literal or the `phase_id`.
- **Classification:** *may remain during dual derivation but must resolve before cutover.*

### Summary table

| Finding | Component | Dual-derivation impact | Cutover impact | Disposition | Resolution phase |
|---|---|---|---|---|---|
| F-135L-1 | `invariants.py` | Yes (input source) | Yes | Must resolve before dual-derivation implementation | 135O / 135P |
| F-135L-2 | `adapters.py`, `persistence.py`, wiring | Yes (central) | Yes | Must resolve before dual-derivation implementation | 135N (identity design) → 135O / 135P |
| F-135L-3 | `phase_reports.py` (non-CLTR) | No | No (precedent only) | Accepted long-term limitation | Unscheduled, out of Track 135 |
| F-135L-4 | `finalization_transaction.py` wiring | Yes (input completeness) | Yes | May remain through dual derivation; must resolve before cutover | 135O (opportunistic) / 135S (gated) |

No finding is silently carried forward. F-135L-1, F-135L-2, and F-135L-4 are each reclassified above from "Non-Blocking (135L shadow scope)" to "Blocking for a named future migration stage" — exactly the reclassification this phase's instructions require for any finding that becomes authority-relevant to the migration design.

### Inherited 135K limitations (six items disclosed, four identified as primary per 135K §26) — disposition

1. **Single-snapshot construction** (one terminal shadow record per transition, not a full spine progression) — *must resolve before dual-derivation implementation*: Stage 1 requires deriving CLTR outputs from the same explicit inputs the legacy path consumes at each governed step, which for a terminal-snapshot model means the "transition" observed is the whole finalization, not sub-steps; this is compatible with Stage 1 as designed (§6) provided the shared input package (§8) itself carries enough state to reconstruct the full spine deterministically if a later stage requires it. No change required for 135M; flagged for 135O design attention.
2. **Adapters run without live comparison sources** — identical to F-135L-2 above; same disposition.
3. **`metadata_digest`/`snapshot_digest` reuse `finalization_snapshot_id`** — *may remain during dual derivation but must resolve before cutover*: Stage 1/Stage 2 comparison can still classify results using this reused identity as long as the reuse is disclosed (as it already is, per-record, in `limitations`); an independent completion-metadata digest is required no later than Stage 3 so that the "completion metadata" and "immutable snapshot" representation kinds are genuinely independently verifiable, not the same value duplicated under two field names.
4. **Commit ownership always `unverifiable`** — inherited from 135J's F5; *must resolve before dual-derivation implementation* becomes authority-relevant, because the shared input contract (§8) explicitly requires "same explicit commit ownership" as a mandatory input every governed transition must supply, and an always-`unverifiable` commit-ownership adapter cannot support that requirement once dual derivation depends on it for comparison (§12). Resolution requires the three-outcome commit-verification model CLTR-001 §10.3/135A §8.2 already call for and 135I/135J/135K all correctly deferred as a production gap, not a CLTR-shadow defect. Planned for 135O, verified in 135P.
5. **No multi-generation supersession exercised** — *may remain through initial cutover*: Stage 2 rehearsal is the first stage that requires exercising `successor_transition_id`/`overlay_flags` under realistic conditions; it need not be exercised earlier.
6. **Reconciliation and adapter live-wiring deferred as "natural next-phase work"** — subsumed by items 2 and 4 above; 135K's own text already anticipated this document's scope.

### Inherited 135J Non-Blocking findings (F2–F5) — disposition

- **F2** (wrong section-number citations within 135I's own text) — *accepted long-term limitation*: a documentation citation-precision defect, not an authority or content-availability defect; corrected opportunistically if 135I is ever re-issued, never migration-Blocking.
- **F3** (`delivery_recorded_bookkeeping_incomplete` undefined in prose though unambiguous in code) — *may remain through initial cutover*: the value's operational meaning is unambiguous in `phase_reports.py:443`; a prose definition should be added to CLTR-001 or CLTR-SCHEMA-001 as editorial hygiene before Stage 3's contract freeze (135S), since Stage 3 requires reconciliation-outcome semantics to be fully self-documenting, not merely correct in code.
- **F4** (37-invariant crosswalk not enumerated in one consolidated table) — *may remain through initial cutover*, same reasoning as F3; full enumeration is useful editorial hygiene for 135S but does not block any evidence-bearing activity before then.
- **F5** (three-outcome commit-ownership model and atomic `latest.*` publication both unimplemented) — *must resolve before dual-derivation implementation* for the commit-ownership half (identical to 135K limitation 4 above); the atomic `latest.*` publication half is *the exact subject of §16–§19 of this document* and is scheduled for 135Q (Atomic Publication Rehearsal Implementation), not 135O.

No finding from 135J or 135K is silently dropped; each has an explicit classification and a named phase above.

---

## 5. Migration terminology

The following definitions are frozen for this contract and all phases it plans (135N onward). A term not listed here retains its CLTR-001 or CLTR-SCHEMA-001 meaning unchanged. Ambiguous terms ("primary," "current," "canonical") are avoided below except where explicitly qualified.

- **Shadow derivation** — a CLTR derivation that runs after and independent of the authoritative outcome, observes it, produces its own record, and can neither block, alter, nor be consulted by the authoritative path. This is the 135K/135L state today.
- **Dual derivation** — two derivations (legacy and CLTR) each independently computed from one shared explicit transition-input package (§8), running for comparison purposes, with exactly one of the two holding lifecycle authority at any given time per the authority-stage model (§6).
- **Authoritative derivation** — whichever derivation path is designated, at the current authority epoch (§40), as the sole source of lifecycle truth. Never more than one derivation is authoritative at a time.
- **Legacy derivation** — the pre-Track-135 production derivation path: canonical phase report generation, completion metadata, Architecture Status, checkpoint, marker, receipt, and the finalization transaction's own promotion/dispatch logic, as it exists prior to any CLTR authority cutover.
- **CLTR derivation** — the `src/pcae/cltr` package's construction of a Canonical Lifecycle Transition Record conforming to CLTR-SCHEMA-001, from either shadow observation (today) or shared explicit input (Stage 1+).
- **Comparison** — the deterministic, adapter-driven (CLTR-SCHEMA-001 §21) act of evaluating whether the legacy derivation's output and the CLTR derivation's output agree on a normalized semantic field, producing exactly one result class from §12.
- **Match** — a comparison outcome in which the compared field is judged equivalent under its assigned `adapter_comparison_mode` (§12: `exact_match` or `semantic_match`).
- **Mismatch** — a comparison outcome in which the compared field is judged non-equivalent under its assigned mode (§12: any `*_mismatch` class).
- **Unverifiable** — a comparison outcome in which no comparison could be performed because a required input, adapter wiring, or comparison source was absent, distinct from both match and mismatch, and never silently upgraded to either (CLTR-SCHEMA-001 §21.2).
- **Divergence** — the general condition of legacy and CLTR derivations disagreeing on any authority-relevant fact, encompassing all non-`unverifiable` mismatch classes; used when discussing the phenomenon, not a specific result class.
- **Cutover** — the governed, operator-approved (§41) act of changing the authority epoch (§40) such that CLTR becomes the sole lifecycle authority for new transitions (entry into Stage 3, §6).
- **Rollback** — a governed act of reverting the authority epoch to a prior value (typically returning legacy to authoritative status) in response to migration evidence, never rewriting history (§38).
- **Demotion** — the governed act of removing a legacy representation's status as an independent lifecycle-fact source while it continues to exist as a deterministic derivative, per legacy source per §36 criteria. Demotion is per-fact, not per-file (135H §2).
- **Retirement** — the governed act of removing a legacy derivation path's independent computation entirely, leaving only compatibility-only historical reads, per §37 criteria. Stronger evidence than demotion; no legacy authority is retired in this phase or its immediately following phases.
- **Atomic publication** — the local-filesystem-atomic act of publishing one complete generation (§20) containing every locally-includable artifact for one governed transition, via a single pointer replacement (§22).
- **Publication transaction** — the full candidate-preparation-through-publication sequence (§25) that produces one atomic publication.
- **Migration epoch** — a stable identifier distinguishing separate migration attempts, contract-version changes, or resumed migration campaigns (§43); evidence from different migration epochs is never silently combined (§43).
- **Migration stage** — one of the six stages defined in §6 (Stage 0–Stage 5), each with exactly one designated lifecycle authority.
- **Authority epoch** — a stable identifier disclosing which derivation is authoritative and under which contract/schema version, distinct from migration epoch (a migration epoch can span multiple authority-epoch changes via rollback/roll-forward, §40).
- **Evidence threshold** — the quantitative and qualitative bar (§15) a migration stage's exit criteria require before the next stage may be entered.
- **Cutover gate** — the complete set of entry prerequisites (§7) that must all be satisfied, and explicitly approved (§41), before Stage 3 begins.

---

## 6. Authority-stage model

Six stages, each with exactly one designated lifecycle authority. Stage transitions are never implicit and never triggered by elapsed time alone (§7).

### Stage 0 — Shadow Observation (current state, post-135K/135L)

- **Authority:** Legacy lifecycle derivation, exclusively.
- **CLTR role:** derivative and observational only (135K §16: `_observe_shadow_cltr` runs only after `promote_and_dispatch()` has already returned; exception-contained; never affects `result`).
- **Evidence:** disclosed per-record `limitations`; no comparison against a second, independently-assembled input package yet — CLTR observes what legacy already computed, it does not independently *derive* from shared raw inputs.
- **Feature flag:** `PCAE_CLTR_SHADOW_ENABLED`, default off.

### Stage 1 — Dual Derivation, Legacy Authority

- **Authority:** Legacy lifecycle derivation remains exclusively authoritative for completion of the finalization transaction (whether it returns success, partial, or failure to the caller).
- **CLTR role:** derives independently from the same shared explicit transition-input package (§8) that legacy derivation consumes, rather than observing legacy's already-computed outputs. Comparison evidence (§11, §12) becomes mandatory and persisted (§14) for every governed transition while this stage is active.
- **Constraint:** CLTR cannot block, delay, or alter completion of the finalization transaction except through a separately frozen, narrow safety condition defined and approved in the Stage 1 implementation contract (135O) — e.g., a fail-closed abort limited to detecting that the shared input package itself is malformed, never a judgment about legacy's *output*.
- **Entry gate:** §7 Stage 1 row.

### Stage 2 — Dual Publication Rehearsal

- **Authority:** Legacy lifecycle derivation remains exclusively authoritative.
- **CLTR role:** CLTR and legacy outputs are both prepared inside one candidate publication transaction (§20's local-atomicity model), exercising the full candidate-preparation sequence (§25) and rollback rehearsal (§27), but the transaction's *authoritative* outcome remains whatever legacy derivation determines. No CLTR authority exists yet; this stage proves the publication mechanism, not CLTR's fitness to govern it.
- **Entry gate:** §7 Stage 2 row.

### Stage 3 — CLTR Authority With Legacy Verification

- **Authority:** CLTR becomes the sole lifecycle authority for every new governed transition.
- **Legacy role:** legacy representations become derived compatibility outputs (produced *from* the CLTR record, not independently computed); legacy's independent derivation path remains available only for comparison and rollback evidence during this stage, not as a candidate authority.
- **Requires:** a separate contract, independent verification, and an explicit operator-approved implementation phase (135S/135T/135U/135V) — this document does not authorize entry into Stage 3; it only defines what entering it will require.
- **Entry gate:** §7 Stage 3 row (the strictest gate in this document).

### Stage 4 — Legacy Demotion

- **Authority:** CLTR, unchanged from Stage 3.
- **Legacy role:** legacy artifacts remain supported as deterministic derivatives (readable, regenerable); they no longer participate in lifecycle truth for any fact meeting the demotion criteria (§36). Narrative parsing and fallback inference (title regexes, recent-Git-history inference, mutable `latest.*` presence-as-fact) become explicitly compatibility-only, never load-bearing.
- **Entry gate:** §7 Stage 4 row; requires 135W or a successor phase, not scheduled by this document.

### Stage 5 — Legacy Retirement

- **Authority:** CLTR, unchanged from Stage 4.
- **Legacy role:** legacy's independent derivation *paths* (the code that would compute a lifecycle fact without consulting CLTR) are removed. Historical compatibility reads remain available and read-only. No historical evidence already recorded is rewritten, backfilled, or relabeled as though CLTR had been authoritative at the time it was created (§39).
- **Entry gate:** §7 Stage 5 row; not scheduled by this document; requires the strongest evidence bar in the entire migration (§37).

At every stage above, exactly one authority is named. No stage description in this document permits CLTR and legacy to be simultaneously authoritative for the same fact, and none permits an intermediate "authority TBD" state — where a fact's authority is ambiguous, the fact defaults to legacy authority until a named stage transition explicitly reassigns it (this default-to-legacy rule is itself frozen as a fail-closed principle for the whole migration).

---

## 7. Stage entry and exit gates

No stage transition occurs merely because time has passed, a sample count is reached, or a phase number increments. Evidence quality controls progression, and every gate below requires explicit governed review of the evidence, not an automated pass/fail alone (except where noted as a hard prerequisite check).

| Stage | Entry prerequisites | Required evidence | Duration/sample size | Acceptable mismatch rate | Prohibited mismatch classes | Operational health | Exactly-once evidence | Recovery evidence | Rollback readiness | Human approval | Exit criteria | Abort criteria |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **0→1** | F-135L-1, F-135L-2 (adapter wiring, transition identity), 135K-limitation-4 (commit ownership) resolved per §4; shared input contract (§8) frozen and independently verified (135N) | 135O implementation independently verified by 135P with zero Blocking findings | N/A (design gate, not volume gate) | N/A (Stage 1 has not begun) | N/A | `pcae health`/`check`/`push check` all clean at 135O/135P completion | N/A yet | N/A yet | Stage 1 can be disabled by flag alone, restoring Stage 0 | Operator approval of 135P's verdict | 135P verdict VERIFIED (with or without Non-Blocking findings, zero Blocking) | Any Blocking finding in 135P; any evidence of legacy behavior change |
| **1→2** | Stage 1 operating; evidence-window coverage (§15) across all four entry points and at least one recovery path | Zero identity/transition/state mismatches; `authority_relevant_mismatch` count = 0; `non_authority_mismatch` disclosed and reviewed | Minimum sample size and elapsed duration jointly derived and approved by 135Q per §15's stated method (not fixed here) | Zero authority-relevant mismatches; a nonzero, bounded rate of disclosed `expected_representation_difference` is acceptable if each instance is individually explained | `identity_mismatch`, `digest_mismatch` (for exact-identity-digest kinds), `commit_ownership_mismatch`, `recovery_classification_mismatch` | Fast Green and affected-lifecycle regression subset pass unchanged with Stage 1 enabled | Zero duplicate CLTR generations per transition | At least one successful recovery-path transition observed and compared with zero authority-relevant mismatch | Full rollback drill (disable dual derivation, confirm Stage 0 behavior resumes) executed and evidenced | Explicit operator sign-off citing the evidence above | 135Q begins only after this sign-off | Any authority-relevant mismatch; any exactly-once violation; any rollback-drill failure |
| **2→3** | Stage 2 rehearsal complete; atomic local-publication mechanism (§20–§22) proven under 135R's adversarial acceptance drills (§54) | 135R verdict VERIFIED, zero Blocking findings, all drills in §54 passed | Determined by 135R; must include entry-point coverage (§16) and at least one crash-recovery and one rollback rehearsal | Zero authority-relevant mismatches sustained through rehearsal | All classes in the "authority-relevant" tier of §13 | Full governance suite green through rehearsal period | Zero duplicate publications, zero duplicate notifications during rehearsal | Crash-before-publish and crash-after-publish both drilled and recovered correctly | Rollback to Stage 1 (disable rehearsal, retain evidence) drilled | A **separate**, explicitly named Stage 3 contract-freeze phase (135S) plus its own verification (135T) — this document does not pre-approve Stage 3 | 135T verdict VERIFIED, zero Blocking findings, explicit cutover-approval artifact (§41) executed | Any Blocking finding in 135T; missing or expired approval artifact |
| **3→4** | Stage 3 operating for a minimum stable window defined by 135S/135T (not fixed here); legacy verification comparison continues throughout | Zero unresolved authority-relevant mismatches during the entire Stage 3 window; at least one successful rollback drill performed *while CLTR was authoritative* | Defined by 135S; must include a full release-boundary cycle if the project has one | Zero | All authority-relevant classes | Sustained governance-suite green throughout the window | Zero exactly-once violations across the entire window | Full recovery-path coverage under CLTR authority, not just legacy authority | Rollback from CLTR authority back to legacy authority proven at least once without rewriting history | Explicit operator approval for demotion (separate from cutover approval) | 135W verdict (or successor) confirms demotion criteria (§36) met per source | Any authority-relevant mismatch surfacing after cutover; any rollback drill failure |
| **4→5** | Stage 4 operating for the strongest evidence bar in the migration (§37); demotion evidence stable | Zero unresolved authority-relevant mismatches; successful recovery and rollback drills repeated under demotion conditions; historical-compatibility validation passed | Longest window in the migration; release-boundary gated if required | Zero | All authority-relevant classes, permanently | Sustained green through the entire demotion window | Zero violations, permanently | Full coverage, permanently | Rollback expiry decision made explicitly (§38) | Explicit operator approval, deprecation notice published, documentation updated | Retirement plan phase (unscheduled) confirms all §37 criteria met | Any regression in any criterion above |

---

## 8. Dual-derivation input contract

One shared explicit transition-input package, consumed identically by both derivation paths, is the load-bearing mechanism that prevents dual derivation from becoming dual *interpretation*. Neither derivation path may independently reconstruct a mandatory input.

### 8.1 Required principles (frozen, non-negotiable for Stage 1+)

Both derivation paths must consume, from the one assembled package, identical values for: phase identity; task identity; transition identity; source revision; staged final revision; explicit commit ownership; report identity and digest; promotion identity; checkpoint identity; marker identity; receipt identity; notification identity and state; recovery classification; entry-point identity; and the assembler's own disclosed limitations.

### 8.2 Explicit prohibition on fallback inference

Neither derivation path may reconstruct any mandatory input from: report titles; filenames; task titles; Architecture Status prose; commit subjects; recent Git history; repository HEAD; latest-file presence; stale completion metadata; or paused-task narrative state. This restates and generalizes CLTR-001 §4.2's nine forbidden competing-authority patterns and 135D.1's staleness-guard lesson (a title-regex reconstruction of `phase_id` is exactly the class of defect that corrupted `.pcae/phase-completion-metadata.json` for ~71 seconds in 135D.1) to the dual-derivation boundary specifically: if legacy derivation were ever allowed to silently re-derive an input CLTR also derives independently, from two different fallback sources, a "mismatch" in comparison could reflect two different reconstructions of the same absent fact rather than a genuine disagreement about a well-defined fact — undermining the entire evidentiary purpose of dual derivation.

### 8.3 `transition_id` identity decision (required before Stage 1, per F-135L-2 disposition)

135L's F-135L-2 observed that `transition_id == phase_id` in the current shadow wiring causes a same-phase correction (partial→success) to collide with the prior shadow generation. The shared input contract must resolve this before Stage 1 begins. Two candidate designs, to be evaluated and frozen by 135N (not decided here):

- **(a) Composite identity:** `transition_id = f"{phase_id}:{entry_point}:{attempt_sequence}"`, where `attempt_sequence` increments per distinct finalization attempt for the same `phase_id` (matching CLTR-001's own transition concept — one governed lifecycle transition per finalization attempt, not per phase).
- **(b) Separate transition and phase identity fields:** `transition_id` becomes independently generated (e.g., a UUID or monotonic counter bound to the finalization-transaction invocation), with `phase_id` remaining a separate, always-present field in the shared input package and every derived record.

135N must select one of these (or a third design meeting the same requirement) before 135O implements the shared input assembler. Either design must guarantee: two distinct finalization attempts for the same `phase_id` never produce colliding `transition_id` values, and a superseding correction is always modeled as `predecessor_transition_id`/`successor_transition_id` (already frozen fields, CLTR-SCHEMA-001 §7), never as an overwrite.

---

## 9. Shared input assembly authority

One component — to be named and implemented in 135O, not this document — owns assembly of the shared explicit transition-input package.

The assembler must: run exactly once per governed transition, at a fixed point inside `run_finalization_transaction()` before either derivation path begins (analogous to where `_observe_shadow_cltr` currently runs, but *before* both derivations rather than after only legacy has run); produce one immutable input package object; bind all identity and evidence fields listed in §8.1; identify its own source authority (i.e., disclose which production values it read and from where — `report_digest`, `finalization_snapshot_id`, git-derived revision facts, etc. — matching the transparency already established by 135K's `limitations` field convention); be digestible (produce a stable digest of its own content, so both derivations and later comparison evidence can reference "the same input package" by digest, not by trusting re-execution to be idempotent); be persisted before divergent derivation begins wherever the migration stage requires evidence of what both derivations actually saw (Stage 1 onward); be reused, unmodified, by both derivation paths — neither path re-invokes the assembler independently; prevent post-assembly mutation (the package, once produced, is immutable for the remainder of that transition, matching CLTR-001 §14.1's "immutable once certified" principle applied one step earlier in the pipeline); expose its own limitations exactly as 135K's shadow records already do; and fail closed on missing mandatory authority — if a mandatory input cannot be assembled (e.g., commit ownership genuinely cannot be determined), the assembler must produce an explicit "assembly failed" outcome rather than a package with a silently substituted or inferred value.

The legacy and CLTR derivations must not assemble their own competing interpretations of any field the assembler is responsible for. This is the single mechanism that makes "dual derivation, not dual authority" actually true at the input layer, mirroring CLTR-001 §4.1's rule ("a lifecycle fact may have only one authoritative source within a transition") applied specifically to *inputs* rather than outputs.

---

## 10. Dual-derivation isolation

A failure in one derivation path must never silently alter the other. Both derivations, given the same assembled input package, must:

- produce separate candidate outputs (legacy's existing outputs; CLTR's own record) with no shared mutable intermediate state between them;
- produce separate validation results (CLTR-SCHEMA-001's own validation of the CLTR record is independent of whatever validation legacy's finalization gate already performs);
- produce separate digests (the CLTR `record_digest` per CLTR-SCHEMA-001 §15 is computed over CLTR's own serialized content; it is never derived from or compared byte-for-byte against a legacy artifact's digest except through the comparison contract's `exact_identity_digest` mode, §12);
- bind to the one shared input package by reference (digest, per §9), never by re-derivation;
- never mutate one another's state — CLTR derivation must remain exception-contained exactly as 135K's `_observe_shadow_cltr` already is (`except Exception: # noqa: BLE001 — shadow observation must never affect production finalization`), and this containment discipline must extend, unchanged in spirit, through Stage 1 and Stage 2 (legacy derivation continues regardless of CLTR derivation's success or failure);
- never fall back across paths — CLTR derivation must never consult legacy's output to "fill in" a value it could not independently derive, and legacy derivation must never consult CLTR's output during Stage 0–2 (this would silently make CLTR authoritative before Stage 3);
- never automatically strengthen a result — an `unverifiable` comparison outcome is never silently promoted to `match` by either path acting alone (CLTR-SCHEMA-001 §21.2's determinism/no-silent-upgrade rule, generalized from adapters to the whole dual-derivation boundary); and
- expose an explicit unavailable/unverifiable status rather than omitting a result when isolation prevents a full comparison.

---

## 11. Comparison contract

Comparison is deterministic and operates on normalized semantic fields, not narrative wording. It reuses, without modification, CLTR-SCHEMA-001 §21's five-value `adapter_comparison_mode` taxonomy and §21.4's already-frozen per-kind assignment (reproduced below for reference, since 135M's comparison contract is built directly on it, not a new taxonomy):

| Representation kind | `adapter_comparison_mode` |
|---|---|
| Canonical phase report | `exact_identity_digest` |
| Completion metadata | `exact_identity_digest` |
| Architecture Status | `normalized_semantic` |
| Immutable snapshot | `exact_identity_digest` |
| Checkpoint | `normalized_semantic` |
| Promoted generation (report) | `exact_identity_digest` |
| Promoted generation (metadata) | `exact_identity_digest` |
| Notification payload | `normalized_semantic` |
| Marker | `normalized_semantic` |
| Receipt | `normalized_semantic` |
| Repository transition view | `observational` |
| Git attribution view | `observational` |
| Compatibility/legacy-format view | `normalized_semantic` |
| Diagnostic envelope | `presentation_only` |
| Reconciliation view | `observational` |

At minimum, comparison must evaluate: phase identity; task identity; transition identity; lifecycle state; status; report identity; report digest; metadata identity; source revision; staged final revision; explicit commit ownership; promoted generation identity; checkpoint identity; marker identity; receipt identity; notification state; planned successor where explicitly governed; Architecture Status transition state; terminal classification; retry/replay classification; limitations; and authority role (the CLTR-001 S/R/D/E/V classification, §1.4 of the research inputs — comparison must confirm both paths agree on *which* role each representation plays, not only on its value).

Comparison must never infer equivalence from similar text. A field assigned `normalized_semantic` mode is compared after normalization of structure (e.g., key ordering, whitespace, semantically-irrelevant formatting), never by fuzzy string matching or narrative similarity — this is the same rule CLTR-SCHEMA-001 §14 already establishes for canonical serialization, extended to the comparison layer.

---

## 12. Comparison result classes

Each class below is drawn either directly from CLTR-SCHEMA-001's existing `conformance_state` family (§22.1: `conformant`, `conformant_with_legacy_adapter`, `incomplete`, `conflicting`) or is a new dual-derivation-specific refinement this document defines for the purpose of migration evidence (§14). New classes are marked **[NEW]**; all others are direct reuses.

| Class | Severity | Cutover impact | Progression permitted? | Operator review required? | Production completion may continue? (per stage) | Evidence requirement | Remediation requirement |
|---|---|---|---|---|---|---|---|
| `exact_match` | none | positive evidence | yes | no | yes, all stages | logged with digest | none |
| `semantic_match` | none | positive evidence | yes | no | yes, all stages | logged with normalized diff (empty) | none |
| `expected_representation_difference` **[NEW]** | low | neutral, if individually explained | yes | yes, first occurrence of a new kind; no thereafter if pattern is pre-approved | yes, all stages | logged with explanation reference | document the expected-difference rule in the migration-evidence record schema (§14) |
| `legacy_missing` **[NEW]** | medium | blocks Stage 1→2 progression until explained | no, until reviewed | yes | yes (legacy authoritative; CLTR absence is itself informative, never blocking) | logged, investigated | must resolve before evidence counts toward §15 thresholds |
| `cltr_missing` **[NEW]** | low pre-Stage-3; high at/after Stage 3 | blocks any stage's progression while unresolved | no | yes | yes pre-Stage-3 (legacy unaffected); this class must not occur post-cutover | logged, investigated | must resolve before evidence counts toward thresholds; post-cutover occurrence triggers rollback consideration (§39) |
| `unverifiable` | none (honest absence) | does not block progression by itself, but a stage cannot exit while its own required kinds remain `unverifiable` (§7) | yes, but does not count as positive evidence | no, unless the rate is unexpectedly high | yes, all stages | logged with reason (missing adapter source, missing input) | wiring/implementation work in the named resolution phase, not a data remediation |
| `non_authority_mismatch` **[NEW]** | low | none | yes | no | yes, all stages | logged | none required; disclosed as evidence-window color |
| `authority_relevant_mismatch` **[NEW]** | high | blocks progression to next stage; **fail-closed at Stage 3+** | no | yes, always | at Stage 0–2: yes (legacy authoritative, unaffected); at Stage 3+: **no** — CLTR fails closed per §13 | logged, root-caused | must be root-caused and either fixed or explicitly re-classified via governed review before any further stage progression |
| `identity_mismatch` | high | blocks progression | no | yes | per stage per §13 | logged, root-caused | resolve before progression |
| `transition_mismatch` | high | blocks progression | no | yes | per stage per §13 | logged, root-caused | resolve before progression |
| `state_mismatch` | high | blocks progression | no | yes | per stage per §13 | logged, root-caused | resolve before progression |
| `digest_mismatch` | high (for `exact_identity_digest` kinds) | blocks progression | no | yes | per stage per §13 | logged, root-caused, tamper/corruption investigation (CLTR-SCHEMA-001 §15.5) | resolve before progression |
| `commit_ownership_mismatch` | high | blocks Stage 1 entry until commit-ownership model resolved (§4) | no | yes | per stage per §13 | logged | resolve before progression |
| `notification_mismatch` | medium–high | blocks Stage 2→3 progression | no | yes | per stage per §13; never triggers a second dispatch by itself | logged | resolve before progression; never remediate by redispatching |
| `marker_mismatch` | medium | blocks Stage 2→3 progression | no | yes | per stage per §13 | logged | resolve before progression |
| `receipt_mismatch` | medium | blocks Stage 2→3 progression | no | yes | per stage per §13 | logged | resolve before progression |
| `temporal_order_mismatch` **[NEW]** | medium | blocks progression if it indicates a causality violation (e.g., notification recorded before promotion) | no if causality-violating; yes with review if merely clock-skew | yes | per stage per §13 | logged | resolve before progression if causality-violating |
| `recovery_classification_mismatch` **[NEW]** | high | blocks Stage 1→2 progression | no | yes | per stage per §13 | logged, root-caused | resolve before progression |

---

## 13. Mismatch policy by stage

Fail-open versus fail-closed behavior is explicitly stage-dependent; one generic policy is never used for every stage.

**Stage 0–2 (legacy-authoritative stages):**
- legacy production behavior remains authoritative regardless of any comparison result;
- every mismatch (any class in §12 other than `*_match`/`unverifiable`) must be persisted in the migration-evidence record (§14) — never silently ignored;
- every mismatch must be visible through the planned read-only status/reconciliation commands (§44, §45);
- CLTR must never claim conformance beyond what comparison actually verified (no silent upgrade, matching CLTR-SCHEMA-001 §21.2);
- an `authority_relevant_mismatch` (or any of `identity_mismatch`, `transition_mismatch`, `state_mismatch`, `digest_mismatch`, `commit_ownership_mismatch`) must block *migration progression* (advancing to the next stage) but must never block *production completion* — the finalization transaction completes exactly as legacy derivation determines, regardless of CLTR's comparison result;
- production completion behavior follows the stage's explicitly frozen policy above; no stage improvises.

**Stage 3+ (CLTR-authoritative stages):**
- an authority-relevant CLTR validation failure (a Blocking invariant failing, or a required field missing per CLTR-SCHEMA-001 §6) must fail closed — the finalization transaction does not complete successfully;
- legacy disagreement, once CLTR is authoritative, becomes verification *evidence* pointing at either a CLTR defect or a legacy-compatibility-output defect — it is never grounds for legacy's output to overrule CLTR's determination;
- legacy output cannot overrule CLTR at Stage 3+ under any circumstance short of a governed rollback (§39);
- rollback may be triggered only through the governed migration controls defined in §38–§39, never automatically by a single mismatch, and never by legacy derivation code itself deciding to reassert authority.

This dual policy directly operationalizes the "Dual derivation must not become dual authority" principle from §2: during Stage 0–2, CLTR's judgment is never binding; during Stage 3+, legacy's judgment is never binding. There is no stage in which both are simultaneously binding.

---

## 14. Evidence thresholds

Quantitative and qualitative evidence required before progressing each stage, building on §7's gate table. At minimum: number of successful ordinary completions; number of successful task-finish completions; number of successful phase-complete completions; number of successful recovery completions; zero identity mismatches; zero transition mismatches; zero state mismatches; zero exactly-once violations; zero duplicate promotions; zero duplicate notifications; zero marker/receipt honesty failures; zero atomic-publication failures; zero unreconciled pointer failures; deterministic replay proof; crash-recovery proof; feature-flag isolation proof (already demonstrated for Stage 0 by 135K/135L; must be re-demonstrated for each new flag introduced at each stage, §42); historical compatibility proof (required no earlier than Stage 3's contract, §39).

This document does not select arbitrary sample counts. Per the explicit instruction to avoid unmotivated thresholds: **135Q (Atomic Publication Rehearsal Implementation) must derive and 135R (its independent verification) must approve the exact minimum sample size, elapsed-duration requirement, and acceptable mismatch rate for the 1→2 and 2→3 transitions**, using a method that at minimum accounts for: (a) the historical rate of governed phase completions in this repository (observable directly from `tasks/DONE.md` and phase-report history, giving an empirical base rate rather than a guessed number); (b) statistical coverage sufficient to detect a mismatch rate distinguishable from zero at a stated confidence level, not merely "run it a while"; and (c) mandatory coverage of all four entry points and at least one recovery path (§16), regardless of how the numeric threshold is derived. Until 135Q/135R freeze this number, no numeric evidence threshold is binding, and no stage transition past 1→2 may be justified by volume alone.

---

## 15. Evidence window

Evidence is measured by a combination of dimensions, not any single one: transition count; phase count; elapsed duration; entry-point coverage (all four, §16); recovery-path coverage (§16, §48); and, where applicable, repository releases (if this project adopts release boundaries in the future). A high volume of only one easy path (e.g., many `ordinary` `phase complete` invocations with no `task finish`, no `phase-report create` standalone invocation, no `notify send-report` standalone invocation, and no recovery-path exercise) must never substitute for missing coverage of the other three entry points or of recovery paths. 135Q/135R must design the evidence-window requirement so that entry-point and recovery-path coverage are independently gating conditions, not merely inputs averaged into one aggregate count.

---

## 16. Migration evidence record

A canonical migration-evidence artifact, distinct from the CLTR record itself and distinct from the canonical phase report, binds: migration stage; migration epoch; input package identity (§9's digest); legacy derivation identity; CLTR derivation identity; both derivations' digests; comparison result (per §12 class, per compared field); mismatch classification; limitations; entry-point identity; recovery classification; production authority at the time of the transition (which stage/epoch was authoritative when this transition occurred); progression eligibility (whether this transition's evidence counts toward the next stage's threshold); operator decision where applicable (e.g., an explicit "reviewed and accepted" annotation for an `expected_representation_difference`); timestamps; and an evidence-record digest of its own.

**The migration-evidence record is evidence, not lifecycle authority.** It must never be consulted by either derivation path as an input (this would create a circular authority dependency), and its presence or absence never determines whether a finalization transaction completes — it is produced *after* both derivations and comparison have already run, purely as a durable audit trail. This mirrors CLTR-001's own rule that the transition record itself must never be inferred from derivative evidence (§4.2) — the migration-evidence record is one level further removed and must observe the same discipline.

---

## 17. Migration epoch

A stable migration epoch or campaign identity distinguishes: separate implementation attempts (e.g., if 135O is later revised or re-implemented); restarted evidence windows (if a Stage 1→2 evidence run is abandoned and restarted); contract-version changes (a CLTR-SCHEMA-001 minor/major bump during migration); rollbacks (a rollback event begins a new epoch segment even if the same schema/contract versions are in force); resumed migration (after a pause); and repository-version boundaries (if this project adopts them).

Evidence from incompatible epochs must never be silently combined into one evidence-threshold count. The migration-evidence record (§16) carries its producing epoch; any aggregation logic (in the future read-only status command, §44) must group by epoch explicitly and disclose when evidence spans multiple epochs rather than silently pooling it.

---

## 18. Atomic publication target

The final desired publication model: one transaction prepares and publishes a complete generation containing the canonical CLTR record; the canonical phase report; completion metadata; the Architecture Status projection; the checkpoint; notification intent/binding; marker intent/binding; receipt intent/binding; a manifest; representation outputs (legacy-compatible derived views); and comparison/migration evidence where applicable (Stage 1+ only — Stage 0 has no publication-time comparison since shadow observation runs after publication today).

Artifacts created **before** external delivery: the CLTR record, the manifest, the report content, the metadata, the Architecture Status projection, the checkpoint, and the notification *intent* (not yet the confirmed outcome). Artifacts finalized **after** confirmed or uncertain delivery: the notification *result* (confirmed/uncertain/failed), the marker's terminal state, and the receipt's finalized state — because these three depend on an external system (Telegram) whose outcome cannot be known until the delivery attempt returns or times out.

This document does not claim a filesystem transaction can atomically include an external Telegram delivery. §19 makes this separation explicit and binding.

---

## 19. Local atomicity versus external effects

**Local atomic publication** can include: the immutable generation; the manifest; the report; the metadata; the Architecture Status projection; the checkpoint; marker *intent*; receipt *state* (as of the local transaction, i.e., "not yet attempted" or "attempt recorded, outcome pending"); notification *intent*; and the current pointer. All of these are filesystem artifacts under this repository's control, and `os.replace`-based atomic pointer replacement (the same mechanism CLTR shadow persistence already uses, `persistence.py:137-233`) can genuinely make their joint publication atomic.

**External terminal delivery** (the Telegram dispatch) cannot be made filesystem-atomic with local publication, because it depends on a network round-trip to a system this repository does not control. It must use: a durable intent record (written before the attempt, as part of local atomic publication); an idempotency key (already established practice via PFN-001's "idempotent dispatch" guarantee, §8 of that contract); an explicit state transition (`not_attempted` → `attempted` → `confirmed` | `uncertain` | `failed`); a confirmed/uncertain outcome distinction (matching the existing `NOTIFIED`/`NOTIFIED_UNCONFIRMED` states already frozen in CLTR-001/135D's state machine); a retry/reconciliation policy (matching 135H.2's existing `pcae phase-report reconcile` model, extended to CLTR generations); and exactly-once **logical** delivery semantics — never physical exactly-once, since a network partition after successful delivery but before confirmation receipt is indistinguishable, from the sender's perspective, from a failed delivery, and only reconciliation (never blind retry) resolves the ambiguity (135H.2 §4: "This changes recovery from 'retry and hope the side effect did not happen' to 'observe and reconcile; never duplicate an irreversible effect.'").

This document explicitly preserves PFN-001 and does not describe external delivery as physically exactly once anywhere in this contract.

---

## 20. Atomic generation contract

One immutable publication generation binds: generation identity; transition identity (per §8.3's resolved design); phase identity; task identity; source revision; staged final revision; the CLTR record; the report; the metadata; the Architecture Status projection; the checkpoint; marker state; receipt state; notification state; commit ownership; a manifest; digests (of every included artifact, plus a manifest-level digest); compatibility data; and limitations.

After cutover (Stage 3+), no component may independently publish an authority-like "latest" artifact outside the generation transaction. This directly closes 135J's inherited F5 finding (atomic `latest.*` publication currently unimplemented) and the exact split-brain precedent 135L's F-135L-3 finding demonstrated in legacy tooling (a report re-promoted under an identical `phase_id` by an unrelated later action, producing a reconciliation conflict) — after cutover, the generation pointer (§22) is the only mechanism by which "latest" is established, and no legacy `latest.md`/`latest.json` write path may bypass it.

---

## 21. Candidate preparation sequence

The future implementation sequence, frozen here as an 18-step design, is:

1. resolve explicit identity (§8.3);
2. assemble immutable shared transition input (§9);
3. validate input (fail closed on missing mandatory authority, §9);
4. derive CLTR candidate (independent derivation, §10);
5. derive legacy compatibility candidates (independent derivation, §10);
6. validate each derivation independently (§10);
7. compare derivations (§11–§12);
8. classify mismatches (§12–§13);
9. evaluate migration-stage policy (§13 — determines whether this transition's outcome is affected by comparison at all, per the current stage);
10. assemble complete local publication generation (§18, §20);
11. verify manifest and all digests (§20, mirroring CLTR-SCHEMA-001 §15's digest contract);
12. persist pre-publication checkpoint (§26);
13. atomically publish current-generation pointer (§22);
14. record local publication result (§16's migration-evidence record, where applicable);
15. process durable external notification intent (§19, §29);
16. record confirmed/uncertain delivery (§19);
17. finalize marker and receipt state through governed continuation (§30, §31, matching 135H.2's exactly-once promotion discipline);
18. expose reconciliation state (§45).

**Ordering applicability:** steps 1–9 apply from Stage 1 onward (Stage 0 today only performs a subset of step 4, after the fact). Steps 10–18 in their fully atomic form apply only from Stage 2 (rehearsal) onward — Stage 0 and Stage 1 continue to use legacy's existing (non-CLTR-atomic) publication path for the authoritative outcome, with CLTR's own generation published separately (as it is today) rather than jointly. Only at Stage 2 does "one candidate publication transaction" begin to jointly include both legacy and CLTR artifacts, and only at Stage 3+ does that joint transaction become the transaction whose outcome is authoritative.

---

## 22. Publication pointer contract

The pointer identifies: pointer identity (a fixed, well-known path per generation family, matching `persistence.py`'s existing `current` file convention); target generation (the `transition_id`/`generation_id` it references); atomic replacement (via `os.replace`, never a non-atomic write-then-rename-elsewhere sequence); validation before replacement (the new generation's manifest and digests must verify before the pointer is updated to reference it — never point at content that has not yet been confirmed intact); stale pointer behavior (a pointer referencing a generation whose manifest digest no longer matches on-disk content must be treated as failed/untrusted, never silently accepted — matching `read_current_generation()`'s existing behavior of returning `None` rather than repairing on mismatch); missing pointer behavior (no pointer present means no generation has ever been published for this identity — never inferred from directory listing or "latest file" heuristics); dangling pointer behavior (a pointer referencing a generation directory that does not exist must fail closed, not fall back to an earlier generation silently); rollback pointer behavior (a rollback, per §38, is itself a new, atomically-published pointer update referencing a prior, already-verified generation — never a direct filesystem rewrite of history); migration-stage binding (the pointer's generation content discloses which stage was authoritative when it was published, §40); and authority-epoch binding (likewise disclosed per generation, §40).

A pointer must never establish truth without verified generation content — this is the direct generalization of CLTR-SCHEMA-001 §15.5's "digest mismatch is tamper/corruption evidence, never silent acceptance" rule to the pointer layer specifically.

---

## 23. Split-brain prevention

Controls required before Stage 3, and permanently thereafter: the report pointer and metadata pointer must never diverge (they are published together, in one generation, per §20 — this is structurally impossible once the atomic generation contract is implemented, not merely policed); the CLTR pointer and report pointer must never diverge for the same reason; the current pointer and checkpoint must never diverge (the checkpoint records the same generation identity the pointer references, and reconciliation, §45, verifies this agreement exactly as `pcae phase-report reconcile` already verifies checkpoint/marker/receipt agreement today); marker and receipt must never reference different generations (both are fields *within* one generation, not independently published artifacts, per §20); notification binding must never reference a different report digest than the one actually published (the notification intent is itself part of the same generation, §18); Architecture Status must never reference a different transition than the one the generation represents (Architecture Status becomes a deterministic derivative of the CLTR record it belongs to, §33, not an independently regenerated artifact that could drift); and legacy and CLTR outputs must never be published from different input packages (this is guaranteed structurally by §9's shared-assembly-only rule, not by a downstream check that could itself be bypassed).

**After final cutover (Stage 3+), there is one generation pointer, not independent "latest" pointers for report, metadata, and CLTR acting as competing authorities.** This is the single most important structural guarantee this document establishes for eliminating split-brain risk, and it is the direct fix for the exact class of defect 135L's F-135L-3 finding already demonstrated occurring in legacy tooling.

---

## 24. Publication failure model

For each failure point below: authoritative state; recorded evidence; retry eligibility; replay prohibition; reconciliation requirement; operator visibility; rollback eligibility.

| Failure point | Authoritative state | Recorded evidence | Retry eligibility | Replay prohibited? | Reconciliation required? | Operator visibility | Rollback eligible? |
|---|---|---|---|---|---|---|---|
| Before input persistence | Whatever was authoritative before this transition began (unaffected) | Nothing durable yet | Yes, freely | No | No | Transient failure, logged | N/A — nothing published |
| During CLTR derivation | Unaffected (Stage 0–2: legacy still authoritative regardless) | Failure recorded per 135K's existing `failures/<phase_id>-<uuid>.json` pattern, extended | Yes | No | No | Disclosed in shadow/dual-derivation status | N/A |
| During legacy derivation | Legacy's own existing failure semantics apply unchanged (this document does not alter legacy failure handling until Stage 3) | Legacy's existing mechanisms | Per legacy's existing rules | Per legacy's existing rules | Per legacy's existing rules | Per legacy's existing rules | N/A |
| During comparison | Unaffected; comparison failure is itself an `unverifiable` result (§12), not a transaction failure | Migration-evidence record notes `unverifiable` with reason | Yes | No | No | Disclosed | N/A |
| During generation assembly | Unaffected (Stage 0–1); at Stage 2+, the candidate generation is simply never completed | Partial-assembly artifacts quarantined, never published (matching 135K's existing quarantine pattern) | Yes, from scratch | No | No | Disclosed | N/A — nothing published |
| During generation verification | Unaffected | Manifest/digest mismatch recorded; generation not published | Yes, from scratch | No | No | Disclosed | N/A |
| Before checkpoint | Unaffected | Nothing durable yet at this failure point | Yes | No | No | Disclosed | N/A |
| After checkpoint but before pointer publication | Prior generation remains authoritative (pointer unchanged) | Checkpoint records `pointer_publication: in_progress` (mirroring 135H.2's `promotion_and_dispatch: in_progress` durable-intent barrier) | No blind retry — must observe checkpoint state first | **Yes, prohibited** — automatic replay must not re-attempt pointer publication blindly | **Yes** — reconciliation determines whether the pointer was actually updated before deciding next action | Fully visible via reconciliation command (§45) | Not applicable yet (new pointer not confirmed) |
| During pointer publication | Ambiguous until reconciled (the `os.replace` may or may not have completed) | Checkpoint's in-progress marker persists until reconciled | No | **Yes, prohibited** | **Yes, mandatory** | Fully visible | Rollback only after reconciliation determines outcome |
| After pointer publication | New generation authoritative | Checkpoint updated to `pointer_publication: complete` | N/A (already succeeded) | N/A | No | Disclosed | Yes, via a new rollback-pointer publication (§38) |
| Before notification intent processing | New generation authoritative (local publication already complete) | Notification intent recorded as `not_attempted` | Yes | No | No | Disclosed | Local rollback possible; external delivery never attempted |
| After external delivery but before confirmation recording | New generation authoritative locally; delivery outcome ambiguous | Notification intent recorded as `attempted`, outcome pending | No blind resend | **Yes, prohibited** — must not blindly resend | **Yes, mandatory** (matches PFN-001's existing idempotent-dispatch discipline) | Fully visible via `pcae notify status`-equivalent extension | Local generation rollback does not un-send an already-attempted external delivery — roll-forward is preferred here (§39) |
| Before marker finalization | New generation authoritative; notification outcome may already be known | Marker recorded as pending | Yes, for marker-finalization step only | No, for marker step alone | Yes, if outcome ambiguous | Disclosed | N/A for marker alone |
| Before receipt finalization | Same as above | Receipt recorded as pending/`delivery_recorded_bookkeeping_incomplete`-equivalent | Yes, for receipt step alone | No, for receipt step alone | Yes, if outcome ambiguous | Disclosed | N/A for receipt alone |

---

## 25. Recovery contract

Recovery must consume recorded migration and publication state exclusively. It must never reconstruct intent from titles, latest files, recent Git history, commit subjects, stale metadata, or paused-task narrative state — the same prohibition as §8.2, applied specifically to the recovery path, and directly informed by 135D.1's incident (a title-regex reconstruction corrupted `phase_id` for ~71 seconds) and 135H.1's incident (a rejected candidate left no durable record, requiring governed manual recovery).

Recovery decisions are frozen for: **no candidate created** (nothing to recover; prior authoritative state stands); **candidate incomplete** (discard candidate, no publication attempted, no recovery action beyond disclosure); **candidate verified but unpublished** (safe to resume publication from the verified candidate, since verification already occurred — this is the one case where resuming *is* safe, because verification is idempotent and re-checking a digest is not a side effect); **pointer publication uncertain** (mandatory reconciliation before any further action — matches the "after checkpoint but before pointer publication" and "during pointer publication" rows of §24); **local publication complete** (proceed to notification-intent processing, exactly once); **notification not attempted** (safe to attempt, exactly once); **notification confirmed** (nothing further to do; recovery must not re-attempt); **notification uncertain** (reconciliation required, never blind resend — matches PFN-001's existing discipline); **marker incomplete** (finalize marker from confirmed/reconciled notification state, never from an independent guess); **receipt incomplete** (finalize receipt from confirmed/reconciled state, same rule); **rollback initiated** (recovery must complete or abort the rollback itself atomically, never leave a half-completed pointer swap); **rollback completed** (nothing further; new authoritative state confirmed).

Recovery paths must meet the same authority and atomicity contract as ordinary finalization — there is no separate, weaker recovery-path authority model, matching 135H.2's existing principle that recovery uses the same gate and the same at-most-once adapter-entry discipline as ordinary completion.

---

## 26. Exactly-once migration contract

Exactly-once semantics, defined across: shared transition input (one assembly per governed transition, §9); CLTR derivation (one record per transition, until multi-generation supersession is explicitly modeled, §8.3); legacy derivation (unchanged from today); comparison evidence (one migration-evidence record per transition, §16); local publication generation (one atomic generation per transition, §20); pointer publication (one atomic pointer update per transition, at-most-once entry per §24's "after checkpoint but before pointer publication" row); checkpoint (one checkpoint per transition, extended from 135H.2's existing model); notification intent (one intent per transition, matching PFN-001 exactly); external terminal delivery (logical exactly-once, per §19); marker (one terminal marker state per transition); receipt (one terminal receipt state per transition); rollback (one rollback event per invocation, itself durably recorded so a repeated rollback request against an already-rolled-back state is a no-op, not a second rollback).

Every logical operation above must have: a stable identity; an idempotency key; a recorded state; a retry policy; an uncertainty policy; and a reconciliation policy — directly generalizing 135H.2's exactly-once-promotion mechanism (`promotion_and_dispatch: in_progress` as a durable intent barrier, reconciliation rather than blind replay) from "promotion and dispatch" to every logical operation in the dual-derivation and publication pipeline.

**Shadow or dual derivation must never create a second logical completion.** This is the binding constraint that makes it safe to run CLTR derivation alongside legacy derivation at all: CLTR's own record-publication, comparison-evidence-publication, and (at Stage 2+) joint-generation-publication are each their own exactly-once operations, but none of them is a second *finalization* completion — there remains exactly one governed lifecycle transition per finalization attempt, exactly as CLTR-001 §2 already requires, regardless of how many derived artifacts that one transition produces.

---

## 27. Notification migration

No notification behavior changes in 135M. At all stages, this document requires: exactly one ordinary terminal delivery per governed transition (unchanged from PFN-001); one stable notification identity per transition; one report/generation binding (the notification always refers to the one generation published for that transition); shadow and comparison paths never dispatch (matching 135K's current behavior exactly — `_observe_shadow_cltr` has no dispatch capability and this document does not add one); legacy and CLTR paths never both dispatch (only one dispatch occurs, sourced from whichever derivation is authoritative at the time, per §13); uncertain delivery does not trigger uncontrolled resend (matching PFN-001's existing idempotent-dispatch guarantee and 135H.2's reconciliation-over-replay discipline); and marker and receipt remain honest (never claim delivery that did not occur, matching PFR-001/PFN-001's existing honesty requirements).

Notification intent becomes CLTR-derived, and the legacy notifier becomes compatibility-only, no earlier than Stage 3 (§6) — specifically, this transition must be part of the Stage 3 contract freeze (135S), not an incidental side effect of any earlier phase. Until then, the legacy notifier (`run_notify_send_report`, one of the four entry points, §16 of this document) remains exactly as it is today, unchanged by this migration plan.

---

## 28. Marker migration

**Current marker authority:** per 135H §1, the marker (`.last-notified.json`) is "canonical terminal/idempotency authority for all four entry points" today — this remains true and unchanged through Stage 0–2 of this migration.

**Future CLTR binding:** at Stage 3, the marker becomes a field within the CLTR generation (§20) rather than an independently-written file whose presence alone constitutes authority; the marker's terminal/idempotency role migrates onto the CLTR record's own `NOTIFIED`/`NOTIFIED_UNCONFIRMED` state (already frozen in CLTR-001/135D's state machine) plus the generation's own exactly-once pointer-publication discipline (§26).

**Migration-stage behavior:** Stage 0–2: marker continues to be written exactly as today by legacy derivation; CLTR observes/compares it (`normalized_semantic` mode per §11) but never writes it. Stage 3+: marker is emitted from CLTR as part of atomic generation publication and removed from legacy decision paths (matching 135H §2's own recommendation for the marker specifically).

**Idempotency, generation binding, notification binding, uncertainty handling, rollback behavior:** all governed by the exactly-once contract (§26) and the atomic generation contract (§20) once the marker becomes a generation field; until then, unchanged from today's file-based mechanism.

**Retirement criteria for independent marker derivation:** the marker file mechanism itself may be retired (Stage 5, §37) only after CLTR-derived marker semantics have operated stably through the full Stage 3/4 evidence bar; the file may remain permanently for compatibility even after its independent authority retires, per 135H §2's "retirement is fact-scoped, not file-scoped" principle.

**Markers must not become a second lifecycle authority** — at every stage in this document, the marker's authority is exactly one of {legacy, none-yet-assigned-to-CLTR, CLTR}, never both simultaneously.

---

## 29. Receipt migration

**Current receipt authority:** per 135H §1, the receipt is "canonical authority for narrow physical-delivery outcome only" — not a general lifecycle-state authority, a narrower scope than the marker's.

**Future CLTR-derived receipt state:** at Stage 3, the receipt's finalized/uncertain status becomes a field of the CLTR generation, populated through the same exactly-once, reconciliation-not-replay discipline already established for promotion (135H.2) and generalized in §26.

**Finalized versus uncertain status:** unchanged in meaning from today (`finalized` requires confirmed delivery or an explicit accepted-uncertain state; a receipt must never claim completion beyond recorded evidence — this document does not weaken that existing honesty rule).

**Generation binding, marker binding, notification binding:** at Stage 3, all three become fields of one generation (§20), eliminating the possibility of a receipt referencing one generation while its marker or notification-result fields reference another (§23).

**Rollback behavior:** a receipt already finalized (delivery confirmed) is never retroactively un-finalized by a rollback — rollback affects future authority, not past, already-recorded, honest evidence (§38's "rollback must never rewrite history").

**Retirement criteria for independent receipt derivation:** same bar as marker retirement (§37), evaluated independently since receipt and marker serve different narrow purposes and may reach retirement readiness at different times.

**Receipts must remain honest** — this document adds no new claim a receipt is permitted to make beyond what is actually recorded, at any stage.

---

## 30. Checkpoint migration

Six checkpoint moments are defined, extending 135H.2's existing single-checkpoint model (`promotion_and_dispatch: in_progress`) into the full atomic-publication pipeline: **pre-publication checkpoint** (recorded after generation assembly and verification, before pointer publication — the direct successor of 135H.2's existing intent barrier); **publication checkpoint** (recorded atomically with, or immediately after, the pointer swap itself); **post-publication continuation checkpoint** (recorded after local publication completes, before notification-intent processing begins); **notification checkpoint** (recorded after the external delivery attempt returns, capturing confirmed/uncertain/failed); **terminal receipt checkpoint** (recorded once receipt/marker finalization completes); and **rollback checkpoint** (recorded atomically with any rollback pointer-swap, §38).

**Which checkpoint is authoritative for recovery at each stage:** Stage 0–2, legacy's existing checkpoint mechanism remains authoritative for legacy's own recovery; CLTR's parallel checkpoints (where they exist, from Stage 2's rehearsal onward) are informative only, never consulted by legacy recovery. Stage 3+: the CLTR generation's own checkpoint sequence becomes the sole authority for recovery decisions (§25), and legacy's compatibility-output recovery, if any is still needed, is itself driven from the CLTR checkpoint state, not an independent legacy checkpoint.

---

## 31. Completion metadata migration

Completion metadata becomes **dual-derived** at Stage 1 (both legacy's existing `.pcae/phase-completion-metadata.json` writer and CLTR's shared-input-derived equivalent field populate independently from the same assembled input); **compared** at Stage 1 (per §11's `exact_identity_digest` mode, since metadata is one of the two kinds CLTR-SCHEMA-001 already promises a digest for); **generated from CLTR** at Stage 3 (the legacy metadata file becomes a rendering of the CLTR record's relevant fields, not an independent write); **compatibility-only** at Stage 4 (the file continues to exist and to be read by any tooling that expects it, but ceases to be independently authoritative for any fact); and **no longer independently authoritative** at Stage 5, in the sense that no code path computes it without consulting CLTR first (the file itself may still be written, for compatibility, as a deterministic derivative).

**Exact fields that must cease being inferred:** `phase_id`/`phase_name` (currently vulnerable to exactly the title-regex reconstruction 135D.1 investigated) must be sourced from the shared input package's transition identity (§8.3), never re-parsed from `.pcae/phase-completion-report.md`'s first line, at Stage 3 and beyond; recommended-next-phase and completion status must be sourced from the CLTR record's own classification fields, not independently asserted.

**Historical metadata remains preserved** — no prior phase's `.pcae/phase-completion-metadata.json` (or its git history) is rewritten by any stage of this migration.

---

## 32. Canonical phase report migration

The canonical phase report becomes **dual-derived** at Stage 1 (report content continues to be authored/assembled by legacy's existing report-generation logic; CLTR's shared input package captures the same `report_digest` and `report_id` for comparison, §11); **compared** at Stage 1 (`exact_identity_digest` mode per §11); **generated from CLTR-bound source data** at Stage 3 (report *content* generation begins consuming the CLTR record's bound evidence references rather than independently re-deriving them, while the thirteen-section PFR-001 structure itself is unchanged — this document does not alter PFR-001's section contract); **published inside the atomic generation** at Stage 2 (rehearsal) and mandatorily at Stage 3+ (§20); and becomes **a deterministic derivative rather than an independent lifecycle authority** at Stage 3+, in the sense that its content is computed from the CLTR record rather than the CLTR record being reconstructed from it (reversing today's implicit direction, where CLTR shadow observation reads `report_digest` *from* the already-produced report).

**PFR-001 is preserved** — all thirteen mandatory sections remain mandatory, the "PFN-001 notification payload" role of the report is unchanged, and this document introduces no weakening of report usability or Telegram compatibility at any stage; a report generated from CLTR-bound source data must satisfy PFR-001 exactly as today's legacy-generated report does.

---

## 33. Architecture Status migration

Architecture Status migrates away from narrative-derived current phase, completed phase, planned successor, chapter grouping, and lifecycle state, over the following path: Stage 1 — CLTR's shared input package captures the same transition identity Architecture Status narratively displays, enabling comparison (`normalized_semantic` mode, §11) without changing how Architecture Status is generated; Stage 2 — Architecture Status projection becomes one of the artifacts prepared (though not yet authoritatively sourced) inside the rehearsed atomic generation; Stage 3+ — Architecture Status becomes a deterministic CLTR derivative, generated *from* the CLTR record's `projected_state`/`certified_state`/`transition_id` fields (already classified as authority role **D**, deterministic derivative, in CLTR-001 §1.4/135D §9), eliminating the narrative-prose-parsing failure mode that caused the exact mislabeling 135C's own verification found ("Architecture Status '135A-135B' mislabel," root-caused to a title-extraction regex bug in `phase_reports.py`).

**Chapter titles may remain presentation metadata** — this document does not require chapter groupings to disappear — **but must never establish lifecycle identity**; at Stage 3+, a chapter title is rendering convenience only, never a fact a recovery or comparison path may depend on.

---

## 34. Git-attribution migration

Explicit migration path from current commit-ownership structures (currently always `unverifiable`, per 135K's disclosed limitation 4 and 135J's inherited F5) to CLTR-bound attribution: the three-outcome commit-verification model CLTR-001 §10.3/135A §8.2 already call for must be implemented (135O, per §4's disposition of this finding) so that commit ownership becomes a genuinely comparable field (`exact_identity_digest` or a dedicated comparison mode, to be specified by 135N) rather than perpetually `unverifiable`.

Prohibited at every stage of this migration, permanently: recent Git history fallback (walking `git log` to guess which commits belong to a phase); commit-subject parsing (matching prefixes like "Phase 135M:" as an authority signal); repository HEAD inference (treating the current HEAD as automatically attributable to the active transition without explicit binding); task-title inference (deriving commit ownership from the active task contract's title text); and bare hash hints appearing verified (a commit hash mentioned in a report or metadata field must never be treated as `verified` ownership without the three-outcome model's actual verification, matching 135G's B-8 finding — "bare `verified` commit hints trusted without repository/branch/revision binding" — remaining fixed, never regressed).

**Historical unverifiable ownership must remain explicitly unverifiable** — this document does not retroactively upgrade any prior phase's commit-ownership classification; 135A through 135L's commit-ownership records remain exactly as classified when they were produced.

---

## 35. Legacy authority inventory

Complete inventory of every current authority-like source, drawn directly from 135H §1's already-established 13-row table (reproduced and extended here with migration-stage columns per this document's own requirement):

| Source | Current authority | Future role | Migration stage | Demotion criteria | Retirement criteria | Compatibility requirement | Historical preservation |
|---|---|---|---|---|---|---|---|
| Canonical phase report | Duplicated authority (content + PFN-001 payload) | Deterministic CLTR derivative | Stage 3 | §36 | §37 | PFR-001 structure unchanged | Never rewritten |
| Completion metadata | Duplicated authority | Deterministic CLTR derivative | Stage 3 | §36 | §37 | File continues to exist | Never rewritten |
| Task state | Task-lifecycle authority (independent of CLTR) | Unchanged — task lifecycle is out of CLTR's scope; only the finalization-transaction boundary is in scope | N/A | N/A | N/A | Unchanged | N/A |
| Architecture Status | Derived authority with independent narrative inference | Deterministic CLTR derivative (role D, unchanged classification, now actually enforced) | Stage 3 | §36 | §37 | Chapter titles remain presentation metadata | Never rewritten |
| Promotion (`ArtifactState` machine) | Legacy promotion authority | Superseded by atomic generation publication (§20) | Stage 2 (rehearsed) / Stage 3 (authoritative) | §36 | §37 | Existing promoted artifacts remain readable | Never rewritten |
| Checkpoint | Canonical transaction/resume authority | CLTR generation's own checkpoint sequence (§30) | Stage 3 | §36 | §37 | Legacy checkpoint format remains readable for historical transitions | Never rewritten |
| Marker | Canonical terminal/idempotency authority for all four entry points | CLTR generation field (§28) | Stage 3 | §36 | §37 | File may remain permanently | Never rewritten |
| Finalization receipt | Canonical authority for narrow physical-delivery outcome | CLTR generation field (§29) | Stage 3 | §36 | §37 | File may remain permanently | Never rewritten |
| Git attribution | Currently unverifiable / narrative-inference-prone | CLTR-bound three-outcome model (§34) | Stage 1 (model implemented) / Stage 3 (authoritative) | §36 | §37 | N/A (attribution model is new, not a legacy artifact to preserve) | Historical unverifiable status preserved as-is |
| Reconciliation state (`pcae phase-report reconcile`) | Read-only cross-check authority for legacy generations | Extended to CLTR generations (§45) | Stage 2+ | §36 | §37 | Legacy reconciliation for pre-cutover phases remains available | Never rewritten |
| Latest pointers (`latest.md`/`latest.json`) | Mutable, independently-writable "latest" claim | Superseded by the single generation pointer (§22–§23) | Stage 3 | §36 | §37 | Legacy latest files may remain as compatibility views | Never rewritten |
| Recovery artifacts (`failures/*.json`, quarantine) | Diagnostic-only, never authoritative today (already correctly classified) | Unchanged role, extended to CLTR generation-level recovery (§25) | N/A (already correctly non-authoritative) | N/A | N/A | Unchanged | Never rewritten |
| Any other production representation capable of influencing lifecycle behavior | Case-by-case; none identified beyond the above during this phase's inspection | To be reassessed if discovered | Case-by-case | §36 | §37 | Case-by-case | Never rewritten |

---

## 36. Legacy demotion criteria

A legacy source may be demoted only when: an equivalent CLTR-derived output exists for that source's fact; comparison coverage is complete for that fact (all relevant representation kinds resolve non-`unverifiable` under real comparison sources, §11); the mismatch policy for that fact class has been proven stable through at least one full evidence window (§14–§15) with zero unresolved authority-relevant mismatches; recovery no longer depends on independent legacy inference for that fact (§25's recovery contract is satisfied using CLTR generation state alone); rollback remains possible (demoting a source must not eliminate the ability to roll back to legacy authority, §38); historical reading remains supported (the demoted source's historical instances remain readable exactly as before); all four entry points use shared input assembly for that fact (§16 — no entry-point-specific exception); exactly-once evidence is sufficient for that fact (§26); and no unresolved authority-relevant finding remains for that fact (§4's disposition table, applied per-fact at the time of the proposed demotion).

**Demotion must be explicit.** A named governed phase (135W or a successor) must state, per source, that demotion has occurred and why the criteria above are met. Silently ceasing to read a source — for example, simply removing a call site that used to consult legacy metadata — is never an acceptable migration action under this contract; the demotion must be documented with the same rigor as any other governed contract change.

---

## 37. Legacy retirement criteria

Retirement requires strictly stronger evidence than demotion: a minimum stable CLTR-authoritative operating window (duration to be derived and approved by the Stage 3 contract phase, 135S, using the same non-arbitrary-threshold discipline as §14); zero unresolved authority-relevant mismatches throughout that entire window (not merely at a single checkpoint); successful recovery drills repeated under CLTR authority (§25, exercised for real, not merely rehearsed); a successful rollback drill performed while CLTR was authoritative (proving rollback remains possible even after retirement is contemplated, before the retirement itself removes that possibility); historical compatibility validation (every pre-cutover historical read path continues to function); operator approval (separate and stronger than the cutover approval of §41 — a dedicated retirement-approval artifact); a release boundary if this project adopts one; a removal plan (naming exactly which independent-derivation code paths will be deleted); a deprecation notice (published ahead of removal, giving any external consumer of legacy formats advance notice); a documentation update (this document and its successors updated to reflect retirement, never silently); and a rollback-expiry decision (an explicit governed decision that rollback to the now-retired legacy path is no longer supported, since retirement by definition removes the code that would make rollback possible — see §38's roll-forward-preference discussion for why this decision must be deliberate).

**No legacy authority is retired in 135M.** This phase performs no retirement of any kind; the criteria above bind only the future phase(s) that eventually attempt retirement.

---

## 38. Rollback architecture

Rollback is defined separately per migration stage, because the safe rollback action differs by stage:

- **Stage 1 rollback:** disable dual derivation via feature flag (§42); CLTR derivation stops; legacy authority is unaffected throughout (it was never not authoritative). No pointer, generation, or authority-epoch change is needed — this is the cheapest possible rollback and requires no special mechanism beyond the flag itself.
- **Stage 2 rollback:** disable publication rehearsal via a separate flag (§42); revert to Stage 1 behavior (dual derivation continues, but joint atomic publication rehearsal stops). No production authority was ever at stake during rehearsal, so this rollback is also cheap.
- **Stage 3 rollback:** returning pointer authority from CLTR to legacy-authoritative operation — this is the first rollback that changes which derivation is authoritative. It requires: restoring a prior verified generation (or resuming legacy's independent derivation path, which must not yet have been deleted, per the demotion-before-retirement ordering in §36–§37); pausing external delivery continuation if a delivery was in flight at the moment of rollback decision (never attempting to "unsend" an already-attempted delivery, §19); preserving mismatch evidence (never deleted by a rollback); preserving CLTR generations already published (never deleted — rollback changes future authority, not past record); preserving audit history (the migration-evidence record, §16, is never purged by rollback); and re-establishing a new migration epoch segment (§17) so that evidence from before and after the rollback is never silently pooled.
- **Stage 4/5 rollback:** governed by the rollback-expiry decision of §37 — once retirement has occurred, rollback to legacy authority may no longer be possible by design (the independent derivation code has been removed), and this must have been an explicit, disclosed decision made before retirement, never discovered as a surprise afterward.

**Rollback must never rewrite history at any stage.** A rollback is always a new, forward-in-time governed action (a new pointer publication, a new authority-epoch record) — never an edit to a previously published generation, checkpoint, report, or metadata file.

---

## 39. Roll-forward preference

Roll-forward is safer than rollback specifically: after external notification delivery has already been attempted (rolling back cannot un-send a message; the correct response to a problem discovered after delivery is to roll forward with a corrective transition, exactly as 135H.1's own recovery — "one corrective terminal notification" — already demonstrated for a legacy-only incident); after marker creation (the marker's terminal claim, once made, is addressed by a corrective forward transition, not erased); after receipt finalization (same reasoning); after irreversible Git publication (a pushed commit is not un-pushed by this migration's rollback mechanism — Git-level reversal, if ever needed, is a separate, explicitly authorized action outside this contract's scope, matching this session's own governance rules against force-push/history-rewrite); and after an authority-epoch change has itself been externally observed or acted upon (e.g., if a downstream consumer has already begun trusting CLTR-authoritative output, reverting the epoch without their knowledge could itself create confusion — roll-forward with a disclosed epoch change is preferred).

This document does not prescribe rollback across any of the irreversible boundaries above, because doing so would create false history (an artifact appearing to say something never actually true at the time). Reconciliation (§45) and forward completion (a new, corrective, forward-dated transition) are the required mechanisms in these cases instead.

---

## 40. Authority epoch

An explicit authority epoch (or authority version) identifies: legacy-authoritative operation (Stage 0–2); CLTR-authoritative operation (Stage 3+); rollback to legacy (a new epoch segment, per §38); resumed CLTR authority (another new epoch segment, following a roll-forward after a rollback); contract/schema version (which CLTR-001/CLTR-SCHEMA-001 version was in force); and migration epoch (§17 — a distinct, coarser-grained identifier that can span multiple authority-epoch changes).

**Every publication generation discloses its authority epoch** — this is a mandatory field of the atomic generation contract (§20), not an optional annotation, ensuring that any later inspection of a generation can determine, without external context, which derivation was authoritative when that generation was produced.

---

## 41. Cutover approval

Authority cutover (entry into Stage 3) requires explicit governed operator approval — never an implicit consequence of a feature flag alone. The approval artifact must record: the approver's identity class (a human operator, not an automated process); the evidence reviewed (citing the specific 135R/135T verification verdicts and evidence-window results, §7); the findings reviewed (every open finding from §4 and any findings from 135N/135O/135P/135Q/135R, with explicit confirmation that none remain classified "must resolve before cutover" and unresolved); the cutover stage being entered; the effective transition or phase boundary at which cutover takes effect (never "immediately, ambiguously" — a specific, named transition boundary); rollback readiness (explicit confirmation that §38's Stage 3 rollback mechanism has been drilled and is ready); an approval expiry (a stated validity window after which the approval must be re-confirmed if cutover has not yet been exercised, preventing a stale approval from authorizing cutover long after the evidence it was based on has gone stale); and revocation behavior (an explicit mechanism by which the approval can be withdrawn before it takes effect).

**No implicit cutover through a feature flag alone.** This document requires the cutover-approval artifact to exist and be valid as a *separate* precondition from any flag's on/off state (§42) — flipping `PCAE_CLTR_AUTHORITY_ENABLED` (or whatever flag 135S ultimately names) without a valid approval artifact must be treated as an invalid configuration (§42.1).

---

## 42. Feature-flag architecture

Separate flags are required for: shadow observation (`PCAE_CLTR_SHADOW_ENABLED`, already existing, unchanged); dual derivation (a new flag, to be named by 135O, gating Stage 1 behavior); comparison enforcement (a new flag, potentially the same as the dual-derivation flag or a finer-grained sibling, gating whether comparison results are persisted as migration evidence, §16); atomic publication rehearsal (a new flag, gating Stage 2's joint-generation rehearsal, independent of dual derivation itself); CLTR authority cutover (a new flag, gating Stage 3, which must never be enableable without a valid cutover-approval artifact, §41); legacy comparison (a flag or sub-configuration controlling whether legacy's independent derivation continues to run for comparison purposes during Stage 3+, as required by the Stage 3 definition in §6); and rollback (a control surface, not necessarily a boolean flag, that reverts the authority epoch, §38).

**A single Boolean must not control the entire migration.** Each flag above must: be explicit (named for exactly what it gates, never a generic "CLTR mode" toggle); have safe defaults (off, matching every CLTR flag introduced so far); disclose active stage (the current combination of flag states must be inspectable via the planned read-only status command, §44); prevent invalid combinations (§42.1); be bound to migration and authority epochs (§17, §40 — enabling a flag records which epoch it took effect under); and never silently grant execution capability (no flag introduced by this migration plan, at any stage, enables subprocess execution, backend invocation, or shell mediation — this remains true through every stage, per §46).

### 42.1 Invalid configuration

Fail-closed handling is required for: CLTR authority enabled without atomic publication implemented (must refuse — Stage 3 structurally depends on Stage 2's mechanism existing); legacy authority disabled without CLTR validation proven (must refuse — there must always be exactly one authoritative source, §6); notification migration enabled without stable idempotency (must refuse — §27 requires this precondition); cutover enabled without an approval artifact (must refuse, per §41, regardless of flag state); retirement enabled before demotion criteria are met (must refuse, per §36–§37's ordering requirement); and rollback requested across a prohibited irreversible boundary (must refuse and redirect to roll-forward, per §39, rather than silently attempting an unsafe rollback).

**Invalid migration configuration must never be normalized into an unsafe state** — where an invalid combination is detected, the correct behavior is an explicit refusal with a clear message, never a best-effort interpretation that picks one of the conflicting configurations silently.

---

## 43. Historical compatibility

Lifecycle evidence created before CLTR production authority existed may be: native CLTR (produced by a CLTR-authoritative transition, Stage 3+); shadow CLTR (produced by Stage 0's observational mechanism, 135K/135L-era); migrated compatibility envelope (a legacy artifact wrapped, at read time, in a compatibility view that discloses it was never CLTR-native, matching the "Compatibility/legacy-format view" representation kind already frozen in CLTR-SCHEMA-001 §5/§21.4); legacy-only (produced before Track 135 began, with no CLTR observation at all — every phase before 135K); incomplete (a shadow or dual-derivation record whose adapters could not fully resolve, e.g. today's 11/15 `unverifiable` results); unverifiable (explicitly marked as such, never silently treated as verified); or superseded (a corrected record, via `predecessor_transition_id`/`successor_transition_id`, already frozen fields).

**Historical evidence is never rewritten as though CLTR had been authoritative at the time it was created.** A phase completed under Stage 0 (shadow-only) is never later relabeled as though it had passed through Stage 3's CLTR-authoritative validation; its provenance (which stage/epoch produced it) is a permanent, disclosed fact about that record.

---

## 44. Schema/version migration

Behavior is defined for: a CLTR-SCHEMA-001 compatible patch during migration (per §2.1's existing PATCH definition — no migration-stage impact, since PATCH has zero wire-format effect by definition); a minor version adding noncritical fields (existing readers at any migration stage must continue to function per §2.2's forward-compatibility rule; new fields may be consumed by comparison logic only once explicitly wired, never assumed present); a major version changing wire semantics during migration (must trigger a new migration epoch, §17, and must not be adopted mid-evidence-window without explicit re-evaluation of all thresholds derived under the prior major version); migration in progress during a schema change (the in-progress evidence window's migration-evidence records disclose which schema version produced them; comparison across the boundary uses explicit adapters, never an assumption that old and new records mean the same thing); comparison spanning different compatible (same-major) versions (permitted, using each record's own `schema_version` for interpretation per §2.2); and a rollback crossing schema versions (must be treated with the same epoch-segmentation discipline as any other rollback, §38, plus explicit schema-version disclosure in the new epoch's evidence).

**Evidence from incompatible schema contracts is never merged without explicit adapters and disclosed limitations** — this generalizes §17's epoch-segmentation rule to schema-version boundaries specifically.

---

## 45. Observability

Migration observability must expose: active migration stage (§6); migration epoch (§17); authority epoch (§40); feature-flag configuration (§42); evidence-window progress (§14–§15); comparison counts (per §12 class); mismatch counts by class (§12); unresolved findings (§4, kept current as new findings are dispositioned by later phases); publication health (§20, §22); recovery health (§25); notification uncertainty (§19, §27); rollback readiness (§38); cutover eligibility (§7, §41); legacy demotion eligibility (§36); and legacy retirement eligibility (§37).

**Observability remains derivative** — none of the observability surfaces described in this section, nor the two read-only commands planned in §46–§47, may themselves become an authority for any lifecycle fact; they read and report, they never decide.

---

## 46. Planned read-only status

A future read-only command, `pcae cltr migration status`, is planned (not implemented in 135M) to report: migration stage; authority source; migration epoch; authority epoch; evidence counts; comparison result counts; blockers (open findings preventing the next stage transition); pending approvals; rollback readiness; cutover eligibility; and `mutation: none` (explicitly disclosed, matching the existing convention `pcae phase-report reconcile` already established — "Mutation: none (inspection only)"). This command is 135N/135O-scope design work at earliest; it is not implemented by this phase.

---

## 47. Planned read-only reconciliation

A future read-only command, `pcae cltr migration reconcile --phase-id <PHASE_ID>`, is planned (not implemented in 135M) to inspect: the shared input package (§9); both derivations (§10); comparison evidence (§11–§12); the publication generation (§20); the pointer (§22); the checkpoint (§30); notification intent and outcome (§19, §27); the marker (§28); the receipt (§29); blockers; and the authority stage in force at the time. Its `mutation: none` guarantee is absolute: **reconciliation must never repair, replay, promote, dispatch, or cut over authority** — it is the direct extension of `pcae phase-report reconcile`'s already-established read-only discipline (135H.2 §7: "The command is read-only by construction and reports `mutation_performed: false` and `redispatch_performed: false`") to the CLTR migration domain.

---

## 48. Security and containment

Migration controls must guard against: path traversal and symlink escape in generation/pointer paths (already enforced for shadow generations via `_safe_generation_dir()`, `persistence.py:76-91`; this discipline must extend unchanged to every new generation/pointer path this migration introduces); pointer substitution (a pointer must only ever be updated via the atomic, verified sequence of §22, never a direct external write); generation substitution (a generation's manifest/digest must be re-verified before any pointer references it, §22); manifest substitution (the manifest is itself digested and embedded in the generation's overall digest chain, matching CLTR-SCHEMA-001 §15); migration-evidence substitution (the migration-evidence record, §16, is itself digested); wrong-epoch evidence (§17's epoch-segmentation prevents silent cross-epoch pooling); wrong-phase evidence and wrong-transition evidence (both prevented structurally by §8.3's resolved transition-identity design); digest substitution (SHA-256 with mismatch treated as tamper/corruption evidence, never silent acceptance, per CLTR-SCHEMA-001 §15.5, unchanged); fabricated commit ownership (prevented by §34's prohibition on unverified attribution shortcuts); stale configuration (feature-flag combinations validated per §42.1); unauthorized cutover (prevented by §41's mandatory approval-artifact requirement); unauthorized rollback (rollback itself must be a governed, approved action — this document does not specify an approval artifact identical to cutover's for rollback, and 135S/135T must decide whether rollback requires the same approval rigor as cutover or a lighter, faster-acting governed process appropriate to its safety-net role); replay (prevented by the at-most-once discipline of §24/§26); duplicate publication (prevented by the atomic pointer contract of §22); and duplicate external delivery (prevented by PFN-001's existing idempotent-dispatch guarantee, unchanged and unweakened by this migration).

---

## 49. Runtime boundary

The migration design preserves, at every stage defined in this document: runtime state Observed; maximum capability observe; execution capability unavailable. CLTR authority migration is lifecycle-*governance* migration — it changes which artifact is authoritative for recording what already happened during a finalization transaction that a human-and-tool-mediated CLI command already initiated. **It is not execution enablement.**

This document introduces, and will introduce at no future stage without a wholly separate, explicitly-scoped governance phase: no shell execution; no subprocess mediation; no backend invocation; no execution adapters; no Telegram inbound control; no automatic apply; and no commit/push authority beyond what already exists in this repository's existing governed CLI commands (`pcae task`, `pcae phase`, `git` invoked only through those governed commands, never directly by CLTR machinery).

---

## 50. All four entry points

For every migration stage defined in §6, all four production finalization entry points — `pcae phase complete` (`run_phase_complete`, `commands/phase.py`), `pcae task finish` (`run_task_finish`, `commands/task.py`), `pcae phase-report create` (`run_phase_report_create`, `commands/phase_reports.py`), and `pcae notify send-report` (`run_notify_send_report`, `commands/notifications.py`) — must use: one shared input assembler (§9, not four independent assemblies); one migration-stage resolver (a single source of truth for "which stage is active right now," consulted identically by all four entry points, never computed independently per entry point); one dual-derivation coordinator (orchestrating steps 4–9 of §21's sequence identically regardless of which entry point invoked it); one comparison contract (§11–§12, unchanged across entry points); one publication contract (§18–§23, unchanged across entry points); and one recovery contract (§25, unchanged across entry points).

**No entry-point-specific authority semantics are permitted.** This directly extends 135K's own design principle — already verified by 135L (`_observe_shadow_cltr` is called from exactly one place inside `run_finalization_transaction()`, with only the `entry_point` string varying per caller) — through every future migration stage: the four entry points may differ in *what triggers* a finalization transaction, never in *how* that transaction is governed once triggered.

---

## 51. Ordinary and recovery path behavior

Migration behavior is defined identically (per §25's recovery contract, applied per path) for: ordinary finalization (the common case — ordinary `phase complete`/`task finish`); task-finish finalization (identical to ordinary, entry-point identity disclosed per §50); phase-complete finalization (identical, entry-point identity disclosed); allow-partial-report recovery (`--allow-partial-report`, already hardened by 135H.2 against the promotion-authority-leak defect it originally exposed — this migration's dual derivation must observe this path exactly as any other, with recovery classification disclosed in the shared input package, §8.1); manual governed recovery (matching 135H.1's precedent — a manual, one-time corrective transition; dual derivation must be able to represent this classification explicitly, not force it into an "ordinary" bucket); paused-task handling (task-lifecycle state, not itself CLTR's concern, but must never be used as a fallback-inference source for CLTR identity, §8.2); stale-metadata conflict (must trigger the same staleness guard 135D.1 introduced, extended conceptually to any CLTR-derived metadata equivalent at Stage 3+); promotion uncertainty (`promotion_outcome_unconfirmed`, per 135H.2, must be representable identically in the shared input package's recovery-classification field); missing terminal artifacts (matching 135H.1's incident class — the shared input assembler must fail closed, not silently proceed, when mandatory terminal artifacts are absent, §9); and read-only reconciliation (§47 — never itself a finalization path, always observational).

**Recovery paths must meet the same authority and atomicity contract as ordinary finalization** — restated here because it is the specific requirement this section (§48 of the phase's own numbered requirements) calls out, and it is satisfied by §25's recovery contract applying uniformly, with no separate, weaker recovery-path authority model at any stage.

---

## 52. Adversarial acceptance criteria

Before any authority cutover (entry into Stage 3), successful drills are required for: wrong phase (a shared input package accidentally or maliciously bound to the wrong `phase_id` must be rejected by the assembler's own validation, §9); wrong transition (same, for `transition_id`, per §8.3's identity design); wrong generation (a pointer or reconciliation request referencing a generation identity that does not match the manifest it retrieves must fail closed, §22); wrong digest (any digest mismatch is tamper/corruption evidence, never silently accepted, §48); wrong commit ownership (the three-outcome model, §34, must correctly reject a fabricated or mismatched commit reference); stale metadata (the staleness guard introduced by 135D.1 must be proven to still function against the CLTR-era metadata equivalent); stale task identity (a task contract whose identity does not match the transition being finalized must be rejected, not silently reconciled); missing certified content (a candidate lacking mandatory certified fields must never be published, matching CLTR-SCHEMA-001 §6's state-dependent presence table); pointer failure (a corrupted or dangling pointer must be detected and must not silently repair itself into an unverified state, §22); crash before publication (recovery must correctly identify "no candidate created" or "candidate incomplete," §25, and take no unsafe action); crash after publication (recovery must correctly identify "local publication complete" and proceed only to the next legitimate step, never re-publish); external delivery uncertainty (reconciliation, never blind resend, §19/§27); duplicate finalization invocation (two near-simultaneous invocations of the same entry point for the same transition must not produce two distinct authoritative outcomes — exactly-once, §26); duplicate notification attempt (same, for notification specifically, matching PFN-001); marker failure (a marker write failure must be recoverable without producing a false terminal claim, §28); receipt failure (same, for receipt, §29); rollback request (a rollback request must be correctly executed or correctly refused per §38's stage-specific rules, never silently ignored or silently over-executed); unsupported schema version (must fail closed per CLTR-SCHEMA-001 §2.7, unchanged); incompatible feature flags (must be refused per §42.1); and operator approval absence (a cutover attempt without a valid approval artifact must be refused outright, §41).

Each of these drills is a required acceptance test for 135R (Atomic Publication and Recovery Independent Verification) and 135T (Cutover Contract Verification) to design and execute — not performed by 135M itself, which performs no implementation.

---

## 53. Recommended staged implementation sequence

135M recommends the following sequence rather than one broad implementation phase, per this phase's explicit instruction not to combine implementation and independent verification in any single phase:

- **135N** — Production CLTR Dual-Derivation and Migration Contract Verification (independently re-derive and verify *this* document before any implementation begins; resolves the `transition_id` identity design of §8.3 and any other open design choice this document explicitly defers to 135N).
- **135O** — Shared Transition Input and Dual-Derivation Implementation (implements §8–§10; resolves F-135L-1, F-135L-2, and the commit-ownership limitation from §4's disposition table).
- **135P** — Dual-Derivation Independent Verification (independently verifies 135O; no implementation).
- **135Q** — Atomic Publication Rehearsal Implementation (implements §18–§25 in rehearsal form, Stage 2; derives the evidence thresholds §14 defers).
- **135R** — Atomic Publication and Recovery Independent Verification (independently verifies 135Q, including the adversarial drills of §52 applicable to rehearsal; no implementation).
- **135S** — CLTR Authority Cutover Contract Freeze (a separate contract, per §6 Stage 3's own explicit requirement; defines the Stage 3 evidence window, the cutover-approval artifact's exact schema, and the notification/marker/receipt authority transfer of §27–§29 in binding detail).
- **135T** — CLTR Authority Cutover Contract Verification (independently verifies 135S; no implementation).
- **135U** — Staged CLTR Authority Cutover Implementation (implements Stage 3, gated on an executed cutover-approval artifact per §41; the first phase in this sequence permitted to change production lifecycle authority).
- **135V** — Authority Cutover Independent Verification (independently verifies 135U, including the full adversarial drill set of §52; no implementation).
- **135W** — Legacy Authority Demotion Plan or Implementation (Stage 4, gated on §36's criteria).
- A later, currently unscheduled phase for legacy retirement (Stage 5), gated on §37's criteria and requiring evidence and stable operation this document cannot yet quantify.

The exact phase letters above are not binding if a future phase derives a safer sequence; the binding requirement is the ordering discipline itself — contract before implementation, implementation before independent verification, and no phase combining implementation with its own independent verification.

---

## 54. Cross-reference matrix

| Migration rule (this document) | CLTR-001 | CLTR-SCHEMA-001 v1.0.1 | 135D | 135G | 135H | 135H.2 | 135J | 135K | 135L | PFN-001 | PFR-001 | Rule type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| §2 One authority per stage | §4.1 primary invariant | — | §9 cross-representation model | — | §7.2 nine-stage strategy | — | — | — | — | — | — | Inherited semantic rule |
| §6 Six-stage model | — | — | — | — | §7.2 (source of the nine-stage strategy this document compresses to six) | — | — | — | §48 recommendation | — | — | Migration encoding decision |
| §7 Entry/exit gates | §14.1 immutability principles | §17.1 nine-step sequence | — | B-1..B-8 hazard classes | §7.1 cutover prerequisites | — | — | — | — | — | — | Migration clarification |
| §8 Shared input contract | §4.2 forbidden competing-authority patterns | §7 required fields | — | NB-1 comparator breadth | §9 (input-assembly precursor discussion) | — | — | §5 (`ShadowTransitionInput`) | §26 (single construction site) | — | — | Implementation guidance |
| §9 Shared input assembler | §14.1 item "immutable once certified" | — | — | — | — | §4 promotion-intent barrier (model reused) | — | — | — | — | — | Migration encoding decision |
| §10 Isolation | — | §21.2 determinism/no-silent-upgrade | — | B-3, B-4 | — | — | — | §16 exception containment | §45 F-135L-1/2 | — | — | Inherited semantic rule |
| §11–§12 Comparison contract/classes | — | §21.1, §21.4 (reused unmodified) | — | NB-1 | §12 NB-1 elevation | — | F1 (repair precedent) | — | — | — | — | Cutover prerequisite |
| §13 Mismatch policy by stage | §4.1 | — | §6 forbidden transitions | — | — | — | — | — | — | — | — | Migration encoding decision |
| §14–§15 Evidence thresholds/window | — | — | — | — | §7.1 | — | — | — | §48 recommendation | — | — | Migration clarification (thresholds deferred) |
| §16 Migration evidence record | §4.2 (never itself authority) | §15 digest contract (model reused) | — | — | — | §7 reconciliation model | — | — | — | — | — | Migration encoding decision |
| §17 Migration epoch | — | §2 versioning (model extended) | — | — | — | — | — | — | — | — | — | Migration encoding decision |
| §18–§20 Atomic publication/generation | — | §16 persistence contract, §5/§21.4 15 kinds | §9 representation matrix | — | §7.1 (atomic `latest.*` cited as gap) | — | F5 (inherited gap) | — | F-135L-3 (precedent hazard) | — | §3 structure (report content unaffected) | Cutover prerequisite |
| §21 Candidate preparation sequence | — | §17.1 nine-step sequence (extended to eighteen) | — | — | — | — | — | — | — | — | — | Implementation guidance |
| §22–§23 Pointer/split-brain | — | §16.3 current pointer | — | B-2 | — | — | — | `persistence.py` (`_publish_current_pointer`) | F-135L-3 | — | — | Cutover prerequisite |
| §24 Publication failure model | §14.1 | §16.2 immutability | — | B-2 | — | §1 promotion-authority-leak repair (model extended) | — | — | — | — | — | Inherited semantic rule |
| §25 Recovery contract | §12.3 no independent reconstruction | — | — | — | — | §7 `pcae phase-report reconcile` | — | — | — | — | — | Inherited semantic rule |
| §26 Exactly-once | §14.1 | — | — | — | — | §1–§4 (direct source) | — | — | — | §8 idempotent dispatch | — | Inherited semantic rule |
| §27 Notification migration | — | — | — | — | §1 marker/notification duplication | — | — | — | — | §4, §5, §7, §8 (all directly binding, unchanged) | §2 (payload role) | Cutover prerequisite (notification-related) |
| §28 Marker migration | — | §21.4 row 9 (`normalized_semantic`) | — | — | §1, §2 (marker as retirement target) | — | — | — | — | — | — | Migration clarification |
| §29 Receipt migration | — | §21.4 row 10 | — | — | §1 (narrow receipt authority) | §7 (`delivery_recorded_bookkeeping_incomplete`) | F3 | — | — | — | — | Migration clarification |
| §30 Checkpoint migration | — | §21.4 row 5 | — | — | §1 | §1 (checkpoint barrier model) | — | §9, §13 | — | — | — | Migration clarification |
| §31 Completion metadata migration | §4.2 item (metadata status forbidden as competing authority) | §21.4 row 2 | — | — | §1 | — | — | — | — | — | — | Cutover prerequisite |
| §32 Report migration | — | §21.4 row 1 | — | — | — | — | — | — | — | §4/§5 (payload role) | §2, §3 (structure, unaffected) | Cutover prerequisite (report-related) |
| §33 Architecture Status migration | §1.4/135D §9 (role D) | §21.4 row 3 | §9 (role D classification, source) | — | — | — | — | — | 135C precedent (mislabel root cause) | — | — | Inherited semantic rule |
| §34 Git-attribution migration | §10.3 | §10 (three-outcome model, deferred) | — | B-8 | §7.1 | — | F5 | limitation 4 | — | — | — | Cutover prerequisite |
| §35 Legacy authority inventory | — | — | — | — | §1 (direct source, 13-row table) | — | — | — | — | — | — | Inherited semantic rule |
| §36 Demotion criteria | — | — | — | — | §2, §7.1 (source) | — | — | — | — | — | — | Cutover prerequisite |
| §37 Retirement criteria | — | — | — | — | §2 ("fact-scoped, not file-scoped," direct source) | — | — | — | — | — | — | Cutover prerequisite |
| §38–§39 Rollback/roll-forward | — | — | — | — | §7.2 (rollback-available design goal) | — | — | — | — | §8 idempotent dispatch (roll-forward rationale) | — | Migration encoding decision |
| §40 Authority epoch | — | §1.1 (`schema_version`/`compatibility_id` model reused) | — | — | — | — | — | — | — | — | — | Migration encoding decision |
| §41 Cutover approval | — | — | — | — | §7.1 (independent cutover review cited) | — | — | — | — | — | — | Cutover prerequisite |
| §42 Feature flags | — | — | — | — | — | — | — | §17 (`PCAE_CLTR_SHADOW_ENABLED`, precedent) | §41 flag-on/off verification (precedent) | — | — | Migration encoding decision |
| §43 Historical compatibility | §14.1 | §5/§21.4 (compatibility/legacy-format view kind) | — | — | §2 (no historical rewrite) | — | — | — | — | — | — | Inherited semantic rule |
| §44 Schema/version migration | — | §2 (direct source) | — | — | — | — | — | — | — | — | — | Inherited semantic rule |
| §45 Observability | — | — | — | — | — | §7 (reconciliation model) | — | §11 (`pcae cltr shadow status`, precedent) | — | — | — | Implementation guidance |
| §46–§47 Planned read-only commands | — | — | — | — | — | §7 (`pcae phase-report reconcile`, direct precedent) | — | — | — | — | — | Implementation guidance |
| §48 Security/containment | — | §2.6/§2.7, §15.5 | — | B-1, B-5, B-6, B-7, B-8 | §13 (inherited-hazards table) | — | — | `_safe_generation_dir` (precedent) | — | — | — | Inherited semantic rule |
| §49 Runtime boundary | — | — | — | — | — | — | — | — | — | — | — | Cutover prerequisite |
| §50 Four entry points | — | — | — | — | — | — | — | §15 (direct source) | §26 (verification) | — | — | Inherited semantic rule |
| §51 Ordinary/recovery paths | — | — | — | — | — | §1–§7 (direct source) | — | — | — | — | — | Inherited semantic rule |
| §52 Adversarial acceptance | — | §2.7, §15.5 | — | B-1..B-8 (direct precedent) | §13 | §1 (promotion-leak precedent) | — | — | — | — | — | Cutover prerequisite |

---

## 55. Risk register

| Risk | Likelihood | Impact | Affected stage | Prevention | Detection | Response | Acceptance criteria |
|---|---|---|---|---|---|---|---|
| Dual-authority risk (both legacy and CLTR treated as binding simultaneously) | Low, if §6/§13 are followed | Very high | All stages | §6's explicit single-authority-per-stage model; §13's stage-dependent mismatch policy | Migration-evidence record (§16) discloses "production authority at the time" per transition; any ambiguity is itself a detectable anomaly | Immediate governed review; treat as a Blocking defect in whichever phase introduced it | Zero instances across every evidence window before any stage progression |
| Split-brain publication (divergent pointers/generations) | Low post-§20/§22 implementation; **already observed once in legacy tooling** (F-135L-3) | High | Stage 2+ | §20 atomic generation contract; §22 pointer contract; §23 explicit split-brain prevention list | Reconciliation command (§47) detects digest/identity mismatch across bound artifacts | Fail closed; do not publish; investigate before retry | Zero unresolved split-brain instances through the full Stage 2 rehearsal window |
| Mismatch normalization (silently treating a real mismatch as expected) | Medium — the `expected_representation_difference` class (§12) is precisely the mechanism this risk could abuse if governed carelessly | High | Stage 1+ | §12 requires operator review on first occurrence of any new expected-difference pattern; §13 requires every mismatch persisted, never silently ignored | Migration-evidence record audit; recurring review of `expected_representation_difference` counts for unexplained growth | Governed review of the expected-difference catalog; tighten classification if abuse is found | No `expected_representation_difference` classification is added without an explicit, reviewed, documented explanation |
| Evidence-window bias (volume from one easy path substituting for real coverage) | Medium, without explicit design discipline | Medium–high | Stage 1→2, 2→3 | §15's explicit requirement that entry-point and recovery-path coverage gate independently, not merely average into an aggregate count | 135Q/135R's evidence-window design must expose per-entry-point and per-recovery-path counts, not only an aggregate | Refuse stage progression until genuine coverage exists across all four entry points and at least one recovery path | §16's evidence-window design explicitly verified by 135R before any threshold is trusted |
| Atomicity overclaim (describing external delivery as filesystem-atomic) | Low, if §19 is followed; historically a real risk pattern in distributed-systems design generally | High (would silently violate PFN-001's honesty requirement) | Stage 2+ | §19's explicit local/external separation, stated as a permanent architectural boundary, never revisited as "solved" by a future optimization | Code review / contract-conformance review at every future phase touching publication | Reject any implementation or document claiming external-delivery atomicity | §19's separation remains unweakened in every future phase's own contract text |
| External delivery uncertainty (network partition mid-delivery) | Medium (inherent to any network delivery) | Medium (already contained by PFN-001/135H.2's existing reconciliation discipline) | All stages | §19, §26 reconciliation-not-replay discipline (already proven in production by 135H.2) | `pcae notify status`-equivalent / reconciliation command | Reconcile, never blind resend | Zero duplicate deliveries across any evidence window |
| Exactly-once regression (a migration change accidentally reintroducing a duplicate-completion path) | Low–medium, given 135H.2's precedent defect class | Very high | Stage 1+ (any phase touching `run_finalization_transaction` or its successors) | §26's explicit exactly-once contract per logical operation; adversarial drills §52 | Regression test suite (135P/135R/135T each add dedicated tests, per their own verification scope) | Treat as Blocking; do not progress until repaired and re-verified | Zero exactly-once violations in every evidence window, permanently |
| Rollback across irreversible state (attempting to "undo" an already-delivered notification) | Low, if §38–§39 are followed | High (would create false history or a duplicate delivery) | Stage 3+ | §39's explicit roll-forward-preference list | Rollback-request handling must check irreversible-boundary conditions before acting (§42.1 invalid-configuration handling) | Refuse the rollback; require roll-forward instead | Rollback mechanism never attempts an action §39 prohibits, verified by 135T's adversarial drills |
| Legacy fallback persistence (a demoted source quietly continuing to be consulted somewhere) | Medium — large systems often retain a stray call site | Medium–high | Stage 3+ | §36's explicit, per-fact, per-entry-point demotion requirement (no entry-point-specific exception, §50) | Code-level audit at 135W; comparison evidence would itself reveal ongoing legacy-authoritative behavior as a mismatch | Treat any discovered fallback as a Blocking defect; do not consider demotion complete until removed | 135W's own verification confirms no remaining call site independently derives a demoted fact |
| Hidden narrative inference (title/commit-subject/Git-history reconstruction reappearing) | Medium — this is precisely the class of defect 135D.1 already found once | High (proven capable of causing real, if transient, corruption) | All stages | §8.2, §25, §34's explicit, repeated prohibitions | Code review at every implementation phase; the staleness guard pattern from 135D.1 as a template | Treat as Blocking; repair immediately; add a regression test naming the specific fallback path found | Zero instances found by 135N/135P/135R/135T/135V's own adversarial review |
| Entry-point semantic drift (one entry point quietly gaining different authority semantics) | Low, given §50's explicit shared-coordinator requirement | High | All stages | §50's explicit "no entry-point-specific authority semantics" rule | Comparison evidence segmented by entry-point identity (§16) would reveal drift as a pattern | Treat as Blocking; unify behavior; add regression coverage per entry point | Every evidence window shows no systematic per-entry-point divergence pattern |
| Schema migration during cutover (a CLTR-SCHEMA-001 version change coinciding with Stage 3 entry) | Low (schema changes are already rare and governed) | High if it occurs | Stage 3 transition specifically | §44's explicit schema/version migration rules; §41's cutover-approval artifact must disclose the schema version cutover is being approved against | 135T's verification must explicitly confirm schema stability through the cutover window | Delay cutover until schema version is stable for the full evidence window | No schema version change occurs during the Stage 2→3 evidence window without an explicit, separately-approved epoch transition |
| Feature-flag invalid combinations | Medium, given the number of flags introduced across stages (§42) | Medium–high | All stages | §42.1's explicit fail-closed invalid-configuration list | Configuration validation at startup/command invocation | Refuse to proceed; clear error message naming the invalid combination | 135O/135Q/135S each add explicit tests for every invalid combination named in §42.1 |
| Historical evidence rewriting | Low, given explicit prohibitions throughout (§36, §37, §39, §43) | Very high (would violate the project's core historical-integrity principle) | All stages | Every section touching historical data explicitly states "never rewritten" | Any write path touching a previously-published generation, report, or metadata file outside the append-only/new-generation pattern is itself a defect | Treat as Blocking at the highest severity; halt migration until root-caused | Zero instances across the entire migration, verified at every independent-verification phase |
| Operator approval bypass | Low, given §41/§42.1's explicit binding | Very high | Stage 3 transition | §41's mandatory, separately-checked approval artifact; §42.1's fail-closed handling of "cutover enabled without approval artifact" | Configuration/state audit before cutover is exercised | Refuse cutover; require a valid approval artifact | 135U cannot be exercised without 135T confirming a valid, unexpired approval artifact exists |
| Premature legacy retirement | Low, given §37's explicit, stronger-than-demotion evidence bar | Very high (irreversible) | Stage 4→5 | §37's explicit criteria list, requiring evidence beyond demotion | Any retirement attempt is reviewed against the full §37 checklist before any code removal occurs | Refuse retirement; continue operating in Stage 4 until criteria are met | The unscheduled retirement phase explicitly confirms every §37 criterion, not a subset |

---

## 56. Recommended next phase

135M freezes a complete, internally consistent, single-authority migration contract with no unresolved Blocking gap for this planning phase's own scope. Every finding inherited from 135J, 135K, and 135L has an explicit disposition (§4); every required contract area (terminology through security/containment, §5–§54) is defined; no section defers a decision without naming the exact future phase responsible for resolving it.

**Recommended next phase: 135N — Production CLTR Dual-Derivation and Migration Contract Verification.**

135N must independently re-derive and verify this migration contract — including resolving the `transition_id` identity design this document explicitly defers (§8.3) — before any dual-derivation implementation (135O) begins. Per this phase's explicit instruction: do not proceed directly from planning to implementation. 135M stops here. Phase 135N is not begun by this document.

---

## Strict non-goals confirmation

This phase did not: implement dual derivation; modify production lifecycle source (`src/pcae/core/finalization_transaction.py` and every other production source file are unchanged by this phase); modify the CLTR shadow implementation (`src/pcae/cltr/*` is unchanged); implement atomic publication; implement migration evidence; implement cutover flags; cut over authority; demote legacy authority; retire legacy authority; modify notification; modify marker or receipt behavior; modify report or metadata generation; modify Architecture Status; add execution; add backend invocation; add shell mediation; or add Telegram inbound control. This phase's changes are documentation and contract/planning artifacts only: this document; `PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/DONE.md`; and governed task-contract lifecycle files.
