# Phase 135V — Stage 3 Authority-Cutover Readiness Architecture

Status: architecture / readiness analysis only. No implementation. No production change.

This document evaluates whether PCAE is architecturally ready to begin **designing and
contracting** Stage 3 authority cutover — the transition in which the Canonical Lifecycle
Transition Record (CLTR) would become production lifecycle authority in place of the legacy
lifecycle. It does not perform, activate, or implement any part of that transition.

Legacy lifecycle remains the sole production authority. CLTR remains derivative. Stage 2
rehearsal and rollback rehearsal remain non-authoritative. No Stage 3 code exists in this
repository as of this phase.

---

## 1. Readiness question

"Ready for Stage 3" is not one milestone. This document distinguishes five, in increasing
order of commitment:

| Milestone | Meaning | Evaluated by 135V? |
|---|---|---|
| Ready to design | Enough is known to start writing a Stage 3 contract | prerequisite to the below |
| **Ready to freeze a contract** | The design questions below can be answered precisely enough to freeze a binding, additive-only Stage 3 contract (a "135M for Stage 3"), the way 135B froze CLTR-001 and 135Q froze the Stage 2 rehearsal contract | **yes — this is what 135V evaluates** |
| Ready to implement | The frozen contract has itself been independently verified (a "135R for Stage 3") and a bounded implementation plan exists | not evaluated here |
| Ready to activate | An implemented, independently verified authority resolver exists, operator authorization is obtained, and a specific transition's evidence package passes the pre-cutover gate | not evaluated here |
| Ready to retire legacy authority | Stage 3 has been active in production for a sufficient soak/evidence period and a separate legacy-retirement decision is made | not evaluated here, out of scope by more than one phase |

**135V evaluates exactly one milestone: readiness to freeze the Stage 3 authority-cutover
contract.** It follows the same discipline Track 135 has used at every stage boundary — 135A
(architecture) preceded 135B (contract freeze) preceded 135C (contract verification) preceded
135D+ (formalization) before any implementation (135K) was attempted. Stage 3 must earn the
same sequence: 135V (this phase, architecture) → 135W (contract freeze) → 135X (contract
verification) → only then implementation phases.

This document's readiness verdict therefore answers: *can a Stage 3 contract be frozen next*,
not *can Stage 3 be implemented, activated, or completed*.

---

## 2. Current migration-stage model

Reconstructed from 135M (stage definitions), 135O/135P (Stage 1), 135Q–135U (Stage 2 and
rollback rehearsal), and verified against live CLI output (`pcae cltr migration status`,
`pcae cltr migration rehearsal status`, both confirming `production_authority: legacy`,
`authoritative: false`, `authority_cutover: false` in the current repository).

| Stage | Production authority | CLTR role | Legacy role | Pointer role | Evidence role | Allowed side effects | Forbidden side effects | Progression prerequisite | Rollback semantics | Recovery semantics |
|---|---|---|---|---|---|---|---|---|---|---|
| **Stage 0** — shadow observation (135K/135L) | Legacy | Passive observer; constructs one shadow record per finalized transition, strictly after legacy's own terminal effects | Sole authority, unaffected | None (no CLTR pointer exists) | Comparison sources mostly `unverifiable` (F-135L-2) | Write-once immutable shadow record under `.pcae/cltr-shadow/` | Any influence on legacy report/marker/receipt/notification | n/a (entry stage) | n/a — nothing to roll back | Re-run of shadow construction is itself idempotent per transition |
| **Stage 1** — dual derivation, legacy authority (135O/135P) | Legacy | Reads legacy's already-completed outputs; independently derives a comparable record from one shared input package; `ProductionAuthority` enum member is structurally always `LEGACY` | Sole authority | None (still no CLTR pointer) | `MigrationEvidenceRecord` per transition, epoch-scoped under `.pcae/cltr-migration/epochs/<epoch>/` | Comparison, mismatch classification, evidence persistence | Any write to legacy artifacts; any promotion/dispatch/marker/receipt call from CLTR-side code | `PCAE_CLTR_DUAL_DERIVATION_ENABLED=1` + valid `PCAE_CLTR_MIGRATION_STAGE`/`_EPOCH` (all default off in this repository) | n/a — evidence is append-only, nothing to revert | Crash mid-capture leaves an incomplete evidence record only; legacy is unaffected because Stage 1 code runs only after (or bracketing) legacy's own completed path |
| **Stage 2** — atomic publication rehearsal (135Q/135S/135T) | Legacy | Rehearses a full candidate-generation build + atomic pointer publication, in an isolated non-authoritative namespace (`.pcae/cltr-migration/epochs/<epoch>/rehearsals/<transition-id>/`) | Sole authority | `current-rehearsal` pointer — rehearsal-only, never read by production | Rehearsal generation + manifest + digest + evidence record | Candidate assembly, atomic pointer switch **within the rehearsal namespace only** | Any write outside the rehearsal namespace; any notification dispatch | Stage 1 evidence accumulation to a threshold (135M stage-transition matrix; no numeric threshold has been reached or is currently enforced — see §9) | n/a at this row — see next row | Crash matrix covers all pre/post-replace boundaries (135S/135T); recovery reads recorded evidence, never re-derives from narrative state |
| **Stage 2 rollback rehearsal** (135U) | Legacy | Reverses the rehearsal-only pointer to a prior verified rehearsal generation, using the same atomic-replace primitive as forward publication | Sole authority | Same `current-rehearsal` pointer, moved backward | `rollback_rehearsal` evidence record (135Q §36-shaped) | Pointer reversal within rehearsal namespace; invalidériz of progression eligibility for the rolled-back-from generation | Any production effect; rewriting or deleting any generation; cross-epoch rollback (not implemented — §10) | A prior verified rehearsal generation must exist | 11-step atomic sequence (§ below); idempotent; conflict-detecting; never mutates production | Full crash matrix (9 parametrized pre-replace boundaries + post-replace durability + recovery-on-replay), 43/43 + 26/26 tests |
| **Stage 3** — proposed authority cutover (this document) | **Proposed: CLTR** | Proposed: becomes the authoritative source for lifecycle truth at defined boundaries | Proposed: demoted to compatibility/derivative role (not yet retired — see §29) | Proposed: a production authority pointer, atomically switched exactly once per transition | Proposed: a certified cutover-evidence package binding migration epoch, authority epoch, and generation digest | Not yet defined in binding form — this document proposes but does not freeze | Everything Stage 0–2 rollback forbid, plus: no dual-authority steady state, no caller-specific authority resolution | Everything in the pre-cutover gate (§9) plus a frozen, independently verified Stage 3 contract | Proposed: bounded by irreversible-effect boundary (§20) | Proposed: recorded-state-only, never inferred (§19) |
| **Later stage** — legacy demotion and retirement (135H, §29) | CLTR (already cut over) | Sole authority | Progressively disabled: read-disabled → fallback-disabled → code-retired | CLTR pointer only | Retirement evidence | Removing legacy read paths, then legacy code | Reintroducing any legacy authority path | Sustained Stage 3 soak period + explicit retirement decision (out of scope for 135V) | n/a — legacy is not authoritative to roll back to | n/a |

Stage 3 cutover and legacy retirement are **not one event**. 135H already established this
(§29 reconstructs 135H's proposed 9-stage cutover strategy into 4 stages here); this document
does not collapse them, consistent with the phase's explicit instruction.

---

## 3. Current authority inventory

Independent enumeration of every artifact touching production lifecycle truth, classified
against the taxonomy 135A froze (immutable representation / deterministic derivative /
external projection / verification result — "no fifth category"), extended with the
operational/evidence/compatibility/historical labels this phase's brief requests.

| Artifact | Current classification | Source | Could it accidentally become a second authority? |
|---|---|---|---|
| Active task/lifecycle state (`tasks/active/*.md`) | Operational control | Task contracts | No — never read by finalization transaction as a truth source |
| Shared finalization transaction (`finalization_transaction.py`) | **Authoritative** (the legacy authority itself) | `run_finalization_transaction()` | n/a — this *is* the authority |
| Canonical phase report (`.pcae/phase-reports/latest.md`/`.json`) | Authority-bearing derivative (PFR-001-governed, but the file pair is non-atomically written — Gap B) | `phase_reports.py` | Yes, latently: two non-atomic files can transiently disagree; not a second *independent* authority, but a split-visibility hazard |
| Completion metadata (`.pcae/phase-completion-metadata.json`) | Authority-bearing derivative | `phase_reports.py` | No (single file, but has previously drifted — 135D.1 incident) |
| Architecture Status (generated section of `PROJECT_STATUS.md`) | Non-authoritative derivative (narrative-parsing, not CLTR-sourced) | `phase_reports.py` title-extraction | **Yes — this is the one confirmed live case.** 135C found a title cross-attribution bug that let Architecture Status assert an incorrect phase grouping. It is display-only today, but if any future code path read it as an authority signal, it would be a second authority. Must remain read-only/presentational through Stage 3. |
| Checkpoint (`.pcae/finalization-transactions/<phase_id>.json`) | Authority-bearing derivative / operational control (drives resume logic) | `finalization_transaction.py` | No, but Gap A (resume logic recognizes only `status=="completed"`) means the checkpoint's *state machine* is incomplete relative to CLTR-001's frozen 14-state model |
| Promoted generation (via `canonical_artifact_promotion.py`) | Authority-bearing derivative | `promote_artifact()` | No, but non-atomic writes (Gap B, 3 sites) create a transient-inconsistency window |
| Production "latest" pointer (`latest.md`/`latest.json`) | Authority-bearing derivative, **not** atomic | `canonical_artifact_promotion.py` | Same as above — Gap B |
| Notification intent/payload | External projection | `notifications.py` | No — one-way, PFN-001-bound |
| Notification marker (`.last-notified.json`) | Operational control (idempotency guard) | `notifications.py` | No |
| Finalization receipt (`.pcae/delivery-receipts/`) | Verification result / authority-bearing derivative | `notifications.py` | No |
| Git commit attribution | Verification result (three-outcome: verified/contaminated/unverifiable, CLTR-001 §10.4) | git history + `phase_reports.py` | No, but Gap C (fabricated-hash silent `continue`) means the *classification itself* can silently degrade rather than fail closed — a correctness gap, not an authority gap |
| Repository-transition representation | Verification result | repository-transition validator | No |
| CLTR shadow record | Non-authoritative derivative (Stage 0) | `src/pcae/cltr/` | No — structurally cannot influence legacy; `production_authority` field, where present, is always `legacy` |
| Stage 1 migration evidence | Non-authoritative derivative, evidence only | `src/pcae/cltr/migration/` | No — read-only relative to legacy, evidence-only, epoch-scoped |
| Stage 2 rehearsal generation | Non-authoritative derivative, evidence + rehearsal-pointer only | `src/pcae/cltr/migration/rehearsal/` | No — isolated namespace, never read by legacy or by any production entry point |
| Stage 2 rehearsal pointer (`current-rehearsal`) | Operational control (rehearsal-scoped only) | `pointer.py` | No — confined to rehearsal namespace |
| Rollback evidence (135U) | Evidence only | `rollback.py` | No |
| Recovery and reconciliation state (`pcae phase-report reconcile`) | Verification result | `phase_reports.py` | No — explicitly read-only, never mutates |

**Conclusion:** exactly one live confirmed authority-adjacent hazard exists today —
**Architecture Status's narrative-parsing derivation** (§17) — and one structural
inconsistency-window hazard — **non-atomic `latest.*` writes (Gap B)** — both inherited
unrepaired from Track 134 and re-confirmed live through 135U. Neither is a second *authority*
today because nothing currently reads either as a truth source for governance decisions; both
become materially more dangerous the moment any Stage 3 mechanism might read from them, which
is why §9's pre-cutover gate requires their resolution as a prerequisite, not merely a
recommendation.

---

## 4. Target Stage 3 authority model

**The exact authoritative object:** a single, immutable, **certified cutover-generation
record** — not the ordinary Stage 2 rehearsal generation, not a bare CLTR shadow record, not
a manifest alone. It is a **manifest-bound CLTR record** (the same `record.json` +
`manifest.json` pair already frozen by CLTR-SCHEMA-001, persisted under
`generations/<transition_id>/`), additionally carrying:

- a `cutover_certification` block (new, proposed for the Stage 3 contract, not frozen here) —
  binding migration epoch, source authority epoch, target authority epoch, and the pre-cutover
  gate's evidence digest;
- the existing `authority_role` and identity fields CLTR-SCHEMA-001 already defines.

This is deliberately **not** "CLTR becomes authoritative" as a vague claim. The authoritative
object is: *one specific, digest-identified generation, produced by the existing rehearsal
mechanism, additionally certified by a not-yet-frozen cutover-certification step, and bound to
exactly one production authority pointer.*

Answering the brief's required questions directly:

| Question | Answer |
|---|---|
| What exactly becomes authoritative? | One certified CLTR generation (`record.json`+`manifest.json`+`cutover_certification`), identified by `transition_id` and content digest |
| One CLTR record, one generation, a manifest-bound package, or another object? | A manifest-bound generation — record and manifest already travel together (CLTR-SCHEMA-001 persistence contract); the cutover proposal adds certification, not a new object kind |
| Which pointer identifies current authority? | A new **production authority pointer** (proposed name: `current-authoritative`, distinct from both legacy's `latest.*` and Stage 2's `current-rehearsal`) |
| What validates the pointer? | The same atomic-pointer-validation primitive Stage 2/rollback already use (`pointer.py`), extended to check `cutover_certification` presence and authority-epoch match — not a new mechanism |
| What validates the generation? | Existing manifest/digest verification (`digest.py`, `manifest.py`), plus a new certification-signature check (not yet designed) |
| Which artifacts are derived from the authoritative generation? | Report, metadata, Architecture Status, notification payload, marker, receipt — all proposed to become read-derivations of the pointed-to generation (§§16–18) |
| Which component controls production lifecycle success? | Proposed: a new **shared authority resolver** (§12), not the legacy transaction directly and not CLTR code directly — a resolver that both converge through |
| Which component controls promotion? | Proposed: promotion becomes "publish the authoritative pointer," using the same atomic-replace primitive already proven in Stage 2/rollback — no new promotion mechanism, a re-target of the existing one |
| Which component controls notification dispatch? | PFN-001's existing `certify_notification_transition()` remains the sole dispatcher; only its **input** changes (payload sourced from the authoritative generation instead of legacy's `PhaseReport` object) — §14 |
| Which component controls marker and receipt finalization? | Unchanged mechanism (`notifications.py`); only the identity/digest fields bound into the marker/receipt change to reference the authoritative generation — §15 |
| Which legacy outputs remain compatibility representations? | `latest.md`/`latest.json` legacy pair, legacy `PhaseReport` rendering, legacy Architecture Status title-parsing path — all become read-only compatibility adapters, not sources of truth |
| Which legacy components remain operational but non-authoritative? | Task/session state, checkpoint (as an operational resume aid only), legacy commit-attribution verification (folded into the certification input, not superseded) |
| Which legacy components must stop being consulted immediately? | None immediately at contract-freeze time (135V); at **activation** time (out of scope here) the four entry points must stop treating legacy's own in-process state as authoritative and instead consult the shared resolver |
| Which legacy components may remain as recovery fallbacks? | The legacy `latest.*` pair, retained read-only as a manual disaster-recovery reference until a separate retirement decision (§29) — never as an automatic fallback authority, which would recreate dual authority |

---

## 5. Authority-transition event

The conceptual authority-transition event, proposed for Stage 3 contract freeze:

| Field | Definition |
|---|---|
| Transition identity | The existing `transition_id` (design B, 135N/135O: UUID4, decoupled from `phase_id`, registry-keyed for replay stability) — reused, not replaced |
| Migration epoch | The existing `PCAE_CLTR_MIGRATION_EPOCH` concept (135M/135O) — a cutover event occurs within exactly one migration epoch |
| Source authority epoch | The legacy authority epoch active immediately before this transition (format: §7) |
| Target authority epoch | The CLTR authority epoch this transition would establish |
| Current authoritative generation before cutover | None (legacy has no CLTR-shaped generation; "authoritative" is presently a state, not an object) — this is itself notable: the *first* cutover transition has no CLTR predecessor generation, unlike every subsequent one |
| Proposed authoritative generation after cutover | The certified cutover-generation record (§4) |
| Prerequisite evidence | The full pre-cutover gate (§9) |
| Acceptance decision | Explicit human authorization (§25), not automatic |
| Publication boundary | The atomic switch of the new production authority pointer — proposed as the **single irreversible event** (§6, §19) |
| Verification boundary | Independent verification of the frozen Stage 3 contract (135X) plus, per-transition, verification that the specific candidate generation passes the pre-cutover gate — two different verification boundaries that must not be conflated |
| Irreversible effects | Pointer publication itself (local, cheaply reversible pre-external-effect); external notification dispatch (not locally reversible — §20) |
| Recovery state | Recorded, not inferred (§19) |
| Rollback or roll-forward policy | Proposed: rollback permitted only pre-external-effect; roll-forward (a new transition) required after (§20) |
| Cutover receipt/evidence | A new evidence kind, analogous to existing rollback evidence records, binding transition identity, source/target epoch, and outcome |
| Operator visibility | Surfaced via the existing `phase-report reconcile`-style read-only command, extended (not replaced) for cutover state |

**Mechanism selection.** The brief asks whether authority transfer should use one atomic local
pointer replacement, a two-pointer protocol, a manifest-bound epoch switch, a transaction
record plus pointer, or another mechanism.

135U already answered the *forward-publication* half of this question empirically: Stage
2/rollback both reuse **one atomic `os.replace`-based pointer-replacement primitive**
(`pointer.py`), and 135U's rollback reused it unmodified rather than inventing a new
primitive. The architectural conclusion for Stage 3 is:

**Proposed mechanism: a manifest-bound generation (already exists) plus a single atomic
pointer replacement (already exists as a primitive) plus a new certification record that must
exist and validate *before* the pointer replace is attempted.** This is not a new physical
mechanism — it is the existing Stage 2 mechanism, re-targeted at a new pointer name, gated by
a new pre-condition (certification) that Stage 2 does not require because Stage 2 is
non-authoritative.

This explicitly is **not** a two-pointer protocol (legacy and CLTR pointers "live" at once)
— that would be dual authority during the transition window, forbidden by §6. It is not a
bare transaction-record-plus-pointer either, because the transaction record (certification)
gates *whether* the pointer replace is attempted at all, rather than being a parallel source
of truth once the pointer has moved.

**Proof of single-resolution:** because the atomic pointer replace is a single filesystem
`os.replace` (already verified atomic under 135S/135T/135U's crash matrices — 9 parametrized
pre-replace boundaries, post-replace durability, and recovery-on-replay, all passing), at any
instant exactly one file exists at the pointer path, and it names exactly one generation.
There is no instant at which two pointers can be independently "current" for the same
transition, because there is only ever one pointer file for the production authority role.
The certification pre-condition does not introduce a second pointer — it is a gate evaluated
strictly before the swap, not a competing swap target.

---

## 6. Single-authority invariant

**Frozen invariant (proposed, for Stage 3 contract freeze, not yet binding until 135W):**

> At every externally visible production lifecycle boundary, exactly one authority epoch and
> exactly one authoritative generation may control lifecycle truth.

Evaluation model:

- **Evaluated at:** each of the four entry points, at the moment they resolve "what is
  currently true about this transition" — this is the proposed shared-authority-resolver call
  (§12), not an ad hoc read of either legacy or CLTR state.
- **Externally visible** means: anything a human operator, a notification recipient, a
  downstream CI job, or a future repository-intelligence query could observe — reports,
  notifications, markers, receipts, Architecture Status, and the CLI's own read commands. It
  explicitly excludes purely internal in-process variables that never escape a single
  function call.
- **Authoritative** means: the fact is treated as ground truth for a governance decision
  (task transition, gate pass/fail, notification content) — not merely "recorded somewhere."
- **Transient internal preparation state is allowed** — candidate assembly, certification
  computation, and pre-publish verification may exist in-process or in the non-authoritative
  rehearsal/evidence namespaces without violating the invariant, exactly as Stage 2 rehearsal
  already does not violate it today (rehearsal generations are not "authoritative," they are
  candidates).
- **Crash before publication:** authority remains with the pre-existing authoritative
  generation (legacy, pre-cutover; the prior CLTR generation, post-cutover). No externally
  visible boundary can have observed the candidate as authoritative, because the pointer never
  moved.
- **Crash after publication:** authority is the newly published generation. Recovery must read
  the pointer, not re-derive from narrative or in-process state (§19).
- **Uncertainty representation:** reuse the existing `promotion_outcome_unconfirmed` /
  `delivery_recorded_bookkeeping_incomplete` pattern from `ReconciliationOutcome` (135H.2,
  carried into CLTR-SCHEMA-001's 5-value enum) — uncertainty is itself a recorded, named state,
  never silently resolved to either "old" or "new" authority.
- **Recovery must not consult both authority systems as parallel sources.** Recovery consults
  the pointer (single source), and if the pointer is ambiguous or missing, recovery returns an
  explicit uncertain/conflict state (`rollback_conflict`, `not_delivered`, `conflict` — reusing
  135U's and CLTR-SCHEMA-001's existing enums) rather than falling back to "check legacy, then
  check CLTR, prefer legacy." **"Legacy preferred if both exist" is explicitly rejected as a
  permanent model** — it is dual authority with a fixed tiebreaker, which is still dual
  authority. It may be used, at most, as a **one-time, human-reviewed, evidence-logged
  disambiguation** during a genuine crash-recovery incident, never as routine steady-state
  logic.

---

## 7. Authority epochs

Reconstructed from 135M's authority-epoch definition and 135O's implementation
(`legacy|dual_derivation_legacy_authority|epoch-1|CLTR-SCHEMA-001|1.0.1`):

| Element | Current (Stage 1/2) | Proposed for Stage 3 |
|---|---|---|
| Legacy authority epoch format | Implicit — "legacy" is the only value `ProductionAuthority` can take; no separate versioned epoch string exists for legacy itself today | Should remain implicit/constant for legacy (`legacy` is a fixed value, not a rotating epoch — legacy does not "version" its own authority) |
| CLTR authority epoch format | `"legacy|" + migration_stage + "|" + migration_epoch + "|" + schema_id + "|" + schema_version` — a **string concatenation**, currently checked with a **substring test** that F-135U-2 found bypassable (`"legacy" in authority_epoch.lower()`) and tightened to an exact-prefix check within 135U itself | Insufficient for Stage 3. A production authority pointer that could ever say "authoritative" must not rely on string-prefix parsing for something this safety-critical. §7.1 below. |
| Migration-epoch relationship | Migration epoch is a sub-field of the authority-epoch string, scoping evidence to `.pcae/cltr-migration/epochs/<epoch>/` | Should persist as a structured field distinct from authority epoch, not concatenated, once a typed model exists |
| Epoch transition rules | None formally frozen — Stage 1/2 evidence is simply never cross-epoch-aggregated (135M) | Stage 3 needs an explicit rule: a cutover transition's target epoch must be new relative to the source; no cutover may target an epoch already superseded |
| Epoch immutability | Epoch strings are not mutated once evidence is recorded; a new epoch means new evidence directories | Carry forward unchanged |
| Epoch compatibility | `compatibility_id=pcae.cltr.v1` (CLTR-SCHEMA-001) is the actual compatibility axis today, orthogonal to authority epoch | Must be explicitly related to authority epoch in the Stage 3 contract — a schema-compatible-but-different-authority-epoch generation must be classified, not silently accepted |
| Epoch binding in reports/evidence | Present today in migration evidence and rehearsal records | Must extend into the report/metadata/marker/receipt derivations proposed in §§14–17 |
| Authority-epoch verification | Currently: string prefix/substring match (post-F-135U-2, exact prefix) | Insufficient alone for production authority-changing decisions — needs the typed check below |
| Stale-epoch rejection | Exists structurally (evidence is epoch-scoped, so stale epochs simply don't aggregate) but is not an explicit *rejection* rule with a named error state | Stage 3 needs an explicit `stale_authority_epoch` rejection outcome, analogous to `rollback_rejected` |
| Future schema-version relationship | `compatibility_id` unchanged across MINOR/PATCH bumps (135I); unknown MAJOR fails closed | Carry forward unchanged — this is already sufficiently rigorous |
| Historical record interpretation | Historical generations remain readable under their own recorded epoch; nothing rewrites history | Carry forward unchanged; explicitly required by CLTR-001's immutable-history invariant |

### 7.1 Typed model resolution

The brief asks whether the current string-prefix check is sufficient only for Stage 2, or
must be replaced by a typed production authority model before Stage 3.

**Resolution: the current string-prefix/exact-prefix check is sufficient only for Stage 2
rehearsal (non-authoritative) and must be replaced by a typed model before Stage 3 contract
freeze can be considered complete for implementation** — but this document does **not**
implement that typed model (the brief forbids it). It is recorded as a **prerequisite for the
Stage 3 contract (135W), not a prerequisite for this readiness architecture (135V) itself**,
because 135V's job is to identify the requirement, not satisfy it. See §9's pre-cutover gate
and §26's readiness package for where this requirement is tracked forward. The reasoning:
F-135U-2 already proved string-based authority-epoch checks are bypassable in a
*non-authoritative* rehearsal context; the same class of defect against a *production*
authority pointer would be a Blocking safety defect, not a Non-Blocking one (§27's finding
classification below reflects this).

---

## 8. Cutover candidate and authoritative generation

Distinguishing six states, per the brief's requirement that a Stage 2 rehearsal generation
must not become authoritative merely by a pointer change:

1. **Rehearsal candidate** — an in-progress Stage 2 assembly, not yet published to even the
   rehearsal pointer. Fully reversible, no evidence yet durable beyond intermediate writes.
2. **Verified rehearsal generation** — published to `current-rehearsal` (or a prior such
   generation), passed Stage 2's own independent verification (135T's tests) at build time.
   Still non-authoritative by construction (`production_authority: legacy` always).
3. **Cutover candidate** — a rehearsal generation *nominated* for cutover consideration.
   Proposed as a new, distinct status: nomination does not mutate the rehearsal generation; it
   is a reference plus a request to begin certification.
4. **Certified cutover generation** — a cutover candidate that has passed the full pre-cutover
   gate (§9) and received the new `cutover_certification` block (§4). This is the *only* state
   allowed to be the target of a production authority pointer switch.
5. **Authoritative production generation** — a certified cutover generation whose target has
   actually been published via the atomic pointer switch. Exactly one may exist per authority
   epoch at any instant (§6).
6. **Historical generation** — any prior authoritative generation, superseded by a later one;
   retained immutably, never deleted, consistent with CLTR-001's immutable-history invariant.
7. **Quarantined generation** — any generation (rehearsal, candidate, or would-be-authoritative)
   that failed a validation, digest, or containment check; reused unchanged from the existing
   `QUARANTINED` overlay flag (CLTR-001 §7, 135A's 14-state model).

**Required additional certification, precisely:** a rehearsal generation becomes a cutover
candidate only by explicit nomination (an operator or governed-command action, not automatic);
it becomes a certified cutover generation only after the full pre-cutover gate (§9) evaluates
to pass with zero unresolved Blocking findings and explicit human authorization (§25) is
attached; it becomes authoritative only via the single atomic pointer switch (§5), which must
refuse to execute against anything other than a certified cutover generation. A bare pointer
change against an uncertified generation is explicitly forbidden and must fail closed —
mirroring how `pointer.py`'s existing `validate_generation_target` already refuses to publish
against a quarantined or malformed target.

---

## 9. Pre-cutover gate

The complete Stage 3 pre-cutover gate, aggregating evidence requirements named throughout the
brief. Each row states the evidence source and current status.

| Requirement | Evidence source | Current status |
|---|---|---|
| Valid Stage 1 derivation | `src/pcae/cltr/migration/` coordinator output | Implemented (135O), verified (135P); **not currently exercised in this repository** (feature flags default off — confirmed via `pcae cltr migration status`: `dual_derivation_enabled: false`) |
| Valid Stage 1 migration evidence | `MigrationEvidenceRecord` | Mechanism exists; no live evidence corpus accumulated yet |
| Complete Stage 2 forward rehearsal | `src/pcae/cltr/migration/rehearsal/coordinator.py` | Implemented (135S), verified (135T); **not currently exercised** (`atomic_rehearsal_enabled: false`, confirmed via `pcae cltr migration rehearsal status`) |
| Independent Stage 2 verification | 135T | Complete for the mechanism; per-transition evidence not yet accumulated |
| Successful rollback rehearsal | `rollback.py` | Implemented and verified (135U), 43/43 + 26/26 tests |
| Rollback independent verification | 135U | Complete |
| Exact candidate inventory | 135Q's 23-item inventory, 10 file-backed + manifest-bound implemented (135S) | Complete per Stage 2 scope; items 11–14 folded/deferred (disclosed) |
| Deterministic identity | `transition_identity.py` (design B) | Implemented, verified (135P) |
| Manifest and digest verification | `manifest.py`, `digest.py` | Implemented, verified |
| Production-output equivalence | Adapter comparison (`adapters.py`, `comparison.py`) | **Gap: adapters are not wired at the real production call site (F-135L-2, carried through 135M–135P unrepaired).** Real invocations resolve most comparisons as `unverifiable`. This is a genuine blocking gap for *evidence accumulation toward cutover*, though not for the *contract-freeze* milestone itself. |
| All-four-entry-point coverage | 135P's end-to-end test | Complete — all four real entry points exercised through the real transaction boundary |
| Ordinary-path coverage | 135S/135T/135U test suites | Complete |
| Recovery-path coverage | Crash matrices (135S/135T/135U) | Complete for Stage 2/rollback; not yet defined for Stage 3 cutover itself (§19 proposes the model, does not implement it) |
| 135H.1 escape resistance | 135Q §-cited proof; 135S/135T tests | Complete for Stage 2 |
| Pointer containment | `persistence.py` path-containment checks | Implemented, tested (containment/symlink test classes, 135U) |
| Immutable persistence | Generation directories, write-once | Implemented |
| Split-brain prevention | 135Q §38 (9 structural checks) | Implemented for the rehearsal namespace; **not yet defined for a production authority pointer** (§21 proposes, does not implement) |
| Notification isolation during rehearsal | Structural — rehearsal code never calls `notifications.py` | Confirmed by code map; enforced only by omission, not by an explicit guard — worth hardening before Stage 3 implementation |
| Marker/receipt isolation during rehearsal | Same as above | Same as above |
| No unresolved Blocking findings | Phase reports 135A–135U | **Zero open Blocking findings as of 135U** — every Blocking finding found (F-135N-1, the 135J §21.4 gap, F-135T-1, F-135T-2) was repaired within its own governed phase before that phase's completion |
| Explicit operator authorization | Not yet designed | **Missing — required before contract freeze can be considered complete for implementation purposes; see §25** |
| Supported schema/version | CLTR-SCHEMA-001 v1.0.1 | Current; §23 evaluates sufficiency |
| Matching migration epoch | `PCAE_CLTR_MIGRATION_EPOCH` | Mechanism exists |
| Valid source authority epoch | Authority-epoch string, exact-prefix-checked (post F-135U-2) | Sufficient for Stage 2; **insufficient for Stage 3 per §7.1** |
| Valid target authority epoch | Not yet defined — no CLTR authority epoch has ever been "target" of anything, because `ProductionAuthority` never resolves to CLTR | **Does not exist yet — a Stage 3 contract must define it** |
| Complete rollback or roll-forward plan | 135U implemented Stage 2 rollback; production-authority rollback is a **different** thing (§20) and does not yet have a plan beyond this document's proposal | Proposed here, not frozen |
| Production recovery readiness | §19 proposes a model | Not implemented |

**Non-Blocking-vs-Blocking-at-the-authority-boundary disposition:** every currently-open
Non-Blocking finding across 135L–135U (adapter-wiring gap, `NON_AUTHORITY_DISCLOSURE`
duplication, recovery-classification imprecision for 2 of 4 entry points, final-revision
grace-period bound, actor/session provenance absence, branch-reachability/rewritten-history
algorithm not yet specified, commit-ownership blocking-vs-warning policy) **remains
Non-Blocking for contract freeze** (135W) because none of them currently causes an incorrect
authority decision — none of them is consulted by anything authoritative today. Each becomes
**Blocking at the authority-activation boundary** (not at contract-freeze) because once a
production authority pointer exists, the same gaps would then sit directly in the trust path.
This distinction — Blocking-for-freeze vs. Blocking-for-implementation vs.
Blocking-for-activation — is formalized in §27.

---

## 10. Disposition of 135U limitations

| Limitation | Disposition | Reasoning |
|---|---|---|
| **Rollback to no current rehearsal** (no pointer state) | **Mandatory before Stage 3 implementation; permanently forbidden as a *production* authority state.** For the rehearsal namespace, "no rehearsal" is a legitimate initial/never-started state (nothing is authoritative regardless). For a *production* authority pointer, "no pointer" must never be reachable once cutover has occurred — a production system with zero authoritative generations is a worse failure mode than dual authority, because no externally visible boundary could resolve any truth at all. Contract-freeze-blocking: **no** (it's a design question the contract can answer). Implementation-blocking: **yes** — the Stage 3 implementation must define what "current authoritative generation" defaults to before the first cutover (answer: legacy, by convention, until cutover succeeds — i.e., "no CLTR pointer yet" is not the same as "no authority"; legacy authority is the implicit default absent a published CLTR pointer). |
| **Cross-epoch rollback reconciliation** | **Permanently forbidden — rollback stays within an authority epoch; cross-epoch movement is roll-forward (a new transition), never rollback.** This confirms the brief's suggested "likely safer rule" as the final architecture, derived from: (a) 135M's own definition of migration epoch as a boundary evidence is never silently combined across; (b) the authority-epoch string already encodes migration epoch as a sub-component, so a "rollback" that crossed epochs would implicitly also be changing the authority-epoch identity, which is exactly the kind of event the transition/certification model (§5) — not the rollback model — is designed to gate. Contract-freeze-blocking: no (this document resolves it). Implementation-blocking: no (135U's existing rollback mechanism already refuses cross-epoch targets implicitly, since epochs are separate directory trees). |
| **Concurrent rollback-versus-forward race** | **Pre-implementation prerequisite for Stage 3 (not merely "hardening").** 135U's own position — "resolved identically to how ordinary forward publication resolves it" (both target the same pointer file via atomic `os.replace`, whichever wins is recorded, both remain auditable) — is **sufficient for Stage 2/rollback because neither outcome is authoritative**; whichever of the two rehearsal writes wins, production truth is unaffected. **This reasoning does not transfer to Stage 3.** Once the pointer is a production authority pointer, "whichever wins is recorded" is not an acceptable resolution for a cutover-vs-rollback race, because the losing writer's caller may have already begun an irreversible external effect (notification) based on a stale assumption about which generation is current. Stage 3 therefore needs genuine compare-and-swap semantics bound to an *expected current generation digest*, not merely last-write-wins (§11 architects this; does not implement it). Contract-freeze-blocking: no (this document identifies the required model). Implementation-blocking: yes. |
| **Separate roll-forward command** | **Not required for Stage 3 contract freeze or implementation; all forward movement remains a new governed transition, per 135Q §37's "preference, not command" framing, confirmed and carried forward unchanged.** A dedicated roll-forward command would be a convenience, not a correctness requirement — "roll forward" is representable as an ordinary new authority-transition event (§5) targeting a newer certified generation. Introducing a separate command class would multiply the number of code paths that must independently prove single-authority resolution (§6), which the architecture actively wants to minimize. Disposition: **deferred, post-cutover hardening at most, not a prerequisite of any kind.** |

Summary table (as required by the brief):

| Limitation | Current support | Authority relevance | Risk | Required behavior | Required phase | Blocking for freeze? | Blocking for implementation? | Blocking for activation? | Final disposition |
|---|---|---|---|---|---|---|---|---|---|
| Rollback to no rehearsal | Not implemented (rehearsal-scope only) | High (would be, for production) | Medium | Legacy-default-authority convention; no production "null authority" state | 135W (contract) / 135Y (implementation) | No | Yes | Yes | Contract must define the default; implementation must enforce it |
| Cross-epoch rollback | Not implemented | High | Medium | Forbidden; cross-epoch = new transition | 135W | No | No (already structurally true) | No | Permanently forbidden, confirmed |
| Concurrent rollback-vs-forward race | Last-write-wins only (sufficient for non-authoritative Stage 2) | **Critical for production** | High | Compare-and-swap on expected generation digest | 135W (contract) / dedicated hardening phase before 135Y | No | **Yes** | Yes | Prerequisite implementation phase required before Stage 3 implementation proper |
| Separate roll-forward command | Not implemented; "preference" only (135Q §37) | Low | Low | None — ordinary transition suffices | n/a | No | No | No | Deferred indefinitely; not required |

---

## 11. Concurrency architecture

Stage 2 proved sequential atomic pointer replacement (single-writer, tested via crash
injection, not via concurrent-writer injection — 135R explicitly named this as F-135R-4, the
seed finding this document must resolve at the architecture level). Stage 3 must define
concurrent-actor behavior explicitly, because production entry points (four of them, all
converging on `run_finalization_transaction`) can genuinely race in ways the rehearsal
namespace's test suite never had to model (only one CI process rehearses at a time today).

| Scenario | Proposed serialization boundary | Proposed behavior |
|---|---|---|
| Two cutover attempts | Compare-and-swap on expected current generation digest, evaluated inside the atomic pointer-replace step | Second writer's expected-digest check fails after the first writer wins; second writer receives a `stale_writer_rejected`-class outcome (new, analogous to existing `rollback_conflict`), must re-read current state and retry explicitly — never silently overwrites |
| Cutover versus rollback | Same compare-and-swap primitive, same pointer | Whichever operation's expected-digest check succeeds first wins; the other fails closed with an explicit conflict outcome, not a silent last-write-wins |
| Cutover versus ordinary legacy finalization | These do not share a pointer today (legacy uses `latest.*`, proposed Stage 3 uses a new `current-authoritative` pointer) — **no race exists structurally**, provided the two pointers are never merged. This is itself an architectural reason to keep them as genuinely separate files rather than unifying prematurely. | No serialization needed if pointers stay separate; if a future phase unifies them, this row must be re-architected |
| Cutover versus recovery | Recovery reads, never writes the pointer, except to record its own evidence | No race — recovery is read-only with respect to the authority pointer itself |
| Cutover versus reconciliation | Same — `phase-report reconcile`-style commands are read-only by contract (already true today, confirmed via live `pcae phase-report reconcile --phase-id 135U` returning `Mutation: none`) | No race |
| Rollback versus forward rehearsal (Stage 2, pre-cutover) | Already resolved identically for non-authoritative purposes (135U); **remains acceptable at Stage 2 because neither result is authoritative** | Unchanged for Stage 2; Stage 3's stricter model (compare-and-swap) applies only once a pointer is a production authority pointer |
| Two finalization entry points racing | Existing legacy behavior — outside this document's scope to re-architect, but Stage 3's shared authority resolver (§12) must not introduce a *new* race beyond what legacy already handles | Shared resolver must be safe to call concurrently from any of the four entry points; read-mostly, so this is lower risk than the write-side races above |
| Stale process replay | Reuse 135U's idempotency/replay-detection pattern (`rollback_idempotent_replay`) | A replayed cutover request with a matching prior outcome returns the recorded outcome, never re-executes |
| Process restart after publication | Recovery reads the pointer and recorded evidence; never re-attempts the atomic swap | Consistent with §6/§19 |
| Operator retry | Must be idempotent against the same transition identity, per existing `transition_id` replay-stability design (135N design B) | Reuses existing mechanism, no new design needed |

**Serialization boundary, precisely:** the single atomic pointer-replace call, extended with a
compare-and-swap precondition (`expected_current_generation_digest`, `expected_authority_epoch`)
evaluated as part of the same atomic operation — not as a separate check-then-act pair, which
would reintroduce the race. This is the one specific extension Stage 2's existing primitive
needs before it is safe to reuse for a production authority pointer; **135U's mechanism is
necessary but not sufficient for Stage 3, and this is the precise, narrow gap between them.**

**Process-local locking is explicitly rejected as the sole production guarantee** — the
brief's caveat is correct: this repository's production surface is a set of independently
invoked CLI processes (four entry points, potentially from different shells, machines, or CI
runners), not a single long-lived server process, so any lock that lives only in one process's
memory cannot serialize a genuinely concurrent second process. The filesystem-atomic
compare-and-swap (an `os.replace`-based check against the pointer's recorded expected digest,
verified post-replace by readback — the same pattern 135U's step 11 already uses for its own
readback/re-verify) is the correct production guarantee, because it is enforced by the
filesystem itself, not by in-process state.

---

## 12. All-four-entry-point cutover model

The four current production entry points, identified from source (`finalization_transaction.py`
call sites, confirmed by 135O/135P's own end-to-end test which exercises all four):

1. `run_phase_complete` (`src/pcae/commands/phase.py`) — `entry_point="phase_complete"`
2. `run_task_finish` (`src/pcae/commands/task.py`) — `entry_point="task_finish"`
3. `run_phase_report_create` (`src/pcae/commands/phase_reports.py`) — `entry_point="phase_report_create"`
4. `run_notify_send_report` (`src/pcae/commands/notifications.py`) — `entry_point="notify_send_report"`

All four already funnel through one shared function, `run_finalization_transaction(entry_point=...)`
— this convergence point is itself the reason Stage 1/Stage 2/rollback integration was possible
with "two new call sites, entry-point-agnostic" (135O) rather than four separate integrations.

**Proposed Stage 3 model:** introduce one **shared production authority resolver** — a single
function, called from inside `run_finalization_transaction` exactly once per transition
(mirroring how Stage 1's coordinator and Stage 0's shadow observer are each called from exactly
one place today), that:

- resolves "what generation is currently authoritative" by reading the production authority
  pointer (§4) if Stage 3 is active for this authority epoch, else defaulting to legacy
  (§10's disposition of the "no pointer" case);
- is the **only** function in the codebase permitted to answer that question authoritatively;
- is called identically regardless of which of the four entry points invoked the transaction —
  no entry-point-specific authority logic, exactly as Stage 1/Stage 2 integration already
  avoided per-entry-point branching;
- on the recovery path, is called with the same read-only semantics as the ordinary path — no
  entry point may fall back to inferring authority from its own local state (this closes off
  the "narrative identity" failure mode explicitly named in the brief — Architecture Status's
  title-parsing derivation, §17, is the cautionary precedent for why this must be forbidden).

This satisfies every constraint the brief lists: all four resolve identically (single shared
function); no caller bypasses the authoritative generation (the resolver is the only path to
it); no entry point independently constructs lifecycle truth (construction happens once,
inside the resolver, from the pointer); no recovery path falls back to narrative identity (the
resolver's recovery behavior is identical to its ordinary behavior — pointer-read-based, per
§19); no caller preserves hidden legacy authority (once Stage 3 is active for an epoch, the
resolver — not any entry point — decides whether legacy or CLTR governs that epoch); no entry
point dispatches from a different authority source (dispatch, §14, consumes the resolver's
output, not its own copy of legacy or CLTR state).

---

## 13. Production finalization transaction changes

Mapping `finalization_transaction.py`'s current shape (1136 lines; shared input assembly →
checkpoint/resume check → legacy sequential path → `promote_and_dispatch()` → receipt modeling
→ `_observe_shadow_cltr()` → Stage 1 pre-transaction/completion capture) against proposed
Stage 3 insertion points:

| Current step | Proposed Stage 3 change |
|---|---|
| Shared input finalization | Unchanged — already the "one shared input" 135M/135O require |
| CLTR certification | New: the certification step (§4, §8) would be invoked here, but **only for transitions already nominated as cutover candidates** — ordinary transitions are unaffected |
| Complete artifact generation | Unchanged for legacy; CLTR-side generation already exists (Stage 1/2 code) |
| Manifest verification | Unchanged — reuse existing `manifest.py`/`digest.py` |
| **Authoritative publication** | New insertion point, proposed to occur **after all local artifacts (report, metadata) are internally verified but before external notification dispatch** — see boundary analysis below |
| Report visibility | Proposed to become a read of the authoritative generation once Stage 3 is active for the relevant epoch (§16) |
| Checkpoint persistence | Unchanged mechanism; proposed to additionally record the resolved authority epoch (closes part of Gap A's state-machine incompleteness, since CLTR-001's 14-state model already accounts for this and legacy's checkpoint currently doesn't) |
| Promotion | Reinterpreted as "publish the authority pointer" for Stage-3-active epochs; unchanged for legacy epochs |
| Notification intent | Proposed input change only (§14) |
| External dispatch | Unchanged mechanism (PFN-001), changed input source |
| Marker | Proposed field-binding change only (§15) |
| Receipt | Proposed field-binding change only (§15) |
| Terminal reconciliation | Unchanged mechanism (`phase-report reconcile`), extended to also report authority-epoch/generation identity |

**Publication boundary decision:** the brief asks whether authority publication should occur
(a) before all irreversible effects, (b) after all local artifacts verify but before external
delivery, or (c) at another boundary.

**Proposed: (b) — after all local artifacts verify but before external delivery.** Reasoning:
publishing the authority pointer is itself a *local*, filesystem-atomic, and (pre-external-
effect) reversible operation — consistent with 135H's rollback-boundary definition ("reversible
until a CLTR-authoritative transition performs its first irreversible publication/dispatch
event"). If publication happened *before* local artifacts verify (option a, taken literally as
"before everything"), a verification failure after publication would leave a published-but-
unverified authoritative generation, violating the sole-authority invariant's intent that
"authoritative" implies "trustworthy." If publication happened *after* external delivery, the
notification would need to reference a not-yet-authoritative generation, which contradicts
§14's requirement that CLTR authority controls notification intent. Boundary (b) is the only
option under which "authoritative" and "verified" are guaranteed to coincide at the moment
anything externally visible occurs.

**PFN-001 and PFR-001 are preserved unchanged** — this document proposes no change to either
contract's binding text; only the *input source* feeding the existing mechanisms changes,
exactly as the brief requires.

---

## 14. Notification authority migration

| Question | Answer |
|---|---|
| Does CLTR authority control notification intent? | Proposed: yes, for Stage-3-active epochs — the resolver (§12) determines *that* a notification is due; PFN-001's existing dispatch mechanism remains the *how* |
| Which artifact supplies the payload? | Proposed: the authoritative generation's derived report projection (§16), not legacy's in-memory `PhaseReport` object directly |
| Which digest binds the payload? | The authoritative generation's manifest digest (already exists, CLTR-SCHEMA-001) |
| When does dispatch become authorized? | After the publication boundary (§13(b)) — i.e., only once the generation is already authoritative, never before |
| How is exactly-once preserved? | Unchanged mechanism: `certify_notification_transition()` + `.last-notified.json` marker (PFN-001) — this document proposes no change to the exactly-once mechanism itself, only to what data it dispatches |
| How is uncertain delivery represented? | Unchanged: existing ATTEMPTED/SENT/SKIPPED_WITH_REASON/FAILED_WITH_REASON outcomes (PFN-001) |
| How does recovery avoid duplicate delivery? | Unchanged marker-based idempotency; recovery re-checks the marker before any redispatch, exactly as today |
| How are old legacy markers treated? | As historical/compatibility records — never re-interpreted as authorizing a new dispatch |
| Does legacy notification code remain a delivery adapter only? | Yes — proposed: `notifications.py`'s dispatch mechanism is unchanged and continues to serve both legacy-authority and CLTR-authority transitions identically; it becomes payload-source-agnostic rather than being replaced |

**No implementation proposed here.** PFN-001 remains binding and unmodified.

---

## 15. Marker and receipt authority migration

| Artifact | Target authority | Derived from authoritative generation? | May remain operational state? | Authority-epoch/digest binding | Old-artifact interpretability | Duplicate/conflict rejection | Relation to authority publication |
|---|---|---|---|---|---|---|---|
| Notification marker | Operational control (unchanged role) | No — it's an idempotency guard, not a truth source | Yes | Proposed: bind `transition_id` + generation digest, not just `phase_id` | Legacy markers remain readable as historical evidence | Existing marker-presence check, unchanged | Must reference a generation that is already authoritative (post-publication) |
| Completion marker | Same as above | No | Yes | Same | Same | Same | Same |
| Finalization receipt | Verification result (unchanged role) | Partially — receipt content should reflect the authoritative generation's identity | Could remain compatibility-adjacent operational state | Proposed: bind authority epoch + generation digest as new optional fields | Legacy receipts remain valid historical evidence under their own recorded (implicit legacy) epoch | Existing finalization logic, unchanged | Receipt finalization occurs after publication, consistent with §13(b) |
| Promotion receipt | Same as receipt, if distinct | Same | Same | Same | Same | Same | Same |
| Recovery evidence | Evidence only | N/A — evidence describes, doesn't authorize | Yes, inherently | Should record both source and target authority epoch for any recovery event spanning a cutover | Historical | N/A | Read-only by construction (§6) |

**No receipt may independently establish lifecycle truth** — every field added above is
additive/descriptive (binding identity for traceability), never a field whose presence alone
would let a receipt substitute for the authority pointer as a truth source. This mirrors
CLTR-001's own forbidden-pattern list (§4's 9 named forbidden competing-authority patterns,
which already explicitly forbid "receipt presence" as an authority signal).

---

## 16. Report and metadata migration

- **Generation-to-report derivation:** proposed — the canonical phase report becomes rendered
  from the authoritative generation's certified content, for Stage-3-active epochs. For
  legacy-authority epochs (i.e., every transition until cutover actually occurs), report
  rendering is unchanged.
- **Generation-to-metadata derivation:** same pattern — `phase-completion-metadata.json`
  becomes a rendering of the authoritative generation's identity/status fields.
- **Atomic visibility:** the report/metadata pair must become visible together, exactly as
  135A's atomic-visibility contract already requires in the abstract (§13 of CLTR-001) — this
  is also the natural fix for Gap B (non-atomic `latest.*` writes), though Gap B's repair is a
  legacy-production fix independent of Stage 3 and could, in principle, be done earlier (it is
  not part of this document's scope to schedule that repair, only to note that Stage 3's own
  atomic-generation mechanism, reused from Stage 2, does not have Gap B's defect, so *new*
  CLTR-derived reports would not inherit it).
- **Identity/digest binding:** report and metadata both carry `transition_id` and generation
  digest, exactly as CLTR-SCHEMA-001 already specifies for its 15 representation kinds.
- **Schema/version handling:** unchanged — CLTR-SCHEMA-001's existing MAJOR/MINOR/PATCH rules.
- **Compatibility fields:** legacy report/metadata fields remain present and populated for any
  epoch not yet cut over; once cut over, they become compatibility-rendering outputs of the
  same authoritative data, not independently computed.
- **Latest-file semantics:** proposed — the legacy `latest.*` pair becomes a compatibility
  projection of whatever the resolver (§12) currently reports as authoritative, still written
  through the existing (currently non-atomic, Gap B) mechanism unless/until that mechanism is
  separately repaired. This document does not require Gap B's repair as a prerequisite for
  contract freeze, but flags it as a "should-fix-before-implementation" item given that Stage 3
  increases how much weight rests on `latest.*` remaining trustworthy for operators and any
  compatibility tooling.
- **Historical report preservation:** unchanged — immutable, per generation.
- **Recovery behavior:** report/metadata recovery reads the resolver's output, never infers
  from git history or narrative parsing (this is the direct architectural rejection of the
  Architecture-Status failure mode, §17).
- **Legacy report generation code remains an adapter:** yes, proposed — `phase_reports.py`'s
  existing rendering logic is retargeted to consume either legacy or CLTR-sourced data through
  one interface, rather than being replaced by new code.

PFR-001 remains unchanged unless a future explicit contract phase changes it, consistent with
the brief's requirement.

---

## 17. Architecture Status migration

Architecture Status is the one artifact this document must treat with particular care, because
135C already found it degrading silently once (the title cross-attribution defect) — it is
the empirical proof that a narrative-parsing derivative can drift from truth without anyone
choosing that outcome.

**Proposed Stage 3 requirements, restated as prohibitions:**

- Architecture Status **must not** infer phase/state from titles or narrative text once a
  CLTR-sourced derivation is available for a given epoch — it must read the authoritative
  generation's structured identity fields instead.
- It **must not** independently determine phase identity — identity comes from the resolver
  (§12)/authoritative generation, never from re-parsing PROJECT_STATUS.md's own prose.
- It **must not** become a fallback authority under any circumstance, including recovery —
  this is the single most direct application of the brief's "no narrative identity" rule.
- It **must not** read mutable post-certification state that isn't bound to the generation —
  chapter groupings, phase counts, and similar presentational content may still be computed
  from the sequence of generations, but never from anything that could disagree with the
  generation's own recorded content.
- **Chapter grouping and presentation are addressed separately from lifecycle identity** — the
  brief is correct to require this distinction: how phases are grouped into human-readable
  chapters/sections is a presentation concern (may legitimately use titles, series groupings,
  etc.), whereas *which phase is which* and *what its status is* must come from structured
  identity, never from presentation-layer parsing. 135C's bug was exactly a presentation-layer
  mechanism (title-extraction regex) being trusted for an identity-adjacent purpose
  (attributing a phase-count grouping); the fix implied here is architectural separation of
  those two concerns, not merely a regex fix.

No implementation is proposed in this phase; this section defines the requirement so 135W can
freeze it as a binding constraint.

---

## 18. Checkpoint and promotion migration

| Artifact | Proposed future authority relationship |
|---|---|
| Pre-adapter checkpoints | Remain operational/resume-aid state; proposed to additionally record resolved authority epoch (closes part of Gap A) |
| Promotion checkpoints | Same |
| Current-generation pointer (legacy `latest.*`) | Compatibility output once Stage 3 is active for an epoch; authoritative only for legacy-authority epochs |
| Promoted report generation | Compatibility output / adapter output, for CLTR-authoritative epochs; unchanged (authoritative) for legacy epochs |
| CLTR authoritative generation | Authoritative, once cut over, per §4 |
| Recovery state | Reads the resolver, never infers from checkpoint alone (checkpoint remains a resume aid, not a truth source) |

**Existing production report promotion does not collapse with authority publication without
proof.** The brief explicitly warns against this. The proof this document offers: promotion
(writing `latest.*`) and authority publication (switching the production authority pointer) are
kept as **two distinct mechanisms operating on two distinct files**, precisely because
`latest.*`'s promotion path retains Gap B (non-atomic writes) today, while the new
authoritative pointer reuses Stage 2's already-atomic mechanism. Collapsing them would either
(a) force Gap B's non-atomicity onto the authoritative pointer, violating §6's invariant, or
(b) require Gap B's repair as a hard prerequisite of Stage 3 contract freeze, which this
document does not currently require (it is flagged as should-fix-before-implementation, §16,
not blocking-for-freeze). Keeping promotion and authority publication as two mechanisms lets
Stage 3 proceed to contract freeze without first having to schedule and complete a legacy
bug-fix phase — while still leaving `latest.*`'s eventual repair or retirement (§29) open as
future work.

Promotion remains, for now: **authoritative for legacy epochs, a compatibility output for
CLTR-authoritative epochs.** Whether it is later retired entirely is a legacy-demotion-stage
question (§29), not a Stage 3 cutover question.

---

## 19. Recovery architecture

For each failure point the brief lists, the recorded state (never inferred) that recovery must
consult:

| Failure point | Current authority epoch | Authoritative generation | Retry allowed? | Replay allowed? | Rollback allowed? | Roll-forward required? | Operator review required? | Reconciliation method |
|---|---|---|---|---|---|---|---|---|
| Before cutover preparation | Prior (unchanged) | Prior (unchanged) | Yes | Yes | N/A (nothing started) | No | No | N/A |
| During candidate generation | Prior (unchanged) | Prior (unchanged) | Yes | Yes | N/A | No | No | Candidate discarded, no evidence of authority change |
| During verification | Prior (unchanged) | Prior (unchanged) | Yes | Yes | N/A | No | No | Same |
| After certification, before publication | Prior (unchanged) | Prior (unchanged) | Yes (re-attempt publication) | Yes | N/A (not yet published) | No | Recommended, not required | Certification record retained as evidence; safe to retry |
| Before authority publication | Prior (unchanged) | Prior (unchanged) | Yes | Yes | N/A | No | No | Same |
| During pointer preparation (pre-`os.replace`) | Prior (unchanged) | Prior (unchanged) | Yes | Yes | N/A (atomic op never became visible) | No | No | Readback confirms prior pointer unchanged |
| **After atomic authority publication** | **New (target)** | **New generation** | No (already succeeded) | N/A | **Yes, only if no external effect has yet occurred** (§20) | Not yet | No, unless rollback is being considered | Readback confirms new pointer; this is the irreversibility hinge point |
| Before production derivatives are visible | New | New generation | N/A (publication complete) | N/A | Same conditional as above | No | No | Same |
| After report visibility | New | New generation | N/A | N/A | Narrowing — external visibility increases the case for roll-forward over rollback | Preferred | Recommended | Reconciliation confirms report matches pointer |
| Before dispatch | New | New generation | N/A | N/A | Last point at which rollback is architecturally clean | Preferred if any doubt | Recommended | Same |
| **During uncertain dispatch** | New | New generation | Marker-check first, per PFN-001 | Governed by existing exactly-once marker | **No — must not rollback once dispatch may have occurred**, per §20 | Yes, if reconciliation determines a defect | **Yes, mandatory** | `promotion_outcome_unconfirmed`-class outcome, human-reviewed |
| After dispatch, before marker | New | New generation | N/A | Marker check prevents duplicate dispatch | No | Yes if needed | Yes | Same pattern as PFN-001's existing `delivery_recorded_bookkeeping_incomplete` |
| After marker, before receipt | New | New generation | N/A | N/A | No | Yes if needed | Recommended | Reconciliation confirms marker/receipt agreement |
| During receipt finalization | New | New generation | Idempotent retry of receipt-writing only | Yes | No | Yes if needed | No | Existing receipt idempotency |
| During result recording | New | New generation | Idempotent | Yes | No | Yes if needed | No | Existing reconciliation command, extended |

**Recovery must use recorded state, not inference** — every row above resolves from a
persisted artifact (pointer file, certification record, marker, receipt), never from
"apparent" state such as git history proximity or narrative title parsing. This is the direct
carry-forward of §6's invariant into the recovery domain, and it is the architectural answer to
Gap A (legacy's own resume logic recognizing only one of several valid "already succeeded"
states) — Stage 3's resolver-based recovery model does not repeat that narrowness, because it
is designed against CLTR-001's full 14-state model from the start rather than against a
narrower ad hoc check.

---

## 20. Rollback after authority cutover

**This is architecturally distinct from Stage 2 rollback rehearsal**, and this document does
not assume Stage 2's mechanics transfer directly, per the brief's explicit instruction.

| Rollback form | Supported? | Reasoning |
|---|---|---|
| Pointer rollback (pre-external-effect) | **Supported** | Purely local, filesystem-atomic, reversible — identical risk profile to Stage 2 rollback, because nothing externally visible has yet depended on the new pointer |
| Pointer rollback (post-external-effect, i.e., after notification dispatch) | **Forbidden; replaced by compensating roll-forward** | Once a notification has been dispatched (or dispatch is uncertain), an external party may already have observed the new authoritative generation as true. A silent pointer rollback at that point would create a *retroactive* disagreement between what was externally communicated and what the system now claims — this is functionally a new split-brain hazard (an external record vs. an internal record), which §21 requires be prevented, not merely reduced. |
| Authority-epoch rollback | **Forbidden after any epoch-bound external effect**; permitted only pre-effect, following the same boundary as pointer rollback | An authority epoch is coarser than a single generation; rolling it back post-effect has all of pointer rollback's post-effect problems plus it would invalidate every generation published under the rolled-back epoch |
| Production data rollback (i.e., undoing effects on artifacts derived from the authoritative generation — report, metadata, Architecture Status) | **Follows the pointer** — once pointer rollback is disallowed post-effect, derived-artifact rollback is equally disallowed for the same reason; pre-effect, derived artifacts simply haven't been published for the new generation yet | Consistency with the "many deterministic derived representations" principle — derivatives must never diverge from the pointer's own rollback policy |
| External-effect compensation | **This is the only "undo" mechanism available post-effect** — e.g., a corrective notification (already a supported PFN-001 pattern — 135H.2.1 used exactly this: "a prior 'promoted but undelivered' generation retained as truthful non-canonical audit evidence" plus one corrective terminal notification) | Reuses an already-proven recovery pattern rather than inventing a new one |
| Recovery completion | Uses §19's recorded-state model | — |
| Historical supersession | A rolled-forward-past generation becomes historical, immutable, never deleted | Consistent with CLTR-001 |

**Final rule, derived (not assumed) from existing contracts:** *rollback is permitted only
strictly before the first irreversible external effect of a cutover transition; after that
point, correction is achieved exclusively by rolling forward to a new, separately certified
transition, optionally paired with a compensating notification.* This is a direct application
of 135H's own rollback-boundary definition ("reversible until a CLTR-authoritative transition
performs its first irreversible publication/dispatch event") to the cutover-specific case the
brief asks about, rather than a fresh invention — 135H already answered this in the general
case; this document confirms the general rule holds for authority cutover specifically and
finds no reason Stage 3 needs an exception.

---

## 21. Split-brain prevention

| Split-brain form | Prevention mechanism | Detection mechanism | Fail-closed behavior | Reconciliation output | Recovery approach | Audit evidence |
|---|---|---|---|---|---|---|
| Legacy pointer and CLTR pointer both treated as current | Structural: the resolver (§12) is the only reader of "current," and it resolves per-epoch (legacy epochs → legacy pointer; CLTR epochs → CLTR pointer) — never both for the same epoch | Resolver-level assertion: exactly one pointer type is consulted per epoch | Resolver returns an explicit `authority_ambiguous`-class outcome rather than guessing | New reconciliation outcome value (extends the existing 5-value enum) | Human review; both pointers' evidence preserved, never overwritten during investigation | Both pointer files retained; investigation record appended |
| Two CLTR generations treated as current | Compare-and-swap (§11) ensures only one write succeeds; readback (§5, §19) confirms | Readback digest mismatch after a race | Reject the second writer at swap time, not after the fact | `stale_writer_rejected` | Losing writer retries from fresh read | Both attempted generations retained (one published, one historical-but-never-authoritative) |
| Two authority epochs active | Epoch immutability (§7) — a new epoch is only ever created by an explicit cutover transition, never implicitly | Resolver checks the pointer's recorded epoch against the requested epoch | Reject if mismatched (`stale_authority_epoch`, §7.1) | Same enum extension | Operator determines correct epoch; no automatic guess | Epoch history retained per §7 |
| Report derived from one generation while marker/receipt bind another | Shared derivation: report/metadata/marker/receipt all read from the same resolver call within one transaction (§13) | Digest cross-check (already how CLTR-SCHEMA-001's 15 representations bind identity today) | Reject/quarantine if any derivative's digest doesn't match the resolver's current answer | Existing `conflict` outcome | Regenerate the mismatched derivative from the authoritative generation | Mismatch recorded as evidence |
| Notification payload from one generation while report comes from another | Same shared-derivation-within-one-transaction rule | Same digest cross-check | Same | Same | Same | Same |
| Recovery process using stale authority | §19's recorded-state model (never inference) | Pointer read is always fresh at recovery time | Recovery refuses to proceed on stale in-memory assumptions | `promotion_outcome_unconfirmed`-class | Re-read pointer before any recovery decision | Recovery evidence records the pointer state it acted on |
| Separate entry points resolving different authority | §12's single shared resolver | N/A — structurally impossible if the resolver is truly the only path | N/A | N/A | N/A | Resolver call is logged/evidenced per invocation |
| Filesystem pointer and evidence record disagreeing | Manifest/digest cross-verification (existing mechanism, `manifest.py`/`digest.py`) | Digest recompute-from-disk-bytes (already implemented, reused from 135U's rollback step 6) | Quarantine the disagreeing generation | `conflict` | Human review; never auto-resolve by preferring one side | Both pointer and evidence record preserved |

Every prevention/detection pair above reuses a mechanism this repository has already built and
tested (compare-and-swap extends the existing atomic-replace primitive; digest cross-check
reuses 135U's own recompute-from-disk-bytes step; the reconciliation-outcome enum extends
CLTR-SCHEMA-001's existing 5 values) rather than introducing new machinery — consistent with
this document's overall finding that Stage 3's *architecture* is largely a matter of
re-targeting and gating what Stage 2/rollback already proved, plus a small number of genuinely
new pieces (certification, compare-and-swap, typed authority epoch) named explicitly
throughout.

---

## 22. Security and containment architecture

Carried forward, with an explicit sufficiency judgment for production authority use:

| Concern | Stage 2 mechanism | Sufficient for production authority as-is? |
|---|---|---|
| Traversal safety | `persistence.py` path containment | Yes — no reason production paths need a different containment model |
| Symlink safety | Symlink-rejection checks (135T's F-135T-1 repair made this actually-called, not merely defined) | Yes, provided the same call-site-wiring discipline is maintained — F-135T-1 is a direct warning that a *defined* protection is not the same as an *invoked* one; Stage 3 implementation must independently verify invocation, not merely definition, exactly as 135T did |
| Pointer substitution protection | Atomic replace + readback | Yes, extended with compare-and-swap (§11) |
| Manifest substitution protection | Digest verification | Yes |
| Artifact substitution protection | Digest verification | Yes |
| Wrong phase/transition/revision rejection | `validate_generation_target` | Yes |
| Wrong migration epoch rejection | Epoch-scoped directory structure | Yes |
| **Wrong authority epoch rejection** | Exact-prefix string check (post F-135U-2) | **No — insufficient for production; requires the typed model (§7.1)** |
| Schema substitution rejection | MAJOR-version fail-closed (CLTR-SCHEMA-001) | Yes |
| Stale-writer rejection | **Not yet implemented** (135U's mechanism is last-write-wins, acceptable only pre-authority) | **No — requires §11's compare-and-swap extension** |
| Conflicting replay rejection | Idempotency + conflict outcomes (135U) | Yes, pattern transfers, needs re-application to the new pointer |
| Quarantine protection | `QUARANTINED` overlay | Yes |

**Summary judgment:** Stage 2's filesystem assumptions (atomicity via `os.replace`, path
containment, symlink rejection, digest verification) are sufficient for production authority
**as physical mechanisms**. The two areas needing strengthening before production use are not
physical/filesystem concerns at all — they are **identity-strength concerns**: the authority
epoch's string-based check (§7.1) and the absence of compare-and-swap semantics (§11). Both are
already named as prerequisites elsewhere in this document; this section exists to confirm no
*additional* filesystem-level hardening is required beyond what 135S/135T/135U already built
and tested.

---

## 23. Schema and version readiness

Evaluating CLTR-SCHEMA-001 v1.0.1 against the brief's checklist, without modifying it:

| Required representation | Present in v1.0.1? | Gap classification |
|---|---|---|
| Authoritative generation identity | Yes (`transition_id`, digest, persistence contract) | Not required |
| Authority epoch transition | Partially — the string-concatenation format exists but has no dedicated typed field for "this generation's target authority epoch differs from its source" | **Required minor schema revision** (a `cutover_transition` block, additive — would not require a MAJOR bump per CLTR-SCHEMA-001's own additive-compatible rules) |
| Cutover certification | No | **Required minor schema revision** — a new `cutover_certification` block (§4), additive |
| Cutover evidence | No, as a named kind — but the existing evidence-record pattern (135U's rollback evidence, 135O's migration evidence) is directly reusable | **Required schema clarification**, not a structural gap — the pattern exists, only the specific evidence-kind name needs adding |
| Pointer publication state | Yes — the existing `current`-pointer-file pattern is reused | Not required |
| Uncertainty | Yes — `reconciliation_outcome`'s 5 values already model this generally | **Future-compatible optional field** — a cutover-specific uncertainty state may be worth adding for clarity, but the existing 5 values are not incorrect, merely generic |
| Concurrency conflict | No dedicated value yet (`conflict` exists but is generic) | **Required schema clarification** — recommend a `stale_writer_rejected` value, additive |
| Stale-writer rejection | Same as above | Same |
| Production rollback/roll-forward classification | No | **Required minor schema revision** — needs values distinguishing pre-effect rollback from post-effect roll-forward-as-compensation, per §20 |
| Marker/receipt bindings | Yes, structurally (15 representation kinds already include marker and receipt with identity/digest fields) | Not required — only the *authority-epoch* field needs to actually be populated for these kinds once Stage 3 exists, which is an implementation task, not a schema gap |
| Notification uncertainty | Yes (PFN-001's existing outcomes) | Not required |
| Historical compatibility | Yes — immutable-history + compatibility-adapter contract (5 comparison modes, 135J §21.4) already generalizes to any new representation kind | Not required |

**Overall schema disposition: CLTR-SCHEMA-001 v1.0.1 is *not* sufficient for Stage 3 as
written, but every gap found is additive** (new optional blocks/enum values), consistent with
its own semantic-versioning rules — none requires a MAJOR bump or breaks existing consumers.
**Classification: required minor schema revision, Blocking before contract freeze can be
considered *complete for implementation purposes*, but not Blocking for this readiness
document's own conclusion**, because 135V's job is to identify this requirement precisely
enough for 135W to act on it, not to perform the revision itself (forbidden by this phase's
scope).

---

## 24. Feature-configuration architecture

Proposed Stage 3 controls, kept structurally separate from every existing flag (per the
brief's explicit requirement) — **no environment variable introduced in 135V activates
anything, because no environment variable is introduced in 135V at all; the table below is a
design proposal for 135W, not a present-tense configuration.**

| Proposed control | Purpose | Relationship to existing flags |
|---|---|---|
| Stage 3 code availability | Gates whether Stage 3 code paths exist/import at all | Analogous to how `src/pcae/cltr/` existing modules can be imported/tested without `PCAE_CLTR_SHADOW_ENABLED` being set — code presence and activation are already kept separate in this codebase, and Stage 3 should follow the same pattern |
| Readiness-only mode | Allows evidence accumulation (certification dry-runs) without ever permitting an actual pointer switch | New, no analog yet — closest existing precedent is Stage 2 rehearsal's own "evidence without authority" posture, generalized one level up |
| Cutover request | The explicit, single-transition nomination-to-certification-to-publication request | New; must require explicit operator input (§25), never inferred from an environment variable's mere presence |
| Operator authorization | Binds a specific transition + digest + epoch pair (§25) | New |
| Target authority epoch | Must be explicit per request, never a persistent global default that silently applies to future transitions | New — this directly addresses the brief's "a single Boolean must not control the entire migration" principle already established by 135M for Stage 1/2, extended to Stage 3 |
| Emergency disable | An immediate revert-to-legacy-default control, usable even mid-incident | New; must not itself be capable of rewriting history — it only affects the resolver's future behavior, never past generations |
| Recovery-only mode | Permits reconciliation/read-only commands even if Stage 3 code is otherwise disabled | Analogous to existing reconciliation commands already being unconditionally read-only regardless of feature flags |
| Legacy compatibility mode | Governs whether legacy `latest.*`/report rendering continues to be populated after cutover (§16, §18) | New |
| Retirement stage | A separate, later-stage control (§29), explicitly out of Stage 3's own scope | New, deferred |

**Prefer configuration contracts over ad hoc flags:** consistent with 135M's own principle
("a single Boolean must not control the entire migration"), each control above governs one
concern; none is a master switch that, alone, could move production authority. Multiple
independent controls must agree before any pointer-switching behavior is reachable — this is
itself a defense-in-depth application of §6's single-authority invariant to the configuration
surface, not just the data model.

---

## 25. Human authorization

Authority cutover must require explicit governed human authorization, per the brief. Proposed
model (design only, no implementation):

| Element | Proposed answer |
|---|---|
| Who authorizes | A human operator with repository write access, acting through a governed command (not an automated agent, not a CI job) — consistent with this repository's existing pattern of the human being the one who runs `pcae` commands and reviews reports |
| What evidence is presented | The full pre-cutover gate (§9) evaluation result, plus the readiness evidence package (§26) |
| What exact action is authorized | Publication of one specific certified cutover generation, for one specific transition — never a standing "authorize all future cutovers" grant |
| How scope is bounded | Authorization binds to a single `transition_id` + generation digest + target authority epoch triple; it does not carry over to any other transition, even a superficially similar one |
| Binding to migration epoch, transition, generation, digest | All four values are part of the same signed/recorded authorization artifact — none may be substituted independently after the fact |
| Expiration or freshness | Proposed: authorization must be freshly obtained per transition and should expire if not acted on within a bounded window (exact bound TBD in 135W — this document does not fix a number, consistent with how 135D also left the final-revision grace-period bound as an open quantitative parameter for a later phase) |
| Replay prevention | The same transition-identity replay-stability mechanism already in place (135N design B) prevents a stale authorization from being reused against a different generation, provided the authorization itself is bound to the generation digest (not merely the transition_id) |
| Revocation before publication | Must be possible — an operator must be able to withdraw authorization any time before the atomic pointer switch actually executes, with no partial effect |
| Audit record | A durable, append-only authorization-decision record, analogous to existing evidence records (rollback evidence, migration evidence) |
| Two-person approval | Not proposed as a requirement for the *first* cutover contract — this document defers that question explicitly to a later phase, noting only that the authorization model above (single artifact binding all four identity elements) would compose cleanly with a future two-person requirement if one is later adopted, without needing to be redesigned |

No approval-handling implementation is proposed in this phase.

---

## 26. Readiness evidence package

The Stage 3 readiness package aggregates (references, does not duplicate) evidence from:

- Stage 1 mechanism + verification (135O/135P)
- Stage 2 mechanism + verification (135S/135T)
- Rollback rehearsal + verification (135U)
- This document's schema-gap findings (§23)
- This document's authority-inventory findings (§3)
- This document's concurrency-readiness findings (§11)
- This document's recovery-readiness findings (§19)
- Production-output-equivalence status (currently incomplete — adapter-wiring gap, §9)
- Notification/marker/receipt migration readiness (§§14–15, design-only)
- Security and containment review (§22)
- The full unresolved-findings register (§27)
- Operator-authorization readiness (§25, design-only, not implemented)

**This package remains derivative evidence.** It aggregates pointers to already-existing,
already-verified artifacts (phase reports, test results, this document) — it is not itself a
new authority, and its existence does not activate anything. Consistent with the brief, it
must not itself be treated as sufficient grounds for cutover; §9's gate and §25's human
authorization remain the actual gating mechanisms.

---

## 27. Acceptance criteria

Advancing from 135V to Stage 3 contract freeze (135W) requires:

1. One precise target authoritative object — **satisfied by this document (§4)**.
2. One production authority resolver — **specified conceptually (§12); not yet implemented (expected)**.
3. One authority publication boundary — **specified (§13(b))**.
4. One authority-epoch transition model — **specified conceptually (§5, §7); typed-model implementation deferred (§7.1)**.
5. No dual-authority steady state — **proven at the architecture level (§6, §21); not yet implemented**.
6. All-four-entry-point convergence — **specified (§12); already structurally supported by the existing shared transaction function**.
7. Complete concurrency model — **specified (§11); compare-and-swap extension not yet implemented**.
8. Crash/recovery model — **specified (§19); not yet implemented**.
9. Notification exactly-once migration model — **specified (§14); PFN-001 unchanged**.
10. Marker/receipt binding model — **specified (§15)**.
11. Report/metadata/Architecture Status derivation model — **specified (§§16–17)**.
12. Checkpoint/promotion migration model — **specified (§18)**.
13. Legacy compatibility model — **specified (§4, §16, §18)**.
14. Rollback/roll-forward policy — **resolved (§10, §20)**.
15. Schema readiness disposition — **resolved: additive revision required (§23)**.
16. Configuration architecture — **specified (§24)**.
17. Operator authorization model — **specified conceptually (§25); not yet implemented**.
18. Security and containment assessment — **complete (§22)**.
19. All 135U limitations classified — **complete (§10)**.
20. No unresolved architectural Blocking finding — **true as of this document (§28's finding table below has zero Blocking-for-freeze entries)**.

**All twenty acceptance criteria for the contract-freeze milestone are satisfied at the design
level by this document.** None requires new source code to satisfy — each is a design
question this document answers, which is exactly what distinguishes "ready to freeze a
contract" from "ready to implement" (§1). Items 2, 7, 8, and 17 explicitly still require
*implementation* work in later phases; their presence in this list as "specified, not yet
implemented" is not a gap in 135V's own readiness verdict, since 135V's verdict concerns
contract-freeze readiness, not implementation completeness.

---

## 28. No-go criteria

None of the following conditions are currently present; each would independently prohibit
contract freeze if it were:

- Unclear authoritative object — **not present**; §4 is precise.
- More than one authority resolver — **not present**; §12 specifies exactly one.
- Unresolved dual-authority period — **not present**; §6 proves single resolution at every
  boundary, including transient preparation states.
- Caller-specific authority logic — **not present**; §12 explicitly forbids it.
- No concurrency protocol — **not present as a design gap** — §11 specifies the required
  protocol (compare-and-swap); it is simply not yet implemented, which is expected at this
  milestone.
- No stale-writer rejection — **specified (§11, §22)**; not yet implemented, expected at this
  milestone.
- No recovery state for post-publication crashes — **specified (§19)**.
- No notification exactly-once model — **not present**; PFN-001 already provides this and is
  preserved (§14).
- Report/marker/receipt generation mismatch risk — **addressed structurally (§21)**.
- Unsupported schema gap — **schema gaps found are all additive (§23), not unsupported**.
- Cross-epoch ambiguity — **resolved (§10)**.
- Production rollback ambiguity — **resolved (§20)**.
- Unresolved containment concern — **none found (§22)**.
- Unresolved Blocking finding from prior stages — **zero, as of 135U (§9, §28's finding table)**.
- Unclear human authorization — **model specified (§25)**; the *mechanism* is not yet built,
  which does not by itself trigger this no-go condition at the contract-freeze milestone, but
  would trigger it at the activation milestone if still unbuilt.
- Inability to prove production-output binding — **not fully provable yet** — the
  adapter-wiring gap (F-135L-2, carried forward, §9) means production-output equivalence
  cannot currently be empirically demonstrated end-to-end. This is the one item in this section
  worth flagging explicitly: it does **not** block contract freeze (the contract can be written
  and frozen without live evidence), but it **would** block progression from contract freeze to
  implementation-readiness if left unresolved, because implementation without live
  production-output comparison would mean building Stage 3 against untested assumptions about
  what "equivalent" actually means in practice.

**No no-go condition currently applies to contract freeze.**

---

## 29. Legacy authority demotion stages

Reconstructing 135H's proposed 9-stage cutover strategy into a smaller, explicitly staged
sequence consistent with what Track 135's actual phase sequence (not 135H's original plan,
which diverged from what was actually built) implies is achievable:

| Stage | Authority state | Legacy role | Rollback/roll-forward support | Evidence requirements | Exit criteria | Forbidden actions |
|---|---|---|---|---|---|---|
| **Stage 3A** — CLTR-authoritative generation publication, legacy derivatives retained | CLTR authoritative for cut-over epochs | Legacy `latest.*`/report rendering retained as compatibility output, still populated | Pointer rollback pre-effect; roll-forward post-effect (§20) | Full pre-cutover gate (§9) passed per transition | Sustained successful operation across a defined evidence window (exact bound: future phase) | Deleting or disabling any legacy compatibility output |
| **Stage 3B** — legacy authority reads disabled, compatibility outputs retained | CLTR authoritative | Legacy code no longer *consulted* for authority decisions, but its outputs still exist as compatibility artifacts | Same as 3A | Demonstrated absence of any remaining read-path dependency on legacy authority | Confirmed zero production code paths still treat legacy as authoritative | Removing legacy's compatibility *output* generation (as opposed to its authority-reading role) |
| **Stage 3C** — legacy fallback disabled | CLTR authoritative, no legacy fallback | Legacy code present but inert; no automatic fallback-to-legacy path remains, closing off the "legacy preferred if both exist" anti-pattern permanently (§6) | Roll-forward only; pointer rollback likely no longer meaningful since there's nothing to fall back to | Proof that no recovery path silently reverts to legacy | Confirmed no code path can reintroduce legacy as an authority, even during incident recovery | Reintroducing any legacy authority-reading path, even "temporarily" |
| **Stage 4** — legacy authority code retirement | CLTR authoritative, legacy retired | Legacy lifecycle-authority code removed (compatibility-rendering code may or may not be retired independently) | Roll-forward only (legacy is gone) | Full retirement decision record (separate governed phase) | N/A — terminal stage | N/A |

Authority cutover (Stage 3, this document's subject) and legacy code retirement (Stage 4) are
kept as clearly separate events, as the brief requires — Stage 3A already fully satisfies
"single authority" (§6) the moment it completes; Stages 3B/3C/4 are about progressively
reducing legacy's *footprint*, not about resolving any remaining authority ambiguity.

---

## 30. Recommended implementation roadmap

Derived from this document's own findings, not assumed in advance:

1. **135W — Stage 3 Authority-Cutover Contract Freeze.** Freezes: the target authoritative
   object (§4), the authority-transition event (§5), the single-authority invariant (§6), the
   typed authority-epoch model requirement (§7.1, as a contract-level requirement — the typed
   model's *implementation* is a later phase), the pre-cutover gate (§9), the concurrency
   protocol requirement (§11, again as a contract-level requirement), the CLTR-SCHEMA-001
   additive revision (§23, as a frozen amendment — a new v1.1.0 or equivalent MINOR bump), the
   configuration architecture (§24), and the human-authorization model (§25).
2. **135X — Stage 3 Authority-Cutover Contract Verification.** Independent adversarial review
   of 135W, following the same discipline that caught F-135N-1 and the §21.4 gap at the
   equivalent step for earlier stages.
3. **Prerequisite implementation phase(s), before any authoritative-publication code is
   written** — this document explicitly does **not** recommend jumping straight to "authority
   resolver implementation" after 135X, because §9 and §22 found two concrete gaps that would
   otherwise be discovered mid-implementation, exactly the pattern 135N had to repair
   mid-verification (F-135N-1) rather than catching earlier:
   - **Concurrency/compare-and-swap hardening** for the existing atomic-pointer-replace
     primitive (§11) — this can be built and tested against the *existing* Stage 2 rehearsal
     pointer first (lower risk, no production exposure), before it is ever reused for a
     production authority pointer.
   - **Authority-epoch typed model** (§7.1) — replacing the string-concatenation format with a
     structured, strongly validated type, closing off the exact class of defect F-135U-2 found
     in the string-based check.
   - **Adapter-source wiring** (F-135L-2, carried forward through every Stage 1/2 phase
     unrepaired) — without this, no empirical production-output-equivalence evidence can ever
     accumulate, which §28 already flags as blocking progression from contract-freeze to
     implementation-readiness.
4. **135Y — Authority Resolver and Cutover Evidence Implementation.** Implements §12's resolver,
   §4's certification model, and §5's transition event, built against the hardened primitives
   from step 3.
5. **135Z — Authority Resolver Independent Verification.**
6. **136A — CLTR-Authoritative Publication Implementation** (first real cutover mechanism,
   still gated by explicit human authorization per transition, §25 — this phase does not itself
   authorize any cutover, it builds the mechanism that a future authorized transition would use).
7. **136B — CLTR-Authoritative Publication Independent Verification.**
8. **136C — Legacy Authority Demotion Plan** (Stage 3A→3B→3C→4 sequencing from §29, as its own
   planning phase, not folded into 136A/136B).

This roadmap does not skip the prerequisite-hardening phases in step 3 merely to keep the
numbering short — the brief explicitly warns against inflating the roadmap unnecessarily but
equally against concealing required work, and this document's own findings (§9's
adapter-wiring gap, §11's compare-and-swap gap, §7.1's typed-epoch gap) are concrete enough
that scheduling them after contract verification (135X) but before resolver implementation
(135Y) is the schedule the evidence actually supports, not an arbitrary insertion.

---

## Findings register

| ID | Title | Source | Affected stage | Authority impact | Exactly-once impact | Recovery impact | Concurrency impact | Schema impact | Disposition | Latest acceptable resolution point |
|---|---|---|---|---|---|---|---|---|---|---|
| F-135V-1 | Authority-epoch check is string-prefix-based, insufficient for production | §7.1, inherited from F-135U-2 | Stage 3 | High | None | None | None | Requires typed model | **PREREQUISITE** for implementation | Before 135Y |
| F-135V-2 | No compare-and-swap on the atomic pointer-replace primitive | §11, inherited from F-135R-4 | Stage 3 | High | None | Medium (post-publication crash ambiguity if racing) | High | Requires stale-writer enum value | **PREREQUISITE** for implementation | Before 135Y |
| F-135V-3 | Adapter comparison sources not wired at real call sites | §9, inherited from F-135L-2 | Stage 1/2/3 | Medium (blocks evidence accumulation, not correctness) | None | None | None | None | **PREREQUISITE** for implementation-readiness (not contract-freeze) | Before 135Y |
| F-135V-4 | CLTR-SCHEMA-001 lacks cutover-certification/authority-epoch-transition/stale-writer fields | §23 | Stage 3 | High | None | None | Medium | Direct | **PREREQUISITE**, additive schema revision | Within 135W |
| F-135V-5 | Legacy `latest.*` non-atomic writes (Gap B) increase in importance once compatibility outputs are derived from them post-cutover | §16, §18, inherited from 134F Gap B | Legacy / Stage 3 compatibility | Low (compatibility-only, not authoritative) | None | Low | None | None | **DEFERRED** — should-fix-before-implementation, not blocking | Before 136A |
| F-135V-6 | Architecture Status narrative-parsing derivation remains unmigrated | §17, inherited from 135C | Legacy / Stage 3 | Medium (precedent risk, not current live authority risk) | None | None | None | None | **PREREQUISITE** for Stage 3 activation (must not consult it as authority), **DEFERRED** for contract freeze/implementation | Before 136A activation |
| F-135V-7 | Two-person cutover approval not designed | §25 | Stage 3 | Low (single-person authorization is architecturally sufficient for freeze) | None | None | None | None | **DEFERRED** | Future governance phase, not required for 135W |
| F-135V-8 | Exact authorization freshness/expiration window unspecified | §25 | Stage 3 | Low | None | None | None | None | **DEFERRED** — quantitative parameter for 135W | Within 135W |

No CONFIRMED-BLOCKING-for-contract-freeze finding exists. Findings F-135V-1, F-135V-2,
F-135V-3, and F-135V-4 are **PREREQUISITE for implementation**, not for contract freeze itself
— this document's central conclusion (§31) reflects that distinction precisely.

---

## 135U limitation disposition table

| Limitation | Current support | Authority relevance | Risk | Required behavior | Required phase | Blocking for freeze? | Blocking for implementation? | Blocking for activation? | Final architectural disposition |
|---|---|---|---|---|---|---|---|---|---|
| Rollback to no current rehearsal | Not implemented (rehearsal scope only) | High for production | Medium | Legacy is the implicit default authority absent a published CLTR pointer; "no pointer" must never mean "no authority" | 135W / 135Y | No | Yes | Yes | Resolved conceptually (§10); implementation required |
| Cross-epoch rollback reconciliation | Not implemented | High | Medium | Permanently forbidden; cross-epoch movement is always a new transition | 135W | No | No | No | Permanently forbidden, final |
| Concurrent rollback-vs-forward race | Last-write-wins (acceptable pre-authority only) | Critical for production | High | Compare-and-swap on expected generation digest | 135W (contract) / prerequisite hardening phase (implementation) | No | **Yes** | Yes | Prerequisite implementation required before Stage 3 resolver work |
| Separate roll-forward command | Not implemented (preference only, 135Q §37) | Low | Low | None — ordinary new transition suffices | n/a | No | No | No | Deferred indefinitely, not required |

---

## No-implementation proof

This phase confirms explicitly:

- No production source changed.
- No test source changed.
- No Stage 3 code was added.
- No cutover feature flag was activated (none was introduced).
- No CLTR authority was created.
- No production pointer changed.
- No authority epoch changed.
- No legacy authority was demoted.
- No legacy authority was retired.
- No notification path changed.
- No marker or receipt behavior changed.
- No execution capability was introduced.

Runtime remains: **Observed**, maximum capability **observe**, execution availability
**unavailable** — confirmed live via `pcae runtime inspect` during this phase's initial
inspection.

---

## Readiness verdict

**CONDITIONALLY READY — PREREQUISITES REQUIRED**

135V finds the Stage 3 authority-cutover **contract** ready to be frozen next (135W) — every
design question the brief requires this document to answer (§§4–29) has a precise, sourced
answer, and zero Blocking findings exist against the contract-freeze milestone specifically
(§27, §28). This is not a "READY FOR STAGE 3 CONTRACT FREEZE" verdict without qualification,
however, because three concrete prerequisites (F-135V-1 typed authority-epoch model, F-135V-2
compare-and-swap concurrency protocol, F-135V-3 adapter-source wiring) must close **before
implementation may begin**, even though none of them blocks the contract *freeze* step itself.
The verdict is therefore conditional on the roadmap in §30 being followed in order — contract
freeze and verification first, then the three prerequisite hardening items, then resolver
implementation — rather than allowing contract freeze to be read as tacit permission to start
building the resolver immediately.

This verdict evaluates readiness to freeze a contract. It does not evaluate, and must not be
read as asserting, readiness to implement, activate, or retire legacy authority (§1).

---

## Recommended next phase

**135W — Stage 3 Authority-Cutover Contract Freeze**, scoped to freeze exactly the design
content this document specifies (§§4–9, §11, §23–25), including the additive
CLTR-SCHEMA-001 revision, and explicitly required to enumerate the three implementation
prerequisites (F-135V-1/2/3) as Blocking-for-implementation (not Blocking-for-freeze) findings
carried forward, consistent with §27's finding classification. 135V does not begin 135W.
