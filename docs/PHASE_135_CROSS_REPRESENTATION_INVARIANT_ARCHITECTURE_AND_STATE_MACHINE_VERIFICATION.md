# Phase 135D — Cross-Representation Invariant Architecture and State-Machine Verification

**Phase class:** Architecture + Formal Verification (Track 135, fourth phase)
**Scope:** Turn the verified CLTR-001 v1.0 contract into a precise, implementation-independent behavioral model: final state inventory, transition inventory, invariant formalization, representation-state matrix, retry/resume/replay matrices, failure model, conformance model, reachability/terminal analysis, determinism and safety proofs. No implementation, no JSON schema, no runtime behavior change, no repair of any disclosed gap.
**Predecessor:** 135C — Canonical Lifecycle Transition Record Contract Verification (verdict: VERIFIED WITH NON-BLOCKING DEFERRED QUESTIONS; zero Blocking findings; ten non-blocking deferred questions).
**Non-goal:** Begin 135E or any later Track 135 phase; implement CLTR; add source code; freeze a schema.

---

## 0. Initial inspection (this session)

Re-run at session start, independently, not copied from any prior phase's report text:

- `git status --short` / `--branch --short`: clean, `main...origin/main`, no divergence.
- `git log --oneline -30`: matches the recorded Track 135 history (135A → 135B → 135C, each with its own completion/sync/repair commit cycle); no unexpected commits.
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy (idle), all required files present, agent lock held by `claude-local`, Git status clean.
- `pcae check`: passed, no active task at session start (task contract for this phase created immediately after, per governed workflow).
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae push check`: clean, nothing to push.
- `pcae runtime inspect`: Observed / observe / execution unavailable, 0 plugins, 0 capabilities registered — unchanged from every prior Track 135 phase's finding.
- `pcae notify status`: Telegram configured, enabled, ready for outbound delivery; auto-finalization hook available with `telegram` as the configured sink; external network active-by-default is `False`.
- `pcae phase-report show --latest`: 135C, status completed, report completeness complete, verdict VERIFIED WITH NON-BLOCKING DEFERRED QUESTIONS, recommended next phase 135D.
- `pcae irg-challenge`: 5 persistent advisory concerns (SRR-66C-002 staleness, SLR-69P-001/SRR-66B-001 lineage, OBJ-004 thin coverage, strategic_governance capability growth, 69P missing successor), calibration "consistent, no change detected" — identical to every prior Track 135 phase's run. Re-classified in §30 below; none is a CLTR-001/lifecycle-state-authority concern.

Source re-verification performed directly in this session (not assumed unchanged from 135C's ~research):

1. `src/pcae/core/finalization_transaction.py:596-602` — the resume check reads:
   ```python
   if (
       existing is not None
       and existing.get("report_digest") == report_digest
       and existing.get("finalization_snapshot_id") == finalization_snapshot_id
       and existing.get("status") == "completed"
   ):
   ```
   Only the literal string `"completed"` is treated as resume-terminal. `"completed_receipt_best_effort_incomplete"` (line 794/798) falls through this check. **Gap A still live**, exactly as 134F, 135A, 135B, 135C found.
2. `src/pcae/core/canonical_artifact_promotion.py:111,115,141` — three plain `path.write_text()` calls, no `os.replace` anywhere in the file. **Gap B still live**, three sites (matching 135C's corrected count, not 135A/135B's original two-site count).
3. `src/pcae/core/phase_reports.py:1850,1857,1859,1863` (inside `detect_cross_phase_commit_contamination`, defined at line 1819) — unresolvable/fabricated hashes are silently `continue`d past, collapsing "unverifiable" into "verified" by omission. **Gap C still live**.
4. All four entry points (`src/pcae/commands/phase.py`, `task.py`, `phase_reports.py`, `notifications.py`) still independently gate on their own marker check before calling `run_finalization_transaction()`. No shared resume authority exists.
5. `grep -ri "transition_id\|canonical_lifecycle\|CLTR-001" src/pcae`: zero hits. No implementation of CLTR-001 exists — correct, since 135A–135C are architecture/contract/verification-only phases.
6. `docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md` (PFN-001, §4 "Phase Finalization Notification Invariant", §8 "Delivery Guarantees") re-read for its exact guarantee text: "exactly one trusted canonical phase report delivered" per governed terminal completion, outbound-only, idempotent via `.last-notified.json`/`certify_notification_transition()`. No clause in this document proposes any change to that guarantee.

No drift found anywhere. All findings this phase builds on are independently re-confirmed live, not merely inherited.

---

## 1. Normative source hierarchy

This phase is bound by the following authority order, highest first. A lower-numbered source always wins in case of apparent conflict; a conflict that cannot be resolved this way is itself a finding (§39).

1. **CLTR-001 v1.0** (`docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT.md`) — the frozen, binding contract. Every state, transition, invariant, and classification in this document must trace to a CLTR-001 clause or be explicitly flagged as a 135D-derived clarification, candidate amendment, implementation-level invariant, or non-blocking recommendation (§12, §37).
2. **Verified 135C findings** (`docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT_VERIFICATION.md`) — the independent verification verdict and its ten disclosed non-blocking findings, which this phase is specifically tasked with dispositioning (§37).
3. **135A architecture** (`docs/PHASE_135_CANONICAL_LIFECYCLE_STATE_AUTHORITY_ARCHITECTURE.md`) — the pre-contract architectural reasoning; used only where CLTR-001 itself defers to it by citation, never as an independent source that could override CLTR-001.
4. **134F independently verified lifecycle behavior** (`docs/PHASE_134_WHOLE_LIFECYCLE_INDEPENDENT_VERIFICATION.md`) — the last independently-verified account of Track 134's actual, current lifecycle behavior; used as compatibility/gap evidence, not as a source of new normative requirements.
5. **PFN-001** (`docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`) — unamended; this phase's notification-state modeling (§21) must remain strictly compatible with it.
6. **PFR-001** (`docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_SPECIFICATION.md` and its contract/verification companions) — unamended; this phase's report-representation modeling (§9) must remain strictly compatible with it.
7. **Current production implementation** — `finalization_transaction.py`, `canonical_artifact_promotion.py`, `phase_reports.py`, the four entry points — used exclusively as **compatibility evidence**: to confirm a disclosed gap is still live, to ground an invariant in a real defect class, or to classify current behavior under §29 (compatibility-state architecture). Current behavior is never permitted to override, narrow, or silently reinterpret any CLTR-001 clause.

### 1.1 Handling of current-behavior divergence

Three divergences between current implementation and CLTR-001 are already on record (Gaps A, B, C above, all independently re-confirmed §0). Per this phase's own instructions, each is:

- **documented** (§0, and again where structurally relevant: §16 irreversibility, §19 conformance, §27 failure model, §35 safety proof);
- **classified as legacy behavior** — current implementation is classified `adapter` throughout (matching CLTR-001 §24.1), never `native`, for any behavior that diverges from a CLTR-001 requirement;
- **not imported into the state machine** — the state machine defined in §3–§6 below is derived from CLTR-001's normative text, never from what `finalization_transaction.py`'s flat status string actually does today;
- **not repaired** — no source file is touched by this phase (confirmed in §41 files-changed and §44 no-go confirmations).

---

## 2. State-machine purpose

### 2.1 Why a formal state machine is required

CLTR-001 §7 already froze a state model as binding contract text. This section states *why* that freeze is necessary, independently re-derived rather than assumed, because the assignment requires the purpose itself to be re-justified, not merely the state names.

A lifecycle **must** be governed by an explicit, centrally-owned state machine — rather than a flat status string interpreted independently by each consumer — because:

1. **It prevents impossible transition sequences.** A flat string (`"completed"`, `"completed_receipt_best_effort_incomplete"`, `"pre_promotion_certification_failed"`, ...) carries no structural guarantee that, e.g., a `"promoted"`-shaped value could never appear without a prior `"certified"`-shaped value having been true. A state machine with an explicit permitted/forbidden-next-state table (§5, §6) makes an impossible sequence a rejected transition, not merely an unlikely one.
2. **It establishes terminality centrally.** Today, "is this transition over" is answered differently by four independent entry points' marker checks and by the transaction's own resume check — and 134F's central finding is exactly that these two answers can disagree (Gap A). A state machine that owns terminality (§5's terminal column) makes this a single fact with a single source, per CLTR-RETRY-1 (CLTR-001 §26.1).
3. **It prevents entry-point-specific lifecycle interpretation.** Four entry points each independently deciding "has this already happened" is the literal mechanism of the safety-through-cooperation pattern 135A §1.1 identifies as Track 135's reason for existing. A state machine owned by the record itself removes the need for, and the risk of divergence among, per-entry-point interpretation.
4. **It defines when canonical authority changes.** Some facts are S-role only from a certain state onward (e.g., certified_state, CLTR-001 §3.2). Without an explicit state machine, "from a certain state onward" has no crisp boundary — it becomes a matter of reading code, not reading a specification.
5. **It defines when derivatives may appear.** CLTR-001 §8.2 invariant 4 ("no marker before required delivery classification") is only enforceable if "required delivery classification" is a named state (NOTIFIED/NOTIFIED_UNCONFIRMED) with a clear entry condition.
6. **It defines when external visibility may occur.** PROMOTED and later states are the first states with real external effects (CLTR-001 §7.3's "External visibility" column). A state machine is what makes "before/after this boundary" checkable at all.
7. **It defines when irreversible actions may occur.** CLTR-ORDER-4 ("no irreversible stage precedes semantic certification") is a state-ordering invariant; it has no meaning without a state machine to order against.
8. **It supports deterministic recovery.** §22–§26 below (retry/resume, replay, failure, NOTIFIED_UNCONFIRMED) all depend on recovery logic being able to ask "what state is this record in" and get one unambiguous answer.
9. **It supports independent verification.** A future 134F/135C-style verification pass needs a finite, named set of states and transitions to check exhaustively (reachability, terminality, invariant satisfaction) — an unstructured status string cannot be exhaustively verified because it has no declared boundary on what values are even possible.

### 2.2 What the state machine must not do

Restating and holding firm to CLTR-001 §2.2 and §28 (unchanged, not re-derived — these are non-negotiable governance boundaries, not architectural choices open to re-justification):

1. **Execute commands.** The state machine records what stage a transition has reached; it never itself invokes `promote_and_dispatch()`, a shell command, or any backend capability. State transitions are facts to be recorded, driven by the finalization transaction's own existing call graph, not a new invocation path.
2. **Authorize execution.** No state (including CERTIFIED, PROMOTED) is or implies a permission grant. CLTR-SAFE-2 (CLTR-001 §26.1) is restated as binding on this document's own state model in §35.
3. **Make policy decisions unrelated to lifecycle finalization.** The state machine does not decide whether an `unverifiable` commit hash should block a transition (§10.4's deferred policy question, addressed as still-deferred in §17 below) — it only defines that the record must be able to represent the distinction.
4. **Infer missing authority.** A state transition either has its required preconditions satisfied by declared/verified facts, or it does not occur. Nothing in this model guesses a missing precondition to let a transition proceed (CLTR-AUTH-2).
5. **Reconstruct provenance heuristically.** Commit ownership, identity, and evidence bindings are never inferred from naming, recency, or prose by this state machine (CLTR-001 §4.2 items 6–7, restated in §14 below).

---

## 3. State model re-derivation

### 3.1 Method

Per the assignment's explicit instruction, the candidate list below is evaluated fresh against CLTR-001's own text (not copied from 135B's freeze or 135A's candidate list without re-checking). This is the same discipline 135C applied to 135B; 135D applies it one layer deeper — not "is this state justified by 135A/135B" but "is this state the smallest set that captures every CLTR-001-required distinction."

### 3.2 Candidate evaluation

| Candidate | Classification | Reasoning |
|---|---|---|
| `PREPARED` | Renamed → **PROPOSED** (true lifecycle state) | CLTR-001 §7.2/§7.3 uses PROPOSED; identical semantic role to the assignment's `PREPARED` (identity + evidence bindings declared, nothing durable yet). Name-only difference; retaining CLTR-001's own name is required because this document must not silently rename a frozen contract's own state identifiers (CLTR-ID-1's spirit — one canonical name per state, not two synonyms in circulation). |
| `VALIDATING` | Renamed → **CERTIFYING** (true lifecycle state) | Same reasoning — CLTR-001 §7.2 names this stage CERTIFYING. Using `VALIDATING` here would reintroduce exactly the multiple-names-for-one-concept risk CLTR-001 §5.2 item 4 forbids for identifiers, and states are themselves a form of identifier for a transition's condition. |
| `VALIDATION_FAILED` | Renamed → **FAILED_PRE_CERT** (true lifecycle state) | Same stage as CLTR-001's FAILED_PRE_CERT (failure during CERTIFYING, before CERTIFIED, no side effects). Not a separate state from FAILED_PRE_CERT — collapsing it would create two names for one condition. |
| `PROJECTED` | **Not a state — a field/attribute of CERTIFYING and CERTIFIED** | CLTR-001 §9 treats "projected state" as record content (advisory during CERTIFYING, authoritative from CERTIFIED onward), not as a spine node a transition occupies. A transition does not "enter PROJECTED" and "leave" it; every CERTIFYING-or-later record simply *carries* a projected-state field. Modeling it as a state would require an entry/exit transition with no distinguishable trigger from CERTIFYING itself — same minimality violation 135A/135B already rejected for CHECKPOINTED (§7.4 precedent). |
| `CERTIFIED` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged. |
| `CHECKPOINTED` | **Not a state — a persistence mechanism** | CLTR-001 §7.4 and §8.3 explicitly and already rule this out: checkpointing is *how* CERTIFIED (and other spine states) become crash-durable, not a distinguishable semantic condition of its own. Re-confirmed here, not merely inherited: a transition cannot be "CHECKPOINTED but not CERTIFIED" in any way that differs observably from "CERTIFYING, durably marked in-progress" — collapsing the two would violate CLTR-001 §7.4's own binding ruling, so re-introducing CHECKPOINTED as a state here would directly contradict frozen contract text, not merely be redundant. |
| `PROMOTED` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged. |
| `NOTIFICATION_PENDING` | Renamed → **NOTIFYING** (true lifecycle state) | Same stage as CLTR-001's NOTIFYING (delivery attempt in progress, outcome not yet known). Name-only difference from the assignment's candidate list; CLTR-001's name is authoritative. |
| `NOTIFICATION_ATTEMPTED` | **Not a distinct state — subsumed by NOTIFYING** | "Attempted" describes NOTIFYING's own entry condition (a delivery attempt is in progress) — introducing a separate `NOTIFICATION_ATTEMPTED` state between NOTIFYING and its two exits (NOTIFIED / NOTIFIED_UNCONFIRMED) would require a distinguishable observable condition that "attempt started but outcome still unknown" does not have beyond what NOTIFYING already means. Rejected as redundant. |
| `NOTIFIED` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged. |
| `NOTIFIED_UNCONFIRMED` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged; formalized in depth in §20 below per the assignment's specific instruction. |
| `MARKER_PERSISTED` | **Not a state — a derivative-creation event, not a spine condition** | CLTR-001 §19.1 classifies the marker as a non-authoritative derivative of NOTIFIED/NOTIFIED_UNCONFIRMED. Whether a marker has been written yet is a fact about a *derivative*, not about the transition's own spine position — two records both in state NOTIFIED (one with a marker written, one without, e.g. because the marker write itself failed per CLTR-001 §18.1's marker-failure row) occupy the *same* spine state with different derivative-completeness. Modeling marker persistence as a spine state would incorrectly promote a derivative-layer fact to authority-layer status, the exact violation CLTR-AUTH-2 forbids. |
| `RECEIPT_COMPLETE` | **Not a state — folded into NOTIFIED's own completeness, per CLTR-001 §7.4** | CLTR-001 §7.4 explicitly rules this out by name: "`receipt_complete` is not a spine state. It is a property of the NOTIFIED state." Re-confirmed here: introducing it would require a NOTIFIED → `RECEIPT_COMPLETE` transition indistinguishable in entry/exit semantics from NOTIFIED itself. |
| `RECEIPT_BEST_EFFORT_INCOMPLETE` | **Not a state — this is exactly NOTIFIED_UNCONFIRMED under a different name** | CLTR-001 §16.2 explicitly derives NOTIFIED_UNCONFIRMED from today's `completed_receipt_best_effort_incomplete` status string. Treating `RECEIPT_BEST_EFFORT_INCOMPLETE` as a second, separate state alongside NOTIFIED_UNCONFIRMED would reintroduce a two-names-one-condition ambiguity CLTR-ID-1/CLTR-ID-2's spirit forbids for identity and which this document extends to state naming. Rejected as a duplicate. |
| `TERMINAL_SUCCESS` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged. |
| `TERMINAL_PARTIAL_EXTERNAL` | Retained (true lifecycle state) | CLTR-001 §7.2/§7.3, unchanged. |
| `FAILED_BEFORE_CERTIFICATION` | Renamed → **FAILED_PRE_CERT** (true lifecycle state) | Identical semantic role; CLTR-001's own shorter name is authoritative (§5.2 item 4 forbids circulating a second alias). |
| `FAILED_AFTER_CERTIFICATION` | Renamed → **FAILED_POST_CERT** (true lifecycle state) | Same reasoning. |
| `RETRYABLE` | **Not a state — a per-state property** | CLTR-001 §4.3/§7.3 already treats retryability as a column on each state's definition, not a state itself (this restates 135A §4.3's original rejection, re-confirmed sound: making RETRYABLE a state would require every retryable state to transition *into* RETRYABLE and then somewhere else, doubling the graph without adding information — retryability is a Boolean fact *about* a state, not a state a transition passes through). |
| `QUARANTINED` | Retained (orthogonal state, not part of the main spine) | CLTR-001 §7.2/§7.3, unchanged. |
| `SUPERSEDED` | Retained (orthogonal state, not part of the main spine) | CLTR-001 §7.2/§7.3, unchanged. |

### 3.3 Final minimum state inventory

Re-derived, not copied: **12 spine states + 2 orthogonal states = 14 total**, exactly matching CLTR-001 §7.2/§7.3's frozen inventory. No candidate from the assignment's list survives evaluation as an *additional* state beyond what CLTR-001 already freezes; every apparent addition (PROJECTED, CHECKPOINTED, NOTIFICATION_ATTEMPTED, MARKER_PERSISTED, RECEIPT_COMPLETE, RECEIPT_BEST_EFFORT_INCOMPLETE, RETRYABLE) is independently re-confirmed to be either a field/property, a persistence mechanism, a derivative-creation event, or a duplicate name — never a state this document must add to CLTR-001's frozen inventory.

**Spine (12):** PROPOSED, CERTIFYING, CERTIFIED, PROMOTING, PROMOTED, NOTIFYING, NOTIFIED, NOTIFIED_UNCONFIRMED, TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_PRE_CERT, FAILED_POST_CERT.
**Orthogonal (2):** QUARANTINED, SUPERSEDED.

This is not a new derivation producing a different answer from CLTR-001 — it is the required independent re-derivation confirming CLTR-001's frozen answer is itself the minimum coherent set, closing the possibility that 135B's freeze under-scrutinized the candidate list (135C did not re-run this specific exercise; 135D is the first phase to explicitly re-evaluate all 21 named candidates one by one against the frozen contract).

---

## 4. State definition table

For every retained state (source: CLTR-001 §3.2, §7.3, §16.3, §18.1, §19–§20, cross-assembled into one table — no CLTR-001 section already tabulates every column below together).

| State | Semantic meaning | Authoritative facts known | Authoritative facts not yet known | Required evidence | Permitted derivatives | Prohibited derivatives | Canonical-state effect | External-visibility effect | Irreversible effects already completed | Terminal | Retryable | Ordinary replay | Constrained repair | Quarantine behavior | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PROPOSED** | Transition identity + evidence bindings declared; nothing durable | Declared identity, declared evidence references | Whether certification will succeed; projected state (not yet computed) | Identity + evidence-reference declarations | None (too early) | Any | None — no record exists durably | None | None | No | N/A (pre-durable; retry = resubmit) | Idempotent resubmission collapses to the same PROPOSED attempt | N/A | Eligible if evidence itself looks fabricated at declaration | No |
| **CERTIFYING** | Certification in progress: evidence extraction, view composition, sealed-snapshot check | Declared identity/evidence; in-progress durable marker | Whether sealed-snapshot/semantic checks will pass | Durable "attempt in progress" checkpoint | None externally visible | Promotion-stage derivatives (report/metadata as "final") | Evidence extraction, view composition, rendering, sealed-snapshot check occur; no irreversible effect | None | None | No | N/A (in progress) | Crash mid-CERTIFYING requires observation before deciding to retry from scratch (§22) | N/A | Eligible only post-hoc if a completed CERTIFYING is later found to have sealed corrupted evidence | No, unless repeated failure |
| **CERTIFIED** | Sealed: identity, evidence bindings, digest all fixed | Record digest; all S/R/E-role fields (§3.2) | Whether promotion/dispatch will succeed | Passed sealed-snapshot + identity + evidence checks | Immutable snapshot | Anything claiming PROMOTED/NOTIFIED-stage facts | Record digest fixed; evidence bindings immutable | None yet — last "free to abandon safely" state | Snapshot sealed | No | Yes (safe re-entry to CERTIFIED itself, not a new CERTIFYING attempt) | Re-submission of identical evidence resolves to this same CERTIFIED record | N/A — CERTIFIED is not itself repaired; a defect found here is a new record, not a mutation | Eligible if digest mismatch found later | Yes if digest mismatch found |
| **PROMOTING** | Artifact promotion + delivery dispatch in progress | CERTIFIED record's full sealed content | Whether promotion+dispatch will complete, partially complete, or fail | CERTIFIED reached; durable persistence of CERTIFIED before this begins (CLTR-001 §8.2 invariant 2) | None yet, or partial (possible external artifact visibility mid-stage) | Claims of NOTIFIED-stage completion | May produce partial irreversible external effects | Possibly Y — artifact may become visible before dispatch completes or fails | Possibly partial artifact promotion | No | Only via a **new** record (never re-entered for this record) | Never — a crash mid-PROMOTING requires observation (§22, §24), never blind replay | Observation-then-decide is the only path forward from an interrupted PROMOTING | Eligible if partial external state is ambiguous | Yes |
| **PROMOTED** | Promotion + dispatch both completed | Promoted artifact identity, promotion_id | Notification outcome (not yet attempted) | Promotion + dispatch both durably confirmed | Promoted-artifact derivatives | PROMOTING re-attempt claims | Artifact promoted; canonical pointer updated (subject to Gap B, §16) | Y — promoted artifact externally visible | Artifact promotion | No | N/A — promotion itself never retried once reached | Idempotent — re-submission collapses to this record's PROMOTED state | Marker/receipt derivative regeneration only | Eligible if promoted artifact content is later found not to match CERTIFIED digest | Yes if mismatch found |
| **NOTIFYING** | Delivery attempt in progress | PROMOTED record's evidence bindings | Delivery confirmation status | PROMOTED reached | Notification payload | Claims of NOTIFIED/NOTIFIED_UNCONFIRMED before outcome known | Delivery attempted | Y — external delivery may occur | Possibly the delivery itself (irreversible once sent) | No | Yes — from NOTIFYING only (retry the delivery attempt itself, never after this state is exited) | A repeated NOTIFYING attempt for the same PROMOTED record is the one legitimate retry case (CLTR-001 §18.1 "Notification failure" row) | N/A — this state is itself the retry target | Eligible if delivery outcome cannot be determined after repeated attempts | Only if repeated |
| **NOTIFIED** | Delivery confirmed | Delivery success, notification_id | — (fully known) | Confirmed delivery evidence | TERMINAL_SUCCESS | Any further NOTIFYING re-entry | Delivery outcome sealed | Y | Delivery | No (transitions to TERMINAL_SUCCESS) | No — terminal-for-resume | Resolves to existing NOTIFIED/TERMINAL_SUCCESS record, never re-dispatches | Marker/receipt regeneration only | Eligible if marker/receipt later contradicts this state | No, unless contradiction found |
| **NOTIFIED_UNCONFIRMED** | Delivery occurred (or believed to have occurred, §20); receipt/bookkeeping incomplete | Delivery-occurred evidence (per real promoted report, not pre-promotion trial); receipt incompleteness | Full receipt-modeling confirmation | Delivery evidence + failed/incomplete receipt-modeling attempt | Reconciled receipt (upgrade path to NOTIFIED-equivalent closure via TERMINAL_PARTIAL_EXTERNAL, never back to NOTIFYING) | Any claim that delivery must be re-attempted | Delivery believed irreversible; receipt bookkeeping incomplete | Y — underlying delivery already happened | Delivery (believed) | Terminal-ish (terminal for delivery re-attempt only) | Only receipt-modeling retry, never delivery retry | Never a delivery retry; receipt reconciliation only | Receipt reconciliation is the only constrained repair path | Eligible if reconciliation itself cannot resolve within a bound | Only if reconciliation fails repeatedly |
| **TERMINAL_SUCCESS** | Fully and confirmedly complete | Everything | Nothing outstanding | NOTIFIED reached | Any regeneration of existing derivatives (byte-identical) | Any new spine transition; ordinary completion replay | Fully sealed | Y | All prior stages' effects | Yes | No | Rejected as duplicate completion (CLTR-001 §17.2) — resolves to this same terminal record | N/A — nothing to repair | Eligible only via post-hoc integrity check (digest mismatch) | Only if quarantined |
| **TERMINAL_PARTIAL_EXTERNAL** | Fully sealed with a disclosed, permanent gap | Everything except full receipt confirmation | Whether the missing confirmation will ever be resolved | NOTIFIED_UNCONFIRMED reached and not reconciled | Same as TERMINAL_SUCCESS, with the gap disclosed | Any claim of "fully confirmed" | Fully sealed with disclosed gap | Y | All prior stages' effects | Yes | No (as a transition; receipt reconciliation is not a spine retry) | Rejected as duplicate completion, same as TERMINAL_SUCCESS | Receipt reconciliation only, and only before this terminal closure — not after | Eligible via post-hoc integrity check | Yes, always (the gap itself is disclosed, so any further ambiguity warrants review) |
| **FAILED_PRE_CERT** | Certification failed before CERTIFIED | The failure/contradiction detail | Nothing durable beyond the failed attempt | Rejected-attempt evidence | None | Any claim this transition proceeded past CERTIFYING | None — nothing durable beyond the failed attempt | N | None | Yes | Yes, freely, via a **new** record (no side effects occurred) | New PROPOSED, not a mutation of this record | N/A — no repair target | Rarely applicable; eligible if the same failure pattern recurs suspiciously | No, unless repeated |
| **FAILED_POST_CERT** | Promotion/dispatch failed after CERTIFIED | CERTIFIED evidence (still sealed and valid); the observed partial-promotion state | Whether/what partial external effect occurred | CERTIFIED record's sealed content + an explicit observation event (§22, §24) | Observation-event derivative | Any claim this record itself successfully proceeded to PROMOTED | CERTIFIED evidence remains sealed and valid; this record does not proceed further | Possibly Y, if partial promotion occurred | Possibly partial promotion | Yes-ish (terminal for this record) | Only via a **new** record, and only after the §22/§24 observation discipline | New PROPOSED referencing the same phase/task, after observing actual external state | N/A — this record is not repaired, a new one supersedes the attempt | Eligible if partial external state is ambiguous | Yes |
| **QUARANTINED** (orthogonal) | Bound evidence no longer matches digest, or a derivative drifted | The mismatch/drift details, both digests | Whether the discrepancy is benign or adversarial | Independent post-hoc integrity verification finding a mismatch | Diagnostic derivatives only | Any derivative asserting the flagged record is still trustworthy without review | Record flagged untrusted; content not deleted | Y — flagged as untrusted | Whatever occurred before flagging (unaffected — flag, not erasure) | N/A (a flag, not a spine terminus) | N/A | N/A | Human review is the only path out | Self — this *is* the quarantine state | Yes, always |
| **SUPERSEDED** (orthogonal) | A later, correcting transition record exists for the same phase/task | The superseding record's identity | Whether the superseded record's own content was itself wrong (not necessarily — supersession does not imply the prior record was invalid) | Existence of a later CERTIFIED-or-later record for the same phase/task | Annotation referencing the superseding record | Any derivative treating this record as current | Record annotated as superseded; content not deleted or rewritten | Y — annotated | Whatever occurred before supersession (unaffected) | N/A | N/A | Rejected — resolves to the superseding record (CLTR-001 §17.8) | N/A — content not repaired, only annotated | Eligible independently of supersession, on its own merits | Only if supersession itself is disputed |

---

## 5. Transition inventory

Every permitted transition, explicit — no implicit transitions. Source: CLTR-001 §5.1 (135A), §7.2–§7.3, §8.1–§8.2 (135B), cross-verified against 135C's independent re-derivation (135C §9, §11).

| # | Transition ID | Source | Target | Preconditions | Required authority | Required evidence | Invariants checked | State mutation | Derivatives created | External effects | Failure state | Retry classification | Idempotency |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `propose_transition` | (none) | PROPOSED | Identity + evidence references can be declared | Declaring agent/process (§6.2 item 31 — actor binding is a disclosed gap, §37 #6) | Declared phase/task/repository identity | CLTR-ID-1, CLTR-ID-2 (identity uniqueness) | Creates the record in-memory/pre-durable | None | None | (rejected before this) | Freely retryable — resubmission is a new T1 attempt | Idempotent by identity+evidence equality |
| T2 | `begin_certification` | PROPOSED | CERTIFYING | Identity resolved; evidence references resolvable | Same declaring authority | Durable "attempt in progress" marker written | CLTR-ORDER-1 (no checkpoint before certification is satisfied by definition — nothing is sealed yet) | Writes durable in-progress checkpoint | Checkpoint entry | None | (rolls back to no durable record if this itself fails) | Freely retryable | Idempotent — re-entering CERTIFYING for the same declared inputs is the same attempt |
| T3 | `certify` | CERTIFYING | CERTIFIED | Sealed-snapshot check, identity check, evidence validation all pass | Certification logic (deterministic, no I/O beyond bound evidence) | Passing evidence extraction, view composition, rendering, sealed-snapshot check | CLTR-AUTH-1, CLTR-DERIVE-1, CLTR-DERIVE-2, CLTR-EVID-1 | Record digest fixed; evidence bindings sealed immutable | Immutable snapshot | None (still no external side effect) | FAILED_PRE_CERT | Freely retryable via a new T1/T2 attempt (this record is not mutated) | N/A — certification is not repeated for an already-CERTIFIED record |
| T4 | `certification_fail` | CERTIFYING | FAILED_PRE_CERT | Sealed-snapshot/semantic/rendering check fails | N/A | The failure/contradiction detail | N/A (a rejection, not an invariant-checked success path) | None durable beyond the failed attempt | Rejected-attempt evidence | None | (terminal) | Freely retryable via new T1 | N/A |
| T5 | `begin_promotion` | CERTIFIED | PROMOTING | CERTIFIED durably persisted first (CLTR-ORDER-2) | CERTIFIED record's own sealed authority | Durably persisted CERTIFIED state | CLTR-ORDER-2, CLTR-ORDER-4 | Begins promotion+dispatch | None yet | Possible partial artifact visibility | (see T7) | Not retryable from within this record once entered (only via new record) | Not idempotent within one record — a second PROMOTING for the same CERTIFIED record must never be initiated (guarded by T3→T5 being consumed once) |
| T6 | `promote_succeed` | PROMOTING | PROMOTED | Promotion + dispatch both complete | Sealed CERTIFIED evidence | Confirmed promotion + dispatch | CLTR-ORDER-3, CLTR-PERSIST-1 | Artifact promoted; canonical pointer updated | Promoted-artifact derivatives | Y — promoted artifact visible | N/A | N/A — never retried once reached | Idempotent — re-submission resolves to this PROMOTED record |
| T7 | `promote_fail` | PROMOTING | FAILED_POST_CERT | Promotion or dispatch fails | N/A | Observed partial-promotion state | CLTR-RETRY-3 (observation before any further decision) | Record reaches FAILED_POST_CERT; CERTIFIED evidence remains sealed | Observation-event record | Possibly Y if partial promotion occurred | (terminal-ish) | Only via a new record, after §22/§24 observation | N/A |
| T8 | `begin_notification` | PROMOTED | NOTIFYING | PROMOTED reached | PFN-001's existing delivery mechanism | Promoted canonical evidence bindings | CLTR-NOTIFY-1 | Delivery attempt begins | Notification payload | Y — external delivery may occur | N/A | Retryable (T8 may be re-entered — see T11) | Not idempotent in the sense of re-dispatching if already NOTIFIED/NOTIFIED_UNCONFIRMED (guarded by CLTR-NOTIFY-2) |
| T9 | `notify_confirm` | NOTIFYING | NOTIFIED | Delivery confirmed | Real, promoted delivery result (never a pre-promotion trial) | Confirmed delivery evidence | CLTR-RECEIPT-1 | Delivery outcome sealed | Marker (derivative), receipt (E-role) | Y | N/A | No — terminal-for-resume | Idempotent — resolves to this NOTIFIED record |
| T10 | `notify_unconfirmed` | NOTIFYING | NOTIFIED_UNCONFIRMED | Delivery occurred (or believed to) but receipt modeling cannot confirm it | Same as T9, minus confirmation | Delivery-occurred evidence + failed receipt-modeling attempt | CLTR-RETRY-1 (this is the state CLTR-RETRY-1 exists to make resume-terminal) | Delivery believed irreversible; receipt incomplete | Marker (derivative, best-effort) | Y | N/A | Only receipt-modeling retry (T12) | Not a delivery retry target |
| T11 | `notify_retry` | NOTIFYING | NOTIFYING | A prior NOTIFYING attempt failed outright (distinct from T10's "occurred but unconfirmed" case) | Same as T8 | Same as T8 | CLTR-NOTIFY-2 (retry only from NOTIFYING) | New delivery attempt | New notification_id instance | Y | (loops to T9/T10/T7-equivalent) | Yes, retry classification: notification-failure retry | Guarded — must not be entered from NOTIFIED/NOTIFIED_UNCONFIRMED |
| T12 | `reconcile_receipt` | NOTIFIED_UNCONFIRMED | NOTIFIED_UNCONFIRMED (retry) or → T13 | Receipt-modeling reconciliation attempted | Independent confirmation signal | Reconciliation evidence | CLTR-RECEIPT-1 | Receipt bookkeeping updated, delivery claim unchanged | Reconciled receipt | N | N/A | Constrained repair — receipt-modeling only | Idempotent per reconciliation attempt |
| T13 | `close_success` | NOTIFIED | TERMINAL_SUCCESS | NOTIFIED reached | Record's own sealed state | N/A | CLTR-SAFE-3 | Fully sealed | N/A | Y | N/A | No | Idempotent — resolves to the same terminal record |
| T14 | `close_partial` | NOTIFIED_UNCONFIRMED | TERMINAL_PARTIAL_EXTERNAL | NOTIFIED_UNCONFIRMED reached and not reconciled to NOTIFIED-equivalent closure | Record's own sealed state + disclosed gap | N/A | CLTR-RETRY-1 | Fully sealed with disclosed gap | N/A | Y | N/A | No (as a transition) | Idempotent |
| T15 | `quarantine` (orthogonal) | Any CERTIFIED-or-later state | QUARANTINED | Independent post-hoc integrity verification finds a digest/derivative mismatch | Independent verifier, not the transaction itself | Mismatch details, both digests | CLTR-PERSIST-2 (violation trigger) | Record flagged untrusted; content unchanged | Diagnostic annotation | Y — flagged | N/A (orthogonal, does not consume the spine state) | N/A | N/A |
| T16 | `supersede` (orthogonal) | Any state | SUPERSEDED | A later CERTIFIED-or-later record exists for the same phase/task | The later record's own successful certification | Reference to the superseding record's identity | CLTR-STATE-3 (no backward mutation — this is annotation, not reversal) | Record annotated as superseded; content unchanged | Annotation | Y — annotated | N/A (orthogonal) | N/A | N/A |

### 5.1 No implicit transitions

Every state change in §4's table is the result of exactly one numbered transition above. No state in §4 has an entry/exit condition that is not traceable to a T-numbered row. This is the required closure property: a future implementation phase (135F+) may add mechanism detail to any T-row, but may not introduce a transition this inventory does not already name (a new transition would itself require a 135D-successor amendment, per §1's authority hierarchy — CLTR-001 is silent on adding new spine transitions outside a governed contract-amendment phase).

---

## 6. Forbidden transition inventory

Explicitly prohibited, per the assignment's minimum list plus this phase's own closure check (every §4 "Forbidden next" cell is accounted for by a named prohibition below):

| # | Forbidden transition | Why forbidden | Enforcing invariant |
|---|---|---|---|
| F1 | PROPOSED → PROMOTED (direct) | Skips certification and its irreversibility gate entirely; would let an unvalidated, unsealed transition produce external effects | CLTR-ORDER-4, CLTR-STATE-4 |
| F2 | PROPOSED → NOTIFIED (direct) | Same reasoning, additionally skips promotion | CLTR-ORDER-3, CLTR-ORDER-4, CLTR-STATE-4 |
| F3 | FAILED_PRE_CERT (i.e. VALIDATION_FAILED) → CERTIFIED without new validated authority | A failed certification attempt cannot become CERTIFIED by any path other than a **new** PROPOSED→CERTIFYING→CERTIFIED sequence with newly validated inputs; mutating a FAILED_PRE_CERT record into CERTIFIED would erase the forensic fact that certification failed once | CLTR-STATE-3, CLTR-PERSIST-2 |
| F4 | CERTIFIED → NOTIFIED (direct, without checkpoint and promotion) | Skips PROMOTING entirely, meaning delivery could occur for an artifact that was never actually promoted/published | CLTR-ORDER-2, CLTR-ORDER-3 |
| F5 | PROMOTED → uncertified state (any backward transition to CERTIFYING or earlier) | Once promoted, the transition's irreversible external effect has occurred; there is no uncertifying it | CLTR-STATE-3 |
| F6 | NOTIFIED → ordinary re-dispatch (re-entering NOTIFYING) | NOTIFIED means delivery is confirmed; a second dispatch would violate PFN-001's exactly-once delivery guarantee | CLTR-NOTIFY-2, PFN-001 §8 |
| F7 | TERMINAL_SUCCESS → ordinary replay (any new spine transition, or a second transition claiming to complete the same phase/task) | Terminal states admit no further spine transition; a second "completion" is a duplicate, not a resume | CLTR-RETRY-2, CLTR-STATE-3 |
| F8 | SUPERSEDED → active (returning a superseded record to current/authoritative status) | Supersession is a one-way annotation; reactivating a superseded record would let two records claim current authority for the same phase/task simultaneously | CLTR-STATE-3, CLTR-ID-2 |
| F9 | QUARANTINED → TERMINAL_SUCCESS without explicit recovery authority | A quarantined record's integrity is in question; only human review (never an automatic re-derivation) may clear it | §18.1 QUARANTINED row, "Human review: Yes, always" |
| F10 | Marker or receipt creation before required prior stages (i.e., before NOTIFIED or NOTIFIED_UNCONFIRMED is reached) | A marker/receipt asserting a terminal-ish outcome for a transition that has not reached that outcome would misrepresent terminality — CLTR-001 §8.2 invariant 4 and §19.2 item 4 | CLTR-MARKER-1, CLTR-001 §8.2 invariant 4 |
| F11 | Derivative generation from an uncertified authority where certification is required | Any derivative whose CLTR-001 §12.1 row requires a CERTIFIED-or-later source (e.g., the canonical phase report, promoted metadata) must never be generated from a PROPOSED/CERTIFYING record | CLTR-DERIVE-1, CLTR-AUTH-2 |
| F12 | Any spine state → PROMOTING without having passed through CERTIFIED for *this* record | Restates F1/F4 at the transition-table level: PROMOTING's only legal predecessor is CERTIFIED (T5) | CLTR-ORDER-2, CLTR-STATE-4 |
| F13 | FAILED_POST_CERT → PROMOTED (retrying PROMOTING in place for the same record) | A record that failed during PROMOTING is never resumed by re-running PROMOTING on itself — the observation discipline (§22, §24) requires a **new** record | CLTR-RETRY-3 |
| F14 | Any terminal or terminal-ish state (TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_PRE_CERT) → any spine state other than the orthogonal QUARANTINED/SUPERSEDED | Terminality means no further spine progress; only the two orthogonal flags may still attach | CLTR-STATE-3, §4's "Permitted next" columns |

No forbidden transition above lacks an enforcing invariant; no §4 "Forbidden next" cell lacks a corresponding F-numbered entry (cross-checked exhaustively during authoring — every state's forbidden-next set reduces to one or more of F1–F14 plus the general "no backward spine transition" rule, CLTR-STATE-3, which subsumes any pair not explicitly named above).

---

## 7. Certification boundary

### 7.1 What must be bound before certification (i.e., by CERTIFYING → CERTIFIED, T3)

Per CLTR-001 §6.2, §8.1 steps 1–7, and §9.2: `transition_id`, `phase_id`, `task_id`, `repository_identity`, `branch_identity`, `source_revision`, declared commit ownership (verified into verified/contaminated/unverifiable per §10.4), test/governance evidence references, `prior_state`, `projected_state` (computed, about to seal), report/metadata identity bindings sufficient for §12.1's derivatives, and the record digest itself (§15.1).

### 7.2 What may remain observational (post-certification, still V-role)

Repository cleanliness, pushed state, `origin/main..HEAD` (CLTR-001 §23.1) remain live, re-measurable observations even after CERTIFIED — they are bound as historical, point-in-time facts *about* the transition, never frozen as perpetually current. `final_revision` may remain explicitly **provisional** at CERTIFIED (§7.4 below).

### 7.3 Which identities must be final at certification

`transition_id`, `phase_id`, `task_id`, `repository_identity`, `branch_identity`, `source_revision`, `report_id`, `metadata_id`, `snapshot_id` — all bound and immutable from CERTIFIED onward (CLTR-001 §5.1, §5.2 items 1–2, "no truncation," "exact identity equality"). `promotion_id`, `notification_id`, `marker_id`, `receipt_id` are **not** yet final at CERTIFIED — they do not exist until their respective later stages (T5+, T8+, post-T9/T10, post-T9/T10 respectively).

### 7.4 Which evidence must be complete

Test evidence references, governance evidence references, commit-ownership three-outcome classification (§10.4) — all must be resolvable (even if the resolution is `unverifiable`, which is itself a complete, distinct outcome, never an absence) before T3 (`certify`) may succeed. Absence of a *resolution* (not merely an unfavorable resolution) blocks T3 and routes to T4 (`certification_fail` → FAILED_PRE_CERT).

### 7.5 Core-bound vs. terminal-extension-bound final revision

Restating and formalizing CLTR-001 §23.4's staged-binding resolution as a state-machine rule: `final_revision` is **core-bound** (known and sealed at CERTIFIED) only when no further commit is required for this transition's own artifacts to be considered final. Where a finalization commit is still required (the common case for this very repository's own governed phases, per 135C §26's first-hand corroboration), `final_revision` is **terminal-extension-bound**: CERTIFIED seals an explicit provisional marker, and a distinct, non-mutating **terminal verification event** (not a T-numbered spine transition — an append to the record's own event history, per CLTR-001 §14.1 item 1) later resolves it once the finalization commit is made and independently confirmed via live `git rev-parse`. This event never reopens CERTIFIED, never changes the record's digest, and is not itself a precondition for T9/T10/T13/T14 (notification and terminal closure do not wait on final_revision resolution, since final_revision concerns the *transition's own* finalization commit, a concern orthogonal to whether delivery succeeded — independently re-confirmed as non-circular in 135C §37).

### 7.6 What becomes immutable at certification

The record's digest, all S/R/E-role fields bound at CERTIFYING (§7.1), and the CERTIFIED-state evidence bindings that seed the immutable snapshot (CLTR-001 §12.1 "Immutable snapshot" row). None of this may be recomputed by any later derivative in a way that could disagree with the sealed value (CLTR-001 §3.2's completed/certified-state rows).

### 7.7 What may still fail after certification

Promotion (T5→T7), notification (T8→T10 with incomplete confirmation), receipt reconciliation (T12), and final-revision resolution (§7.5's terminal extension, if it exceeds its bound — CLTR-001 §23.4 item 4, still deferred as a quantitative parameter, §37 #5). None of these failures reopen or invalidate the CERTIFIED record's own sealed content (CLTR-001 §7.3 CERTIFIED row: "record digest fixed; evidence bindings immutable" — this holds regardless of what happens afterward).

### 7.8 What may never be re-derived afterward

Identity, evidence bindings, and the record digest (§7.6) — CERTIFIED content is sealed for the life of the record. A defect discovered later routes to QUARANTINED (T15) for human review, never to silent in-place recomputation (CLTR-PERSIST-2).

### 7.9 Consequences of certification success and failure

**Success (T3):** the transition becomes eligible for promotion; irreversible external effects become possible for the first time (T5 onward); the record's authority over completion-state facts becomes sole from this point forward (CLTR-001 §3.2's S-from-CERTIFIED rows).
**Failure (T4):** FAILED_PRE_CERT — no side effects occurred, nothing durable beyond the rejected attempt persists as a claim, freely retryable via a wholly new PROPOSED (T1). The distinction between T3 success and T4 failure is exactly what makes the FAILED_PRE_CERT/FAILED_POST_CERT split load-bearing (§3.2 of this document, and re-confirmed here): collapsing them would erase the "were there any side effects to account for" fact recovery logic depends on (§22).

---

## 8. Irreversibility model

### 8.1 Classification scheme

Each lifecycle operation is classified along the eight categories the assignment specifies. An operation may carry more than one classification (e.g., "notification dispatch" is both externally visible and best-effort external).

| Operation | Reversible | Retryable | Idempotent | Externally visible | Irreversible | Best-effort external | Derivative-only | Repair-only |
|---|---|---|---|---|---|---|---|---|
| Projected-state construction (T2/T3-adjacent, CLTR-001 §9) | Yes (advisory until CERTIFIED) | Yes (recomputed freely pre-CERTIFIED) | Yes (deterministic pure function) | No | No | No | No | No |
| Semantic validation (part of T3) | Yes if it fails (→T4) | Yes (new attempt) | Yes | No | No | No | No | No |
| Certification (T3) | No — once sealed, CERTIFIED content never reverses | No (a new record substitutes, this one is not retried) | Yes (idempotent re-entry to the same CERTIFIED record for identical inputs) | No | **Yes** — the sealing act itself is the first irreversible internal commitment, though not yet externally visible | No | No | No |
| Checkpoint creation (durability mechanism for CERTIFYING/CERTIFIED, CLTR-001 §7.4/§8.3) | N/A — a mechanism, not a stage | N/A | Yes | No | No (it is the *means* of making certification durable, not itself a new irreversible fact) | No | No | No |
| Canonical promotion (T5→T6) | No | No (new record only) | Yes (idempotent once PROMOTED) | Possibly (partial promotion may be visible before dispatch completes) | **Yes** | No | No | No |
| Latest-pointer switch (`latest.md`/`latest.json` update, subject to Gap B) | No, in principle (should be atomic per CLTR-001 §13) | N/A | Should be (per §13.3, not yet guaranteed by current implementation, §16 below) | Yes | Yes (once switched, the prior pointer target is superseded) | No | No | No |
| Notification dispatch (T8→T9/T10) | No | Yes, but **only from NOTIFYING** (T11), never after | Governed by PFN-001's exactly-once guarantee — must not be re-dispatched once confirmed | Yes | **Yes** (once actually sent) | **Yes** — delivery outcome may be only best-effort-confirmable (NOTIFIED_UNCONFIRMED) | No | No |
| Marker persistence (post-T9/T10) | Yes — freely regenerable | Yes | Yes (regeneration is idempotent) | No (internal cache/derivative) | No | No | **Yes** | No |
| Receipt persistence (E-role, post-T9/T10) | No — once written, immutable event | Only via reconciliation (T12), never re-creation | Reconciliation itself should be idempotent per attempt | No (internal evidence) | Yes, as an immutable event record (not rewritten) | No (receipts reflect reality, not attempt outcomes) | No (E-role, evidentiary, not "just a derivative") | Yes — reconciliation (T12) is repair-only, never re-triggering delivery |
| Final-state observation binding (§7.5's terminal extension; repository cleanliness/pushed-state/ahead-count, CLTR-001 §23) | N/A — each observation is a fresh, point-in-time fact, not something to "reverse" | N/A (re-measure, don't retry) | Yes — re-measurement is idempotent as a *measurement*, though its *result* may differ each time | No (internal governance fact, unless surfaced in a report) | No (the *binding* of a past measurement is permanent as history, but is never claimed as still-currently-true) | No | Yes (a V-role observation is itself a derivative fact about live state) | No |

### 8.2 Using the classification to verify transition ordering

Cross-checking §8.1 against §5's transition inventory: every operation classified **irreversible** in §8.1 (certification's sealing act, canonical promotion, notification dispatch, latest-pointer switch) occurs only at or after T3 (`certify`), consistent with CLTR-ORDER-4 ("no irreversible stage precedes semantic certification"). No operation classified irreversible occurs during PROPOSED or CERTIFYING's pre-certification steps (T1, T2) — confirming F1/F2/F12 (§6) are consistent with this classification, not merely asserted alongside it. No operation classified **repair-only** (receipt reconciliation) is capable of re-triggering an operation classified **irreversible** (notification dispatch) — this is the structural content of CLTR-NOTIFY-2 and is independently re-confirmed here at the operation-classification layer, not only at the state-transition layer (§6, F6).

---

## 9. Cross-representation model

For each representation CLTR-001 governs (§12.1, §3.2, §19–§23), the following table states its lifecycle-state existence range, source authority, identity/digest binding, mutability, role, and tolerance for absence/inconsistency.

| Representation | Exists in states | Source authority | Identity binding | Digest binding | Mutable/immutable | Role | Absence allowed | Inconsistency Blocking? |
|---|---|---|---|---|---|---|---|---|
| Canonical transition record itself | CERTIFYING onward (in-progress before; sealed from CERTIFIED) | S/R/E per §3.2, the record IS the authority | `transition_id` (self) | Self-digest (§15.1) | Immutable from CERTIFIED | Authoritative | No, once CERTIFYING begins | N/A (this is the anchor everything else is checked against) |
| Canonical phase report | CERTIFIED onward | Derived (D), per CLTR-001 §12.1 | `report_id` | Report content digest bound in record | Immutable once bound | Derivative | No, once CERTIFIED (required by PFR-001) | Yes — CLTR-DERIVE-2 |
| Completion metadata | CERTIFIED onward | Derived (D) | `metadata_id` | Metadata digest bound in record | Immutable once bound | Derivative | No, once CERTIFIED | Yes |
| Architecture Status | Any state, regenerable at will | Derived (D), never authoritative (§4.2 item 3) | Reference to most recent record's `transition_id` per phase | Not separately digested | Mutable (regenerable) | Derivative/projection | Yes — absence just means "not yet regenerated," never treated as a lifecycle fact | Yes if it disagrees with the record's projected/certified state — CLTR-STATE-1/2 |
| Immutable snapshot | CERTIFIED onward | Evidence (E) | `snapshot_id` | Snapshot digest bound in record | Immutable | Authoritative evidence for CERTIFIED content | No, once CERTIFIED | Yes — must never diverge from the record it was sealed with |
| Checkpoint | PROPOSED/CERTIFYING (transient; persistence mechanism, not a spine node) | Evidence (E), persistence-only | `checkpoint_id` | N/A | Mutable until CERTIFIED, then superseded by the sealed record | Persistence mechanism | Yes, once CERTIFIED (the record itself supersedes it) | Yes if it disagrees with the eventual CERTIFIED record — must be a reconstructible prefix |
| Promoted report | PROMOTED onward | Derived (D), same digests as CERTIFIED artifacts | `report_id` carried through | Same as canonical phase report | Immutable content, mutable pointer target | Derivative, externally visible | No, once PROMOTED | Yes — must reflect exactly one CERTIFIED record, never a mix (CLTR-PERSIST-1) |
| Promoted metadata | PROMOTED onward | Derived (D) | `metadata_id` carried through | Same pattern | Same pattern | Derivative, externally visible | No, once PROMOTED | Yes — same atomic-visibility requirement |
| Mutable latest pointer (`latest.md`/`latest.json` or future equivalent) | PROMOTED onward | Derived (D), never authoritative (§4.2 item 9) | Points at `report_id`/`metadata_id` of the current generation | N/A (a pointer, not digested itself) | Mutable | Derivative pointer | Yes — recoverable from immutable history if missing (CLTR-PERSIST-3) | Yes if stale/mixed-generation — CLTR-PERSIST-1 |
| Notification payload | NOTIFYING | Reference (R) to promoted evidence | `notification_id` | Bound to record's evidence digest at PROMOTED | Immutable per dispatch attempt | External projection | N/A (only exists during/after an actual dispatch attempt) | Yes if it does not trace to exactly one PROMOTED record |
| Notification result | NOTIFYING onward | Evidence (E) once recorded | `notification_id` | N/A | Immutable, append-only across retries | Evidence | No, once a dispatch attempt occurs | Yes if it contradicts the record's NOTIFIED/NOTIFIED_UNCONFIRMED state |
| Completion marker | NOTIFIED/NOTIFIED_UNCONFIRMED onward | Derived (D), retired as authority (§19) | `marker_id` bound to `transition_id` | Reference to record digest, for staleness detection | Mutable (regenerable cache) | Replay accelerator, compatibility signal | Yes, always — missing marker never blocks correctness (§19.2 item 6) | No if merely missing/stale (regenerate); Yes if fabricated (§19.2 item 8) |
| Finalization receipt | NOTIFIED/NOTIFIED_UNCONFIRMED onward | Evidence (E) | `receipt_id` bound to `transition_id` | N/A — receipts are their own immutable event class | Immutable | Evidence, own narrow domain (delivery outcome) | No, once dispatch is attempted | Yes if it claims success without matching record state (CLTR-RECEIPT-1) |
| Git attribution view | Any state, computed from CERTIFYING-time verification | Derived (D), from verified commit-ownership fields | `transition_id` | N/A | Regenerable | Derivative presentation | Yes, regenerable at will | Yes if it disagrees with the three-outcome classification (§10.4) |
| Repository transition view | Any state, computed from bound revisions | Derived (D) | `transition_id` | N/A | Regenerable | Derivative presentation | Yes, regenerable at will | Yes if it diverges from the two bound revisions |
| Terminal repository-state observations (cleanliness, pushed, ahead-count) | Bound at CERTIFYING; possibly re-measured at a terminal-extension point (§7.5) | Verification-only (V) | Bound to `transition_id` as a point-in-time fact | N/A | Immutable as historical fact; never re-treated as current | Verification observation | No, at least one binding is required before CERTIFIED for cleanliness/pushed-state gating | Yes if a stale V-role value is treated as still current without re-measurement |

---

## 10. Representation-state matrix

Implementation-independent, testable matrix: for each lifecycle state, which representations must not exist, may exist, must exist, must be immutable, may be repaired, may be externally visible, are authoritative, and are derivative only.

| State | Must NOT exist | May exist | Must exist | Must be immutable | May be repaired | May be externally visible | Authoritative | Derivative only |
|---|---|---|---|---|---|---|---|---|
| PROPOSED | Report, metadata, snapshot, promotion/notification/marker/receipt artifacts, latest-pointer update | Declared identity/evidence (pre-durable) | Identity + evidence declarations | Nothing yet | N/A | Nothing | None yet (record itself not yet durable) | N/A |
| CERTIFYING | Snapshot, promotion, notification, marker, receipt | Checkpoint (in-progress marker) | Durable in-progress checkpoint | Nothing yet | Checkpoint (freely, pre-seal) | Nothing | None yet | N/A |
| CERTIFIED | Promotion, notification, marker, receipt | — | Record digest, sealed evidence bindings, immutable snapshot | Record digest, evidence bindings, snapshot | No (repair = new record) | No (last "free to abandon" state) | Record itself (S/R/E fields) | Snapshot |
| PROMOTING | Notification, marker, receipt | Partial promoted-artifact visibility | (in-progress; no new required artifact beyond CERTIFIED's) | CERTIFIED's own sealed content (unaffected) | No | Possibly (partial) | CERTIFIED content (unchanged) | N/A |
| PROMOTED | Notification, marker, receipt | — | Promoted report, promoted metadata, updated latest pointer | Promoted report/metadata content | No (repair = new record) | Yes | Promotion fact itself (E+D) | Promoted report/metadata (content still sourced from CERTIFIED) |
| NOTIFYING | Marker, receipt (not yet — F10) | Notification payload | Dispatch attempt in progress | N/A (in-progress) | No | Yes | N/A (outcome pending) | Notification payload |
| NOTIFIED | — | — | Marker, receipt, notification result (confirmed) | Notification result, receipt | Marker only (regenerable) | Yes | Delivery outcome (E) | Marker |
| NOTIFIED_UNCONFIRMED | — | Marker (best-effort) | Delivery-occurred evidence, incomplete receipt | Delivery evidence | Receipt (reconciliation only) | Yes | Delivery-occurred fact (E) | Marker |
| TERMINAL_SUCCESS | — | — | Everything from NOTIFIED, sealed | Everything | No | Yes | Full record | All derivatives |
| TERMINAL_PARTIAL_EXTERNAL | — | — | Everything from NOTIFIED_UNCONFIRMED, sealed with disclosed gap | Everything except the unresolved gap itself | No (gap is permanent once closed) | Yes | Full record, with disclosed incompleteness | All derivatives |
| FAILED_PRE_CERT | Snapshot, promotion, notification, marker, receipt | Rejected-attempt evidence | Failure/contradiction detail | The rejection record itself | N/A (repair = new attempt) | No | None (nothing durable beyond the rejection) | N/A |
| FAILED_POST_CERT | Notification, marker, receipt (unless partially created before failure — flagged for observation) | Partial promotion evidence | CERTIFIED content (still sealed), observation event | CERTIFIED content | No (repair = new record) | Possibly (if partial promotion occurred) | CERTIFIED content (unchanged) | N/A |
| QUARANTINED (orthogonal) | N/A — orthogonal to spine content | Diagnostic annotation | Mismatch details, both digests | The flagged record's original content (unchanged, flag only) | Only via human review | Yes — flagged as untrusted | N/A (trust suspended pending review) | Diagnostic annotation |
| SUPERSEDED (orthogonal) | N/A — orthogonal | Reference to superseding record | Supersession annotation | Original content (unchanged) | No (annotation only) | Yes — annotated | The *superseding* record, not this one | Annotation |

This matrix is implementation-independent (no field name, storage mechanism, or wire format is referenced) and testable (every cell names an inspectable presence/absence/mutability condition a future verification phase can check against an actual constructed record).

---

## 11. Invariant architecture

CLTR-001's 33 invariants (§26.1) are re-derived here into evaluable conditions — a formal predicate over record content and state, not a restatement of contract prose. Closing 135C finding #7 (three of §8.2's seven ordering requirements lacked a numbered entry), this section also mints **CLTR-ORDER-5, -6, -7** as the missing entries, explicitly classified as a **derived clarification of CLTR-001** (not a new requirement — the substantive text already existed in CLTR-001 §8.2 items 4, 6, 7; only the numbered-invariant-inventory representation was incomplete).

| ID | Category | Normative statement | States | Representations | Evaluation inputs | Success condition | Failure condition | Severity | Failure consequence | Retry consequence | Quarantine consequence | Compatibility handling | Future test strategy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CLTR-ID-1 | Identity | All representations of a transition share exactly one `transition_id` | All | Every representation in §9 | `transition_id` field of record vs. each representation's own bound `transition_id` | `∀ r ∈ representations(record): r.transition_id == record.transition_id` | Any representation with a differing/absent `transition_id` | Blocking | Reject divergent representation | N/A | Candidate | Legacy artifacts predating records are exempt (§29) | Property-based check: construct a record, generate every derivative, assert equality |
| CLTR-ID-2 | Identity | All representations of a phase's most recent transition share exactly one `phase_id` | All | Same | `phase_id` across representations of the *latest* record per phase | Equality holds | Any mismatch | Blocking | Reject | N/A | Candidate | Same | Same, scoped to "most recent record per phase" |
| CLTR-AUTH-1 | Authority | A lifecycle fact has exactly one authoritative source within a transition | All | All | §3.2's authority-role table | Exactly one S/D-role source resolves the fact | Two sources both claim S-role for the same fact and disagree | Blocking | Design defect — must be resolved pre-implementation | N/A | N/A (design-time) | Legacy cooperating-authority pattern is `adapter`-classified, not `conformant` | Static review of every derivation function's inputs |
| CLTR-AUTH-2 | Authority | No derivative independently reconstructs a fact the record does not carry | All | All derivatives | Derivation function's input set vs. record's own field set | Every derivative field traces to a record field or bound evidence reference | A derivative field has no traceable record-level source | Blocking | Fix the derivation, discard the inferred value | N/A | N/A | N/A | Static analysis of derivation functions; the Architecture Status title-extraction bug (135C §25.2) is the canonical negative example |
| CLTR-STATE-1 | State | A completed phase never appears in any derivative's "active" classification | Any state ≥ TERMINAL_SUCCESS/TERMINAL_PARTIAL_EXTERNAL for that phase | Architecture Status, any "active"/"in progress" view | Record's own terminal-or-not status vs. derivative's active/inactive classification | Terminal record ⇒ derivative shows inactive | Terminal record, derivative shows active | Blocking | Regenerate the derivative from the record's projected state | N/A | Candidate if repeated | N/A | Regression test fixing the exact 134E.10-class defect |
| CLTR-STATE-2 | State | A planned successor is never classified active until its own record reaches CERTIFIED or later | Any | Architecture Status "Planned"/"In Progress" | Successor's own record state (if any) | Successor shown active only if its own record ≥ CERTIFIED | Successor shown active with no CERTIFIED-or-later record of its own | Blocking | Regenerate | N/A | Candidate | N/A | Test: name a successor, assert it never appears "active" until proposed |
| CLTR-STATE-3 | State | No state transitions backward along the spine | All | Record itself | §5's transition table's source/target pairs over time | Every observed transition matches a T-row in §5 | Any transition matches no T-row, or reverses a §4 "Forbidden next" | Blocking | Reject the transition attempt | Candidate if already persisted | N/A | Legacy status strings are read-only historical facts, never replayed as spine transitions | Exhaustive transition-table conformance test (§34 reachability) |
| CLTR-STATE-4 | State | No state skips a required predecessor | All | Record itself | §5's precondition column | Every transition's precondition is satisfied by the record's actual prior state | A transition fires without its precondition state having been reached | Blocking | Reject | Candidate if already persisted | N/A | Same | Same |
| CLTR-ORDER-1 | Ordering | No checkpoint before certification | CERTIFYING | Checkpoint | Checkpoint's declared spine position vs. actual passed checks | Checkpoint marked CERTIFIED only after T3 succeeds | Checkpoint claims CERTIFIED before T3 | Blocking | Reject; certification stages must complete first | N/A | N/A | N/A | Unit test on the certify/checkpoint call ordering |
| CLTR-ORDER-2 | Ordering | No promotion before checkpoint | PROMOTING | Checkpoint, record | CERTIFIED durably persisted flag | T5 fires only if CERTIFIED is durably persisted | T5 fires against an in-memory-only CERTIFIED | Blocking | Reject | N/A | N/A | N/A | Crash-injection test between T3 and T5 |
| CLTR-ORDER-3 | Ordering | No terminal notification before promotion | NOTIFYING | Record | PROMOTED reached flag | T8 fires only from PROMOTED | T8 fires from any earlier state | Blocking | Reject | N/A | N/A | N/A | Transition-table conformance test |
| CLTR-ORDER-4 | Ordering | No irreversible stage precedes semantic certification | PROMOTING onward | Record, §8.1 classification | §8.1's "irreversible" column vs. state reached | No operation classified irreversible in §8.1 occurs before T3 | An irreversible operation (promotion, dispatch) occurs pre-CERTIFIED | Blocking | Reject | N/A | N/A | N/A | Cross-check §8.1 against §5, as performed in §8.2 |
| **CLTR-ORDER-5** *(new, derived clarification)* | Ordering | No post-certification mutable read may redefine the transition (CLTR-001 §8.2 item 6) | CERTIFIED onward | Every derivative | Derivative's data source vs. record's sealed fields | Every post-CERTIFIED derivative reads only the sealed record, never re-scans mutable repository/PROJECT_STATUS.md state | A derivative re-derives a fact from mutable state instead of the sealed record | Blocking | Regenerate the derivative from the record | N/A | Candidate if the derivative was already externally delivered | N/A | The Architecture Status title-extraction bug (135C §25.2) is the canonical negative test case |
| **CLTR-ORDER-6** *(new, derived clarification)* | Ordering | No marker before required delivery classification (CLTR-001 §8.2 item 4) | NOTIFIED/NOTIFIED_UNCONFIRMED | Marker | Marker's claimed transition state vs. record's actual state at marker-write time | Marker written only once record reaches NOTIFIED or NOTIFIED_UNCONFIRMED | Marker written from PROPOSED/CERTIFYING/CERTIFIED/PROMOTING/PROMOTED/NOTIFYING | Blocking | Reject the marker as fabricated (§19.2 item 8) | N/A | Candidate | N/A | Same as F10 (§6) |
| **CLTR-ORDER-7** *(new, derived clarification)* | Ordering | No receipt may claim completion before actual stage completion (CLTR-001 §8.2 item 5) | NOTIFIED/NOTIFIED_UNCONFIRMED | Receipt | Receipt's claimed outcome vs. record's actually-reached spine state at modeling time | Receipt's claimed stages ⊆ record's actually-reached stages | Receipt claims a stage the record has not reached | Blocking | Reject the receipt as optimistic/fabricated | N/A | Candidate | N/A | Same discipline as CLTR-RECEIPT-1, evaluated at ordering time specifically |
| CLTR-DERIVE-1 | Derivation | Every derivative is a pure function of the record plus referenced evidence | All | All derivatives | Derivation function's declared inputs | Inputs ⊆ {record fields, bound evidence} | Any other input (I/O, randomness, sibling-derivative inspection) | Blocking | Derivation bug — fix, don't accept | N/A | N/A | N/A | Static analysis + determinism test (§34) |
| CLTR-DERIVE-2 | Derivation | Regeneration of any derivative from the same sealed record is byte-identical | CERTIFIED onward | All derivatives | Two independent regenerations of the same derivative from the same record | Byte-for-byte equality | Any divergence | Blocking | Derivation bug | N/A | N/A | N/A | Regenerate-and-diff test |
| CLTR-COMMIT-1 | Commit ownership | Declared phase commits equal the commits any derivative report claims as phase-owned | CERTIFIED onward | Git attribution view, report | Record's declared commit set vs. derivative's claimed set | Set equality | Derivative claims a commit the record does not bind, or omits one the record binds | Blocking | Reject the divergent derivative claim | N/A | Candidate | N/A | Set-equality test |
| CLTR-COMMIT-2 | Commit ownership | Every declared commit resolves to exactly one of verified/contaminated/unverifiable | CERTIFYING | Record | §10.4's three-outcome definitions applied to each declared hash | Every hash classified into exactly one outcome | A hash left unclassified, or classified into more than one outcome | Blocking | Fail closed on ambiguous classification | N/A | N/A | N/A | Exhaustiveness/mutual-exclusivity test (135C §13) |
| CLTR-COMMIT-3 | Commit ownership | Fabricated hashes are never silently equivalent to verified | CERTIFYING | Record, Git attribution view | Unresolvable hash's classification | Classified `unverifiable`, never silently `verified` | Unresolvable hash classified/treated as `verified` (today's Gap C behavior) | Blocking (representability); blocking-vs-warning *policy* deferred (§17) | Record the outcome distinctly regardless of downstream policy | N/A | Candidate if policy treats it as suspicious | Gap C (§0) is the canonical current-source negative example, not repaired here | Regression test against the exact `continue`-past-failure pattern |
| CLTR-EVID-1 | Evidence | Report prose never serves as sole evidence for an R/E-role fact | CERTIFYING onward | Report | Whether a fact classified R/E has a structured reference vs. only narrative text | Structured reference present | Only prose exists for an R/E-role fact | Blocking | Reject the report as insufficiently evidenced | N/A | N/A | N/A | Schema-level presence check (deferred to schema phase, but the *test strategy* is nameable now) |
| CLTR-PERSIST-1 | Persistence | The current pointer never exposes a mixed-generation report/metadata pair | PROMOTED onward | Latest pointer, promoted report/metadata | Generation identity of each half of the pointer pair | Both halves bind the same `transition_id` | Halves bind different `transition_id`s | Blocking | Reject the read; surface as atomic-visibility failure | N/A | N/A | Gap B (§0) is the current live counterexample, not repaired here | Concurrent-read/crash-injection test |
| CLTR-PERSIST-2 | Persistence | Immutable history is never rewritten | CERTIFIED onward | Record, snapshot, historical reports/metadata | Digest of a historical artifact at two points in time | Digest unchanged | Digest changed | Blocking | Reject the write; candidate quarantine | N/A | Yes | Historical Track 134 artifacts are exempt only in the sense of predating any record — once a record exists, no exemption | Digest-comparison test over time |
| CLTR-PERSIST-3 | Persistence | The mutable current pointer is always reconstructible from immutable history | PROMOTED onward | Latest pointer | Pointer's target vs. most recent immutable history entry | Pointer, if corrupted/missing, can be rebuilt from history alone | Pointer is the *only* place a fact lives (no history to reconstruct from) | Blocking | Reconstruct from history; never treat corrupted pointer as ground truth | N/A | N/A | N/A | Deliberately corrupt the pointer, verify reconstruction |
| CLTR-RETRY-1 | Retry | NOTIFIED_UNCONFIRMED is resume-terminal by the record's own logic, not only entry points | NOTIFIED_UNCONFIRMED | Record's own resume-check logic | Resume-check function's own recognized-terminal set | NOTIFIED_UNCONFIRMED ∈ recognized-terminal set, checked by the record/transaction itself | Resume-check recognizes only `"completed"` (today's Gap A) | Blocking | This is the direct 134F-gap-closure invariant | This *is* the retry-consequence definition | N/A | Current entry-point-only marker check is `adapter`-classified, insufficient alone | Exactly the test that would catch Gap A: resume with a `NOTIFIED_UNCONFIRMED`-equivalent record and assert no re-dispatch |
| CLTR-RETRY-2 | Retry | A duplicate ordinary completion for an already-terminal phase/task is rejected | PROPOSED (of a new, colliding transition) | Record | New PROPOSED's declared phase/task vs. existing terminal record for the same phase/task | New PROPOSED rejected, referencing the existing terminal record | New PROPOSED silently accepted as a fresh success | Blocking | Reject; reference the existing terminal record | N/A | N/A | N/A | Duplicate-submission test |
| CLTR-RETRY-3 | Retry | Recovery from an unknown-outcome crash always observes actual external state before deciding | Crash mid-PROMOTING/NOTIFYING | Record, observation event | Whether an explicit observation event precedes any retry decision | Observation event exists and is dated before the retry decision | Retry decision made without a prior observation event | Blocking | Block the retry decision until observation completes | This *is* the retry-consequence definition | N/A | N/A | Crash-injection + observation-order test |
| CLTR-NOTIFY-1 | Notification | Notification references promoted canonical evidence, never independently re-gathered evidence | NOTIFYING | Notification payload | Payload's evidence source vs. record's PROMOTED-state bindings | Payload traces to exactly the PROMOTED record's evidence | Payload includes independently re-fetched "current" evidence | Blocking | Reject the payload; regenerate from the record | N/A | N/A | N/A | Payload-provenance test |
| CLTR-NOTIFY-2 | Notification | Notification retry only from NOTIFYING, never from NOTIFIED/NOTIFIED_UNCONFIRMED | NOTIFYING only | Record | Which state a retry (T11) is entered from | T11 entered only from NOTIFYING | T11-equivalent re-dispatch attempted from NOTIFIED/NOTIFIED_UNCONFIRMED | Blocking | Reject the retry; direct to receipt reconciliation (T12) instead | N/A | N/A | N/A | Exactly F6 (§6) at the invariant-inventory layer |
| CLTR-MARKER-1 | Marker | Marker and receipt for a transition bind the same `transition_id` | NOTIFIED/NOTIFIED_UNCONFIRMED onward | Marker, receipt | `marker.transition_id` vs. `receipt.transition_id` | Equal | Differ | Blocking | Flag as a detectable inconsistency | N/A | Candidate | N/A | Cross-binding equality test |
| CLTR-MARKER-2 | Marker | Marker presence alone is never sufficient proof of terminal state | Any | Marker, record | Whether a consumer's terminal-state determination consults the record | Record consulted | Marker alone treated as proof | Blocking | Consult the record before trusting the marker | N/A | N/A | Current entry points consult *only* the marker — `adapter`-classified, a disclosed compatibility gap, not `conformant` | Test: delete the record, keep the marker, assert no consumer claims terminal state |
| CLTR-RECEIPT-1 | Receipt | Receipt reflects actual observed delivery outcome, never assumed/optimistic | NOTIFIED/NOTIFIED_UNCONFIRMED | Receipt | Receipt's claimed outcome vs. record's actual notification-stage outcome | Equal | Receipt claims success the record does not show | Blocking | Reject a receipt that claims success without matching record state | N/A | Candidate | Current source's "read from the real promoted report" discipline is the positive precedent (135C §23) | Optimistic-receipt-injection test |
| CLTR-COMPAT-1 | Compatibility | Historical artifacts are never rewritten, migrated in place, or reinterpreted as record-produced | All (applies to pre-record artifacts) | All historical representations | Artifact's own digest/content over time | Unchanged | Changed, or reinterpreted under CLTR-001 semantics without a record | Blocking | Reject the mutation | N/A | Candidate | This is the compatibility contract's own central guarantee | Historical-artifact-immutability test |
| CLTR-COMPAT-2 | Compatibility | PFN-001 and PFR-001 remain unamended by any CLTR-001-conformant work | All | PFN-001, PFR-001 texts and guarantees | Whether any CLTR-001-derived work changes either contract's text or guarantees | No change | Any change | Blocking | Reject the change as out of CLTR-001's scope | N/A | N/A | N/A | Document-diff check against PFN-001/PFR-001 baselines |
| CLTR-SAFE-1 | Safety | Runtime remains Observed/observe/execution unavailable throughout any CLTR-001-conformant work | All | `pcae runtime inspect` | Runtime state before/after any CLTR-001-related change | Unchanged | Changed | Blocking | Reject the change | N/A | N/A | N/A | Re-run `pcae runtime inspect`, diff |
| CLTR-SAFE-2 | Safety | The record never becomes an execution-authorization mechanism | All | Record, every state | Whether any state's definition grants/implies/preconditions an execution capability | No state does | Any state's semantics are read as "may execute" | Blocking | Reject the design | N/A | N/A | N/A | Semantic audit, performed in §35 below |
| CLTR-SAFE-3 | Safety | Terminal states are recognized consistently by both the record's own core logic and every consuming entry point | NOTIFIED, NOTIFIED_UNCONFIRMED, TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_PRE_CERT | Record's resume logic, all four entry points | Whether the record's own logic and each entry point agree on terminal classification | Agreement | Disagreement (today's Gap A: entry points' marker check disagrees with the transaction's own resume check) | Blocking | This is the structural fix for 134F's finding | Required of any future implementation | N/A | Current state is `adapter` — entry points provide real (if fragile) safety today, per 134F | Cross-entry-point consistency test, once implemented |

### 11.1 Numbering-completeness closure

With CLTR-ORDER-5, -6, -7 added, §8.2's seven ordering requirements now each have a dedicated numbered invariant entry (previously 4 of 7, per 135C finding #7, §37 below). This is a **derived clarification of CLTR-001**, not an amendment: no new substantive requirement is introduced — CLTR-001 §8.2 items 4, 6, 7 were already binding contract text; only their representation in the numbered inventory (§26.1) was incomplete. The total invariant count under this document's inventory is therefore **36** (33 original + 3 closure entries), all traced to already-frozen CLTR-001 text.

---

## 12. Invariant completeness review

Checked against the assignment's twenty-category completeness list. Each row states whether §11's 36 invariants cover the category, and if a gap exists, its classification.

| Category | Covered by | Gap found? | Classification if gap |
|---|---|---|---|
| Identity | CLTR-ID-1, CLTR-ID-2, §13 below | None | — |
| Authority | CLTR-AUTH-1, CLTR-AUTH-2, §14 below | None | — |
| State | CLTR-STATE-1..4, §15 below | None | — |
| Ordering | CLTR-ORDER-1..7, §16 below | None (closed by §11.1) | — |
| Projected state | §9 (CLTR-001), CLTR-STATE-1/2, §18 below | None | — |
| Certification | §7 (this document), CLTR-ORDER-1/4 | None | — |
| Commit ownership | CLTR-COMMIT-1..3, §17 below | **Partial**: branch-reachability/rewritten-history not a named evaluation input (135C finding #2) | Implementation-level invariant, non-blocking recommendation (§37 #2) |
| Evidence binding | CLTR-EVID-1, §19 below | None | — |
| Derivation | CLTR-DERIVE-1, CLTR-DERIVE-2 | None | — |
| Persistence | CLTR-PERSIST-1..3 | None | — |
| Atomic visibility | CLTR-PERSIST-1, §20 below | None | — |
| Immutable history | CLTR-PERSIST-2, CLTR-COMPAT-1 | None | — |
| Notification | CLTR-NOTIFY-1..2, §21 below | None | — |
| Marker | CLTR-MARKER-1..2, §22 below | None | — |
| Receipt | CLTR-RECEIPT-1, §23 below | None | — |
| Retry | CLTR-RETRY-1..3, §24, §25 below | None | — |
| Replay | CLTR-RETRY-2, §26 below | None | — |
| Compatibility | CLTR-COMPAT-1..2, §29 below | None | — |
| Final repository observations | §7.5, §31 below | **Partial**: quantitative grace-period bound for provisional `final_revision` left unspecified (135C finding #5, CLTR-001 §23.4 item 4) | Implementation-level invariant (a numeric parameter), non-blocking |
| Execution boundary | CLTR-SAFE-1..3, §35 below | None | — |

### 12.1 Missing-invariant candidates identified during this review

Two candidates were found not fully covered by a Blocking invariant (both already disclosed by 135C, re-confirmed here rather than newly discovered):

1. **Branch-reachability / rewritten-history commit verification** (135C finding #2). Classification: **implementation-level invariant** — the three-outcome taxonomy (verified/contaminated/unverifiable) is already expressive enough to accommodate this as a refinement (a branch-unreachable hash classifies as `unverifiable` under CLTR-001 §10.4's existing definition, "cannot be resolved against the bound repository identity/revision"); no CLTR-001 text change is required, only a future schema/implementation phase's evaluation-input list must include branch reachability and history-rewrite detection. **Not promoted to Blocking** — the existing CLTR-COMMIT-2/3 invariants already force a distinct, recorded outcome for any hash that cannot be verified this way; the gap is in the *evaluation procedure's* input completeness, not in the invariant's own severity or determinism.
2. **Provisional `final_revision` grace-period bound** (135C finding #5). Classification: **implementation-level invariant** — CLTR-001 §23.4 item 4 already establishes the *qualitative* rule (TERMINAL_SUCCESS is blocked while `final_revision` remains provisional past the bound); only the *quantitative* bound itself is unspecified. **Not promoted to Blocking** — the qualitative rule is fully specified and independently satisfiable regardless of the numeric value eventually chosen.

No candidate in this review was found to require a **new Blocking invariant** beyond CLTR-ORDER-5/6/7 (§11.1) or to require **amending CLTR-001's text**. Both candidates above are correctly deferred, consistent with CLTR-001's own deferral pattern (§32.3), and are re-affirmed here as still-open, still-non-blocking, still-correctly-scoped-to-a-later-phase.

---

## 13. Identity invariants

Formal verification for each identifier type named by the assignment, each evaluated against exact equality, dotted/multi-dotted forms, suffix preservation, no prefix matching, no truncation, no fuzzy matching, no title-derived identity, no commit-subject-derived identity, and cross-transition substitution resistance.

| Identifier | Exact equality | Dotted/multi-dotted | Suffix preservation | No prefix match | No truncation | No fuzzy match | No title-derived identity | No commit-subject-derived identity | Cross-transition substitution resistance |
|---|---|---|---|---|---|---|---|---|---|
| `transition_id` | Required (CLTR-ID-1) | N/A (not phase-ID-shaped) | N/A | Required — no transition may resolve by ID prefix | Required | Required | Required — this is the exact identity this document's §11's CLTR-ORDER-5 entry exists to protect (Architecture Status bug, 135C §25.2) | Required | Required — receipt/marker/notification all bind this exact value (CLTR-MARKER-1) |
| `phase_id` | Required (CLTR-ID-2) | Required — `134E.10.1V.1`-class forms preserved exactly (CLTR-001 §5.2 item 1) | Required — the 134E.10.1.1/134E.10.1V.1 regression class is the standing negative example | Required | Required (the literal fix codified as a standing rule) | Required | Required — same Architecture Status bug class | Required (§4.2 item 7) | Required — repository-binding rule (§5.2 item 6) |
| `task_id` | Required, explicitly nullable | Same grammar discipline as `phase_id` where applicable | Same | Required | Required | Required | Required | Required | Bound to its declaring `phase_id` (§5.2 item 8) — never resolved independently |
| `repository_id` | Required | N/A | N/A | Required | Required | Required | N/A | N/A | Required — every sub-transition identifier is implicitly scoped to it (§5.2 item 6) |
| `report_id` | Required, bound at CERTIFIED | N/A | N/A | Required | Required | Required | Required | Required | Bound to exactly one `transition_id` (§5.2 item 7) |
| `metadata_id` | Required, bound at CERTIFIED | N/A | N/A | Required | Required | Required | Required | Required | Same |
| `snapshot_id` | Required, bound at CERTIFIED | N/A | N/A | Required | Required | Required | N/A | N/A | Same |
| `checkpoint_id` | Required, bound at PROPOSED | N/A | N/A | Required | Required | Required | N/A | N/A | Same |
| `promotion_id` | Required, bound at PROMOTED | N/A | N/A | Required | Required | Required | N/A | N/A | Same |
| `notification_id` | Required, bound at NOTIFYING (possibly plural across retries) | N/A | N/A | Required | Required | Required | N/A | N/A | Every instance still bound to the same one `transition_id` |
| `marker_id` | Required, bound to `transition_id` | N/A | N/A | Required | Required | Required | N/A | N/A | Required (CLTR-MARKER-1) |
| `receipt_id` | Required, bound to `transition_id` | N/A | N/A | Required | Required | Required | N/A | N/A | Required (CLTR-MARKER-1, CLTR-RECEIPT-1) |

**Formal statement, all twelve identifiers:** for identifier type `X` bound to transition `t`, and any two representations `r1, r2` both claiming to describe `X` for `t`: `r1.X == r2.X` must hold by byte-for-byte comparison unless `X`'s type explicitly and separately declares a case-insensitive comparison rule (CLTR-001 §5.2 item 5) — never a globally-assumed permissive comparison. No identifier type above is exempted from any of the nine columns; every "Required" cell traces to CLTR-001 §5.1–§5.3, independently re-checked here per-identifier rather than accepted as a blanket claim.

---

## 14. Authority invariants

Formal definitions, each restated as an evaluable predicate:

1. **Exactly one authority per lifecycle fact.** ∀ fact `f` classified in CLTR-001 §3.2: exactly one role (S, R, D, E, or V) is assigned, and no second artifact independently establishes `f`'s value. Evaluable as: for any two representations claiming to state `f`, at most one is the declared S/R/E-role source; every other representation's value for `f` must be *derivable* (a pure function, CLTR-DERIVE-1) from that source, never independently asserted.
2. **Derivatives cannot override authority.** ∀ derivative `d` and fact `f`: `d.f` is accepted only if `d.f == derive(record, f)`; a derivative asserting a different value for an S/D-role fact is rejected, not reconciled by preferring the derivative.
3. **Evidence cannot become authority.** R/E-role facts (tests, governance checks, notification result) bind an *identity/digest reference* to external evidence; the evidence's own content is never treated as if it were itself an S-role fact about the transition's lifecycle state (e.g., a test suite passing does not, by itself, make the transition CERTIFIED — CERTIFIED requires the full CLTR-001 §8.1 ordering to have been satisfied, of which test evidence is only one input).
4. **Observations cannot redefine certified truth.** V-role facts (repository cleanliness, pushed state, `origin/main..HEAD`) are bound as point-in-time historical facts (§7.2, CLTR-001 §23.3); a later, different observation of current repository state never retroactively changes what was true *for that transition* at certification time.
5. **Markers cannot independently prove completion.** CLTR-MARKER-2: formalized as `terminal(record) := f(record.spine_state)`, never `f(marker.presence)`. A consumer computing `terminal` from marker presence alone violates this invariant regardless of whether the marker happens to be correct in a given instance.
6. **Receipts cannot independently establish stages that did not occur.** CLTR-RECEIPT-1, CLTR-ORDER-7: `receipt.claimed_stages ⊆ record.actually_reached_stages` must hold; a receipt is evidence *about* the record's own state, never a second, independent source for what that state is.
7. **Mutable latest files cannot establish certification.** The latest pointer (`latest.md`/`latest.json` or successor mechanism) is D-role only (CLTR-001 §4.2 item 9); `certified(record) := record.spine_state ≥ CERTIFIED`, never `certified(record) := latest_pointer.exists_and_matches(record)`.
8. **Architecture Status cannot establish active lifecycle state.** `active(phase) := ∃ record for phase: record.spine_state ∈ [PROPOSED, PROMOTING]` (per §9.4 of CLTR-001, the successor-activation rule) — Architecture Status is a rendering *of* this predicate, never an independent input to it. This is precisely the invariant the live Architecture Status title-mislabeling bug (135C §25.2) demonstrates the cost of violating at the *derivation* layer (a title, not lifecycle authority, but the same class of failure).
9. **Git history cannot establish phase ownership without explicit binding.** `owns(transition, commit) := commit ∈ transition.declared_commit_set ∧ classify(commit) ∈ {verified, contaminated}` — never `owns(transition, commit) := recent(commit) ∧ no_conflicting_claim(commit)` (the exact `git log --oneline -N` fallback pattern CLTR-001 §4.2 item 6 and §9.3 of 135A forbid, already retired from the primary code path by 134E.10.1.1 and forbidden from reintroduction anywhere by this invariant).

**Cross-check against §11's table:** every one of these nine authority rules maps to CLTR-AUTH-1, CLTR-AUTH-2, or one of the nine forbidden-pattern items in CLTR-001 §4.2 — no authority rule here is newly invented; each is the same requirement restated as an evaluable predicate rather than contract prose, per this phase's own instruction not to merely reproduce the contract's wording.

---

## 15. State invariants

1. **Completed transition implies phase inactive.** `∀ phase p: latest_record(p).spine_state ∈ {TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL} ⇒ active(p) = False` (CLTR-STATE-1).
2. **Inactive phase must not appear under In Progress.** `active(p) = False ⇒ p ∉ ArchitectureStatus.in_progress` — a direct rendering-layer consequence of invariant 1, enforced by CLTR-ORDER-5 (no post-certification mutable read may redefine the transition).
3. **No active phase implies explicit empty active-state projection.** `(∄ p: active(p)) ⇒ ArchitectureStatus.in_progress == ∅` explicitly, never an omitted/undefined field that a renderer could misinterpret as "unknown" rather than "empty." (CLTR-001 §9.1 "must" item 6, §22.1 item 3.)
4. **Planned successor remains inactive.** `successor(p) = s ⇒ active(s) = False` until `s`'s own record independently reaches PROPOSED-or-later (CLTR-STATE-2, §9.4 of CLTR-001).
5. **Certified state cannot revert to uncertified.** `∀ record r: r.spine_state ≥ CERTIFIED ⇒ □(r.spine_state ≥ CERTIFIED)` (a temporal-logic "once true, always true" statement) — formalizing F5 (§6) and CLTR-STATE-3.
6. **Terminal state cannot ordinary-replay.** `r.spine_state ∈ {TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL} ⇒` any new PROPOSED for the same phase/task is rejected, not accepted as a new attempt (CLTR-RETRY-2, F7).
7. **Superseded state cannot become current.** `r.superseded = True ⇒ current_pointer(phase(r)) ≠ r`, always — enforced by F8 and CLTR-ID-2 (only one record's identity may be "the most recent" for a phase at any time).
8. **Quarantined state cannot become terminal success without explicit recovery transition.** `r.quarantined = True ⇒ r.spine_state` does not advance to/remain asserted as TERMINAL_SUCCESS without a human-review-gated recovery event (F9, §18.1 QUARANTINED row "Human review: Yes, always").

All eight state invariants above are traced to CLTR-STATE-1..4 (§11) or a named forbidden transition (§6); none introduces a new state-machine rule beyond what §3–§6 of this document already establish — this section exists to restate them as point predicates for future test-authoring convenience, per the assignment's explicit instruction to produce "formal conditions."

---

## 16. Ordering invariants

Formally verified (predicate form; source: CLTR-ORDER-1..7, §11):

1. **Authority binding before validation.** `bind(identity, evidence) ≺ validate(record)` — T1/T2 must precede any part of T3's checks.
2. **Validation before certification.** `validate(record) ≺ certify(record)` — T3's internal checks must pass before the CERTIFIED state mutation occurs (this is the same event, decomposed: "validate" is not a separate T-row, it is T3's precondition).
3. **Certification before checkpoint.** Formally, per §7.4/§8.3's clarification: checkpointing is the *durability mechanism* for CERTIFIED, not a distinct stage — so this invariant reduces to "CERTIFIED is never observably durable before its own certification checks pass," which CLTR-ORDER-1 already states.
4. **Checkpoint before promotion.** `durable(CERTIFIED, record) ≺ begin(PROMOTING, record)` — CLTR-ORDER-2, T5's precondition.
5. **Promotion before terminal external notification.** `reach(PROMOTED, record) ≺ begin(NOTIFYING, record)` — CLTR-ORDER-3, T8's precondition.
6. **Notification classification before marker if required.** `classify(NOTIFIED | NOTIFIED_UNCONFIRMED, record) ≺ write(marker, record)` — CLTR-ORDER-6 (new, §11.1), F10.
7. **Marker before complete receipt if contract requires.** **Independently re-examined, not assumed**: CLTR-001 §8.1 step 11 lists "Marker persistence" before step 12 "Receipt persistence" — but §19.1/§20.1 do not actually require marker-before-receipt as a *precondition*; both are independent derivatives of the same NOTIFIED/NOTIFIED_UNCONFIRMED state, and CLTR-001 nowhere states a receipt is invalid if written before a marker. **Finding**: §8.1's numbered list is a narrative ordering (a reasonable default sequencing), not a binding precondition-enforcing invariant, for this specific pair — unlike marker-before-required-stages (item 6 above, which *is* a genuine precondition per §8.2 invariant 4). This is a **non-blocking clarification** of this document's own making (§37, new finding): the two derivatives (marker, receipt) may be written in either order, or concurrently, without violating any CLTR-001 invariant, so long as both individually satisfy their own creation-timing rules (marker: not before NOTIFIED/NOTIFIED_UNCONFIRMED; receipt: reflects actually-reached stages, CLTR-ORDER-7). This is recorded as a genuine, if narrow, finding of this phase (§37, not one of 135C's ten, and not previously disclosed) — classified **non-blocking**, an implementation-level sequencing freedom, not a contract defect.
8. **Receipt reflects actual completed stages.** `receipt.claimed_stages ⊆ record.actually_reached_stages` — CLTR-ORDER-7.
9. **No irreversible stage before certification.** `∀ op ∈ irreversible(§8.1): time(op) > time(certify(record))` — CLTR-ORDER-4.
10. **No post-certification mutable state redefines the transition.** `∀ t > certify(record): derive(record_at_certify, d) == derive(record_at_t, d)` for any derivative `d` — CLTR-ORDER-5.

**Finding disposition:** item 7's non-blocking clarification (marker/receipt ordering freedom) is the one substantively new observation in this section; all other nine items restate §11's already-established invariants in explicit temporal-predicate form, per this phase's instruction to formally verify (not merely restate) the ordering contract.

---

## 17. Commit-ownership invariants

Formal invariant behavior, evaluated per case (source: CLTR-001 §10, CLTR-COMMIT-1..3, 135C §13):

1. **Explicit ownership declaration.** `∀ record r: r.declared_commits` is an explicit set, declared at PROPOSED (T1), never inferred at CERTIFYING time from Git history scanning.
2. **Repository existence.** Every declared commit hash is checked for existence via `git log -1 <hash>` (or equivalent) within the bound `repository_identity`.
3. **Repository identity binding.** A hash resolving only in a *different* repository than `r.repository_identity` is never treated as belonging to `r` — classified `unverifiable` (not silently dropped).
4. **Branch/revision consistency.** **Not yet a named CLTR-001 evaluation input** (135C finding #2, §12.1 #1 above) — this document classifies branch-reachability and rewritten-history detection as an **implementation-level invariant**: a future schema/verification phase should extend the `unverifiable` classification's evaluation procedure to include "hash exists in object database but is unreachable from `r.branch_identity`" and "hash predates a history rewrite invalidating its original context." Both cases are *already* representable under the existing three-outcome taxonomy without any CLTR-001 text change — only the verification *procedure* needs extension, not the *contract*.
5. **Order preservation.** Declared commits are treated as a **set**, not a sequence, for ownership-verification purposes (CLTR-001 §10.1 item 6) — no ordering claim is made or required by this invariant architecture; ordering *within* Git history remains an orthogonal, already-solved concern.
6. **No prior-phase contamination.** `∀ commit c ∈ r.declared_commits: subject(c)` does not name a different phase's ID as its primary attribution — else classified `contaminated`.
7. **No unrelated commits.** Same mechanism as item 6 — recency alone is never sufficient grounds for inclusion in `r.declared_commits` (CLTR-001 §4.2 item 6, §10.2 item 4).
8. **No recent-git fallback.** `r.declared_commits` is never computed as `git log --oneline -N` — this fallback is retired everywhere, not just at the one call site 134E.10.1.1 already fixed (CLTR-001 §25.1).
9. **No commit-subject authority.** `subject(c)` is evidence for contamination *detection* (a signal), never proof of ownership on its own (CLTR-001 §9.3 of 135A, §4.2 item 7).
10. **Fabricated hashes.** `∀ c ∈ r.declared_commits: resolve(c) ∈ {verified, contaminated, unverifiable}`, exhaustively and mutually exclusively (CLTR-COMMIT-2) — never silently collapsed to `verified` by omission (CLTR-COMMIT-3; Gap C, §0, is the live current-source counterexample, not repaired here).
11. **Unverifiable hashes.** Classified distinctly and recorded; whether `unverifiable` blocks, warns, or is informational remains an **explicitly deferred governance-policy question** (CLTR-001 §10.4, re-affirmed still-deferred by this phase, not resolved here — see §37 disposition of 135C's related finding #4).
12. **No-commit phases.** `r.declared_commits = ∅` is a valid, first-class declaration (e.g., this very phase, 135D, and 135A/135B/135C before it) — never an implicit default reached by falling through an unhandled case.
13. **Verification-only phases.** A transition may legitimately declare zero source-changing commits while still declaring the governed completion/metadata-sync commits that accompany its own finalization — the record's classification capability (CLTR-001 §10.2 item 3) must be able to represent *why* a commit belongs (documentation, repair, verification-only), deferred in exact enumeration to schema work but required in *capability* now.
14. **Completion commits.** The commits a governed phase's own finalization produces (PROJECT_STATUS.md/CHANGELOG.md/tasks sync, canonical report/metadata commits) are themselves classifiable as phase-owned per item 13's capability — this is exactly the pattern this very phase's own eventual finalization will produce (§41).

### 17.1 Three-outcome model and state-transition effect

The three-outcome model (verified/contaminated/unverifiable) affects state transitions as follows, per CLTR-001 §18.1's "Commit ownership conflict" row and this document's own §5/§6:

- **verified**: no transition effect; T3 (`certify`) proceeds normally if all other CERTIFYING checks pass.
- **contaminated**: T3 may still succeed or route to T4, **per governance policy** — CLTR-001 does not itself decide this; this document does not resolve it either (explicitly deferred, consistent with CLTR-001 §10.4). The transition this cannot proceed past, until policy is resolved, is **T3 itself** for any record containing a `contaminated` classification, if and only if governance policy chooses to make `contaminated` blocking (policy-dependent, not contract-dependent).
- **unverifiable**: same deferred-policy structure as `contaminated` — the specific blocked transition, pending policy resolution, is again **T3**, and only T3; no other transition in §5's inventory depends on the commit-ownership outcome.

**No policy decision not already frozen by CLTR-001 is made here.** This document restates, rather than resolves, the deferred blocking-vs-warning-vs-informational question (§37 disposition of 135C finding #4).

---

## 18. Projected-state invariants

Formal invariants (source: CLTR-001 §9, re-verified sound by 135C §12):

1. **Deterministic projection.** `projected_state(record) = f(record.inputs_at_CERTIFYING)`, a pure function — no I/O, no randomness (CLTR-DERIVE-1 applied specifically to projection).
2. **Authority-bound projection inputs.** `f`'s domain is restricted to declared identity, declared prior state, and declared recommended successor — never mutable state re-scanned at projection-compute time.
3. **Completed phase removed from active state.** `projected_state(record).active_phases` excludes `phase(record)` once `record` reaches CERTIFIED — CLTR-STATE-1 applied at the projection layer specifically.
4. **Successor not activated.** `projected_state(record).recommended_successor ≠ projected_state(record).active_phase` — these are structurally different fields, never conflatable (§9.4 of CLTR-001, CLTR-STATE-2).
5. **Projection stable after certification.** `∀ t1, t2 ≥ certify(record): projected_state(record, t1) == projected_state(record, t2)` — CLTR-DERIVE-2 applied to the projection specifically.
6. **Every derivative uses the same projection.** `∀ d1, d2 ∈ derivatives(record): d1.projected_state_ref == d2.projected_state_ref == record.projected_state` — no derivative computes its own independent projection.
7. **No post-certification regeneration.** Regenerating any derivative must reproduce `projected_state(record)` byte-identically; a divergent regeneration is a derivation bug (CLTR-ORDER-5), never a signal to recompute from current mutable state.
8. **No latest-state merge.** `projected_state(record)` never merges fields from the current mutable latest pointer — it is computed once, at CERTIFYING, from declared inputs only.
9. **No report-based inference.** `projected_state(record).active_phase` is never inferred from report title/prose presence — this is exactly the Architecture Status title-extraction bug class (135C §25.2), independently re-flagged here as the canonical violation this invariant exists to forbid.
10. **No active-task fallback after certification.** Once `record` reaches CERTIFIED, no consumer may fall back to task-memory/PROJECT_STATUS.md free-text inference for `active_phase` even if the projection is temporarily unavailable — unavailability is an explicit failure (§27 below), never a silent fallback to a different (inferior) authority source.

---

## 19. Evidence invariants

1. **Evidence identity binding.** Every R/E-role evidence reference (test results, governance checks, notification result) carries the identifier of the record it is bound to — `evidence.transition_id == record.transition_id`, always (implicit in CLTR-EVID-1, made explicit here per 135C finding #6's related observation about cross-referencing style, non-blocking).
2. **Evidence timestamp/observation-point binding.** V-role evidence (repository cleanliness, pushed state) is tagged with its own measurement timestamp (CLTR-001 §23.3 item 1) — never left implicitly dated to "whenever the record was read."
3. **Stale evidence rejection.** A V-role value's binding is historically fixed; it is never re-used as if it were a fresh measurement for a *different* purpose (e.g., a later `pcae health` check) without an explicit fresh measurement (CLTR-001 §23.3 item 2).
4. **No evidence strengthening.** A derived summary (e.g., files-changed, D-role) never asserts something the bound evidence (source/final revision) does not itself support (CLTR-001 §11.1's "files changed" row).
5. **No prose-only evidence.** CLTR-EVID-1 — R/E-role facts require a structured reference; narrative report prose may explain but never solely evidence such a fact.
6. **No silent evidence substitution.** A verification pass presented with a digest that does not match its claimed evidence must reject or quarantine, never silently accept a different evidence set as if it were the one certified (CLTR-001 §15.1 item 7).
7. **No cross-phase evidence reuse without explicit reference.** Evidence bound to transition `t1` is never treated as evidence for a different transition `t2` merely because they concern the same phase — each transition's evidence bindings are its own (CLTR-001 §5.2 item 7's "never shared across two transitions" rule, extended here explicitly to evidence, not only identifiers).
8. **Unavailable evidence classification.** Missing required evidence at CERTIFYING blocks T3 (routes to T4/FAILED_PRE_CERT) — it is never silently treated as "passing by default" (CLTR-001 §3.2's "failure behavior when unavailable" column, cross-checked exhaustively by 135C §5 with no fact found missing a defined failure behavior).
9. **Governance observation truthfulness.** Bound governance-check evidence (`pcae health`/`check`/`doctor task-memory`/`push check`/`runtime inspect` results at certification time) reflects the actual tool output at that moment — never a summary that could disagree with a literal re-run of the same tool against the same state.
10. **Runtime-state observation truthfulness.** Same principle applied specifically to `pcae runtime inspect`'s snapshot at CERTIFYING (CLTR-001 §11.1 "Runtime state" row) — bound once, not live-re-queried by later derivatives claiming to describe *that* transition's certification-time runtime state.

---

## 20. Atomic-visibility invariants

Formal, implementation-independent, testable requirements (source: CLTR-001 §13.3, independently re-confirmed testable by 135C §16):

1. **A consumer sees exactly one generation.** `∀ read(latest_pointer): read` resolves to exactly one `transition_id`'s report+metadata pair, never a value that could be attributed to two different generations simultaneously.
2. **Report and metadata generation IDs match.** `read(latest.report).transition_id == read(latest.metadata).transition_id`, always — this is CLTR-PERSIST-1 stated as a direct equality check.
3. **Partially written generations are invisible.** A reader observing the pointer mid-write sees either the fully-old or fully-new pair, never a torn/partial write (all-or-nothing visibility).
4. **Current pointer changes atomically.** The pointer-switch operation itself (whatever mechanism a future phase selects, per CLTR-001 §13.2's deliberately-undecided menu) is a single indivisible operation from any reader's perspective.
5. **Pointer target is complete.** Once the pointer is switched, both halves of the pair it points to are already fully written — the switch is the *last* operation, never a signal that "writing has begun."
6. **Stale pointer is detectable.** A reader can compare the pointer's target generation against the most recent entry in immutable history and detect if the pointer lags behind (CLTR-PERSIST-3).
7. **Missing pointer is recoverable deterministically.** If the pointer itself is corrupted or absent, it is reconstructible from immutable history alone, with no dependency on timing or retry count (CLTR-001 §13.3 item 5, CLTR-PERSIST-3).
8. **Historical generation remains immutable.** Once superseded, a prior generation's content is never rewritten — only the pointer moves (CLTR-PERSIST-2 applied specifically to the pointer-switch mechanism).
9. **Crash recovery cannot expose mixed state.** A crash during the pointer-switch operation, whatever mechanism is eventually chosen, must leave the system in a state a reader can classify as either "still old, write not yet visible" or "already new, write fully visible" — never an undefined third state.

**No implementation mechanism is selected here** — consistent with CLTR-001 §13.2's deliberate deferral, re-affirmed by 135C §16 as non-blocking and testable regardless of mechanism. The current live gap (Gap B, §0: three plain `path.write_text()` sites, no `os.replace`, in `canonical_artifact_promotion.py:111,115,141`) is the compatibility-evidence counterexample these nine invariants are designed to make structurally impossible — not repaired here (§29, §44).

---

## 21. Notification invariants

Preserving PFN-001 (re-verified unamended, §0 item 6; source: CLTR-001 §21, CLTR-NOTIFY-1..2):

1. **Exactly one governed terminal external delivery.** `∀ record r: |{successful dispatches for r}| ≤ 1` — PFN-001's exactly-once guarantee, tracked (not reimplemented) by this record's NOTIFYING/NOTIFIED/NOTIFIED_UNCONFIRMED stages.
2. **Dispatch only after promotion.** `time(begin(NOTIFYING, r)) > time(reach(PROMOTED, r))` — CLTR-ORDER-3, T8's precondition.
3. **Payload identity equals promoted transition identity.** `payload.transition_id == r.transition_id`, and `payload` is generated only from `r`'s PROMOTED-state evidence bindings.
4. **Payload evidence derives from promoted canonical artifacts.** `payload.evidence_refs ⊆ r.promoted_evidence_bindings` — never independently re-gathered "current" evidence at dispatch time (CLTR-NOTIFY-1).
5. **Test adapters cannot dispatch externally.** PFN-001's existing `PCAE_NOTIFY_ENABLED`/sink-isolation discipline is unchanged; this document introduces no new dispatch path that could bypass it.
6. **Ordinary replay cannot redispatch.** `r.spine_state ∈ {NOTIFIED, NOTIFIED_UNCONFIRMED} ⇒` any subsequent submission for the same transition resolves to the existing record's state, never re-entering NOTIFYING (CLTR-NOTIFY-2, F6).
7. **Unconfirmed delivery cannot be treated as never attempted.** `r.spine_state == NOTIFIED_UNCONFIRMED ⇒ delivery_attempted(r) == True` — this is the exact distinction CLTR-RETRY-1 exists to preserve; NOTIFIED_UNCONFIRMED is never conflated with "notification never happened."
8. **Receipt must distinguish attempted, confirmed, failed, and unknown outcomes.** `receipt.outcome ∈ {confirmed, best_effort_incomplete, failed, unknown}` as four genuinely distinct, non-overlapping values (formalizing CLTR-001 §20.2 item 9's "best-effort incomplete" flag as one instance of a more general four-way classification this document names explicitly for the first time — a **derived clarification**, not a new requirement, since CLTR-001 §18.1's failure table already distinguishes these four cases informally row-by-row).
9. **Telegram remains outbound-only.** No inbound control path exists or is implied by any NOTIFYING-stage invariant (CLTR-001 §21.1 item 8, §28).
10. **No inbound lifecycle authority.** No external system's response to a delivered notification is ever treated as an authoritative input to any subsequent state transition (CLTR-001 §28.2, §35 below).

---

## 22. Marker invariants

1. **Marker identity equals transition identity.** `marker.transition_id == r.transition_id`, always (CLTR-MARKER-1, §19.2 item 1).
2. **Marker phase equals record phase.** `marker.phase_id == r.phase_id` (implied by item 1, restated for the phase-level identifier specifically, per CLTR-ID-2's phase-level scope).
3. **Marker cannot precede required stages.** `time(write(marker, r)) ≥ time(reach(NOTIFIED | NOTIFIED_UNCONFIRMED, r))` — CLTR-ORDER-6, F10.
4. **Marker cannot independently establish completion.** `terminal(r) := f(r.spine_state)`, never `f(marker.exists)` — CLTR-MARKER-2.
5. **Stale marker rejected.** `marker.digest_ref ≠ digest(r) ⇒` marker is treated as a regenerate-signal, never as still-valid evidence (§19.2 item 7).
6. **Fabricated marker rejected.** `marker.transition_id` resolves to no known record, or `marker.digest_ref` does not match any known record's digest, `⇒` marker is rejected outright, never trusted as evidence a transition occurred (§19.2 item 8).
7. **Marker surviving supersession cannot establish current state.** `r.superseded == True ⇒` any marker still bound to `r` is not treated as describing the *current* state of `phase(r)` — the consumer must additionally check `r.superseded` (a **non-blocking** completeness note also raised independently by 135C §22, re-confirmed here: the general binding + supersession mechanisms compose correctly without a special-cased marker rule).
8. **Missing marker does not erase certified canonical history.** `¬∃ marker(r) ⇒ terminal(r)` is still computable directly from `r.spine_state` — marker absence degrades performance (a slower resume path that must read the record directly), never correctness (§19.2 item 6).
9. **Marker repair cannot replay irreversible stages.** Regenerating a marker is a **derivative-only** operation (§8.1's classification) — it never re-triggers T8 (notification dispatch) or any earlier irreversible operation.

---

## 23. Receipt invariants

1. **Receipt binds the exact transition.** `receipt.transition_id == r.transition_id` (§20.2 item 1).
2. **Receipt binds report and metadata generation.** `receipt.report_id == r.report_id`, `receipt.metadata_id == r.metadata_id` (§20.2 items 2–3).
3. **Receipt binds phase commits.** `receipt.commit_ownership_ref == r.declared_commits` at the time of receipt (§20.2 item 4).
4. **Receipt accurately reflects promotion.** `receipt.promotion_outcome == (r.spine_state ≥ PROMOTED)` (§20.2 item 5).
5. **Receipt accurately reflects notification.** `receipt.notification_outcome == (r.spine_state ∈ {NOTIFIED, NOTIFIED_UNCONFIRMED})` (§20.2 item 6).
6. **Receipt accurately reflects marker persistence.** `receipt.marker_outcome == (marker(r) successfully derived)` (§20.2 item 7).
7. **Incomplete stages remain incomplete.** `receipt.claimed_stages ⊆ r.actually_reached_stages` — CLTR-ORDER-7, restated per-receipt.
8. **Optimistic success prohibited.** `receipt.outcome == confirmed ⇒ r.spine_state == NOTIFIED` strictly — never asserted for a record still at NOTIFYING or only reaching NOTIFIED_UNCONFIRMED (CLTR-RECEIPT-1, §20.3).
9. **Complete receipt implies required prior stages.** `receipt.terminal_classification == TERMINAL_SUCCESS ⇒ r.spine_state == TERMINAL_SUCCESS` (and transitively, every stage T1–T9/T13 was actually reached) (§20.2 item 8).
10. **Best-effort-incomplete receipt has deterministic terminal and repair semantics.** `receipt.best_effort_incomplete == True ⇒ r.spine_state == NOTIFIED_UNCONFIRMED`, and the only permitted repair path is T12 (reconciliation), never T8/T9 re-entry (§20.2 item 9, §16.3 of CLTR-001).

---

## 24. Retry and resume state machine

Complete matrix, covering invocation at every retained state (source: CLTR-001 §16.3, independently re-verified complete by 135C §19).

| State at re-entry | New invocation must | T-row(s) involved |
|---|---|---|
| PROPOSED (no durable footprint yet) | **Begin** — retry from scratch, no side effects to account for | T1, T2 |
| CERTIFYING (crash mid-attempt, no CERTIFIED reached) | **Begin** (equivalent to PROPOSED — nothing sealed yet) | T2, T3/T4 |
| CERTIFIED, PROMOTING not yet started | **Continue** — proceed to PROMOTING; sealed evidence remains valid, no re-certification | T5 |
| PROMOTING started, outcome unknown (crash mid-stage) | **Resume**, but only after an explicit **observation step** (never assume; check actual external state first) | Observation event, then T6/T7 |
| PROMOTED | **Continue** — PROMOTING never re-attempted; only NOTIFYING may proceed | T8 |
| NOTIFYING started, outcome unknown | **Resume**, same observation discipline as PROMOTING | Observation event, then T9/T10 |
| NOTIFIED | **Return prior result** — reject any further spine transition; regenerate derivatives only | T13 (if not yet closed), else no-op |
| NOTIFIED_UNCONFIRMED | **Repair derivative only** — retry receipt reconciliation (T12), never delivery; or accept T14 (close to TERMINAL_PARTIAL_EXTERNAL) | T12, T14 |
| TERMINAL_SUCCESS | **Return prior result** — reject ordinary replay (CLTR-RETRY-2) | None (terminal) |
| TERMINAL_PARTIAL_EXTERNAL | **Return prior result** — reject ordinary replay; receipt reconciliation no longer applies once this closure has occurred | None (terminal) |
| FAILED_PRE_CERT | **Begin** — a wholly new PROPOSED record, freely, no side effects occurred | T1 (new record) |
| FAILED_POST_CERT | **Resume**, but only via a **new** record, and only after the observation discipline (never retry this record's own PROMOTING) | Observation event, then new T1 |
| QUARANTINED (orthogonal, any underlying spine state) | **Require human review** — no invocation may proceed past this flag automatically | None until cleared |
| SUPERSEDED (orthogonal, any underlying spine state) | **Reject** ordinary replay — direct to the superseding record | None (redirect) |
| Ambiguous case: recorded state alone cannot determine the correct outcome | **Quarantine** and require human review — never guess (CLTR-001 §17.9's final row) | T15 |

**Core ownership.** Every row above is a decision the **record's own resume logic** owns (CLTR-001 §16.1, CLTR-SAFE-3) — entry-point-specific marker checks may remain **compatibility accelerators only** (a fast local check that agrees with the record and skips re-reading it, per §19.1's "replay accelerator" role), never the primary decision-maker. This is the exact structural requirement CLTR-RETRY-1 exists to make binding, and the exact place today's implementation (Gap A, §0) still fails: current entry points' marker checks *are* the primary decision-maker, with the transaction's own resume logic as a secondary, incomplete check — the reverse of what this matrix requires. This is not repaired here; it is the precise target for a future implementation phase (135E+).

---

## 25. NOTIFIED_UNCONFIRMED formalization

Per the assignment's explicit instruction, this state is re-modeled adversarially against CLTR-001 as authority, not against 135B's or 135C's own framing.

1. **Is the event known to have occurred, or only known to have been attempted?** Independently re-confirmed against current source (§0 item 1's neighborhood, `finalization_transaction.py`'s post-dispatch receipt modeling): today's actual mechanism reads `notification_result.success` from the **real, promoted** report — never a pre-promotion trial. This means, as currently implemented, reaching this state implies delivery **did occur** (confirmed, not merely attempted) — only the receipt-modeling/persistence bookkeeping step failed afterward. CLTR-001 §7.3's hedge ("delivery occurred, **or is believed to have occurred**") is defensible as forward-looking generality (a future, different delivery mechanism might reach this state via a genuinely less-certain path), but as applied to today's actual mechanism specifically, "believed" understates the certainty. This is 135C finding #1, independently re-confirmed still accurate by this phase's own source re-check (§0 item 1's neighborhood), not merely inherited.
2. **Evidence unavailable case.** If the underlying delivery-confirmation evidence is itself unavailable (a hypothetical future delivery mechanism with genuine uncertainty, distinct from today's "confirmed occurrence, incomplete bookkeeping" mechanism), CLTR-001's hedge already accommodates it — this document does not need to invent new contract text, only to note the state's definition currently conflates two distinguishable sub-cases (confirmed-occurrence-incomplete-bookkeeping vs. genuinely-uncertain-occurrence) under one name.
3. **Is duplicate dispatch forbidden?** Yes, absolutely — CLTR-NOTIFY-2, F6: no path from NOTIFIED_UNCONFIRMED re-enters NOTIFYING. This is unaffected by the sub-case distinction in item 1/2 above.
4. **Is receipt completion repairable?** Yes, narrowly — T12 (reconciliation) is the only repair path, and it repairs *bookkeeping*, never delivery.
5. **Is marker creation allowed?** Yes — CLTR-ORDER-6 permits marker creation once NOTIFIED_UNCONFIRMED is reached (it is one of the two states, alongside NOTIFIED, that satisfy the marker's creation-timing precondition).
6. **Is the state terminal for ordinary completion?** Yes — terminal for the purposes of re-attempting PROMOTING or NOTIFYING (CLTR-RETRY-1's exact classification). Not terminal in the sense of "no further event can ever be appended" — T12 (reconciliation) and T14 (close to TERMINAL_PARTIAL_EXTERNAL) both remain available.
7. **Does a constrained confirmation-recovery transition exist?** Yes — T12, explicitly scoped to receipt-modeling reconciliation only, never delivery retry.
8. **Is human review required?** Only if reconciliation (T12) itself cannot resolve within a bound (§4's NOTIFIED_UNCONFIRMED row, "Human review: Only if reconciliation fails repeatedly") — not required merely by virtue of reaching this state, since (per item 1) the underlying delivery is not actually in doubt under today's mechanism.
9. **Does it map to TERMINAL_PARTIAL_EXTERNAL?** Yes, via T14, once reconciliation is abandoned or exhausted — this is the state's designated terminal closure (CLTR-001 §7.3).

**Disposition:** CLTR-001's classification of NOTIFIED_UNCONFIRMED is **CONFIRMED sound** — re-derived independently, not merely trusted. The one genuine refinement this phase identifies (item 1's naming-precision gap, restating 135C finding #1) is **not resolved here**: this document does not amend CLTR-001's text. It is recorded as a **candidate future amendment**, specifically: a future contract revision (CLTR-001 v1.1 or a schema-phase clarification) could split the state's definition into two named sub-conditions — "delivery-confirmed, receipt-incomplete" (today's actual mechanism) and a hypothetical "delivery-uncertain" (a future, different delivery mechanism's possible failure mode) — without changing any of items 3–9's behavioral requirements, which are identical under either sub-condition. **This is unavoidable to fully resolve without touching CLTR-001's own text, so it is documented as a candidate amendment, not silently repaired or left unaddressed.**

---

## 26. Duplicate and replay state machine

Every case produces exactly one deterministic transition result (source: CLTR-001 §17.1–§17.9, independently re-verified complete by 135C §20).

| Case | Deterministic result | T-row / mechanism |
|---|---|---|
| First ordinary completion | Proceeds normally through T1→T13 (or T14) | Full spine |
| Exact replay (same evidence, CERTIFIED-or-later, no newer record exists) | **Return prior result** — resolves to the existing record's current state | Idempotent re-entry (§17.1) |
| Duplicate ordinary completion (new PROPOSED for an already-terminal phase/task) | **Reject** at PROPOSED, referencing the existing terminal record | CLTR-RETRY-2 |
| Conflicting replay (evidence differs from an existing CERTIFIED-or-later binding, same `transition_id`) | **Reject** — never silently overwritten | §17.4, CLTR-PERSIST-2 |
| Cross-phase replay (evidence/identifiers resolve to a different phase than declared) | **Reject** at identity resolution (T1/T2), never accepted under the submitting transition's claimed identity | §17.5, CLTR-ID-2 |
| Retry after checkpoint (crash before PROMOTING begins) | **Continue** to PROMOTING; no re-certification | T5 |
| Retry after promotion (crash/re-submission after PROMOTED) | **Reject** re-promotion; only NOTIFYING may proceed or be retried | F13, T8 |
| Retry after notification (crash/re-submission after NOTIFYING begins, outcome unknown) | **Observe**, then decide (T9/T10), never blind retry | CLTR-RETRY-3 |
| Retry after marker | **Regenerate** the marker derivative; never re-trigger the underlying stage | §19, marker repair |
| Retry after receipt (complete) | **No-op** — folded into NOTIFIED's own terminal-for-resume classification | Implicit in T13 |
| Retry after best-effort incomplete receipt | **Reconcile** (T12) or **accept** TERMINAL_PARTIAL_EXTERNAL (T14) — never bare retry of delivery | T12, T14 |
| Replay after supersession | **Reject**, referencing the superseding record | §17.8, F8 |
| Replay with changed commit ownership | **Reject** as conflicting replay (subsumed under §17.4's field-agnostic framing, independently re-confirmed sound by 135C §20 — no combinatorial enumeration of which field differs is needed) | §17.4 |
| Replay with changed report digest | **Reject** as conflicting replay, same mechanism | §17.4 |
| Replay with changed metadata digest | **Reject** as conflicting replay, same mechanism | §17.4 |

**Determinism confirmed:** every row above names exactly one required system behavior — no case is left as "implementation's choice," matching 135C §20's own finding and independently re-verified here at the state-machine layer specifically (not merely the contract-text layer).

---

## 27. Failure-state architecture

For each failure class (source: CLTR-001 §18.1, independently re-verified complete and non-overlapping by 135C §21):

| Failure class | Resulting state | Canonical-state effect | Derivative effect | External visibility | Retryable | Quarantine requirement | Human-review requirement | Evidence retained |
|---|---|---|---|---|---|---|---|---|
| Missing authority (declared identity/evidence don't resolve) | Rejected pre-PROPOSED | None durably recorded | None | No | Yes, freely | No | No, unless repeated | Rejected proposal |
| Identity conflict (ambiguous/malformed ID) | Rejected pre-PROPOSED | None | None | No | Yes, freely | No | No, unless repeated | Malformed input |
| Commit ownership conflict (contaminated/unverifiable) | Partial — outcome noted; T3 may proceed or block per deferred policy | Depends on policy | Depends on policy | Depends on policy | Yes, freely if pre-CERTIFIED | Yes if unverifiable and policy treats it as suspicious | Yes if unverifiable and policy treats it as suspicious | Hash + resolution attempt |
| Projection conflict (deterministic projection cannot be computed) | FAILED_PRE_CERT | None | None | No | Yes, freely | No | No, unless repeated | Contradiction detail |
| Semantic mismatch (sealed evidence contradicts declared identity) | FAILED_PRE_CERT | None | None | No | Yes, freely | No | No, unless repeated | Contradiction detail |
| Certification failure (rendering/composition exception) | FAILED_PRE_CERT | None | None | No | Yes, freely | No | No, unless repeated | Exception detail |
| Checkpoint failure (durable write itself fails) | Ambiguous, resolved by durability guarantees (§8) | Depends on prior durable state | Depends | No, if write never completed | Yes | No | Yes if durability cannot be confirmed on restart | Partial write, for forensic inspection |
| Promotion failure | FAILED_POST_CERT | CERTIFIED evidence remains sealed | Possibly affected if partial promotion occurred | Possibly Y | Only via new record, never re-running this record's PROMOTING | Yes, if partial external state is ambiguous | Yes | Full CERTIFIED evidence + observed partial-promotion state |
| Atomic pointer failure (mixed-generation exposure) | None to the record | Y — a derivative was wrong, must be regenerated | Y | N/A — regenerate | No, unless already externally delivered | Only if externally delivered | Which record the stale derivative actually matched |
| Notification failure (delivery itself fails) | Record notes NOTIFYING failed | — | Y — delivery genuinely did not happen | Yes, retry NOTIFYING (T11) for the same PROMOTED record | No | Only if repeated | Delivery attempt evidence |
| Notification uncertainty (delivery outcome unknown, crash mid-NOTIFYING) | Requires observation before deciding | — | N/A pending observation | N/A pending observation | Yes, after observation | No, unless observation itself cannot resolve | Only if observation cannot resolve | Whatever partial evidence exists |
| Marker failure (marker write fails) | None to the record | N to record; Y to marker-dependent legacy readers until regenerated | N to record | Yes — regenerate from record | No | No, unless marker can never be regenerated | Record itself remains source of truth regardless |
| Receipt failure (best-effort modeling incomplete) | NOTIFIED_UNCONFIRMED | — | N — underlying delivery already succeeded | Retry receipt modeling only (T12), never delivery | No | Only if receipt can never be reconciled | Delivery evidence that did succeed |
| Digest failure (record's bound evidence no longer matches its digest) | None — record content not rewritten | Y — flagged, not silently trusted | Y | N/A | Yes, always | Yes, always | Mismatch details, both digests |
| Stale derivative (regenerated from an older record than the current pointer) | None to the record | Y — the derivative is wrong | Y | N/A — regenerate | No, unless externally delivered | Only if externally delivered | Which record the stale derivative matched |
| Cross-phase substitution | None if caught at CERTIFYING (rejected); Y if caught later (quarantine) | Y once discovered | Y once discovered | Depends on when caught | Yes if discovered post-hoc | Yes, always | Substitution details |
| Repository final-state mismatch (V-role fact no longer matches at a later read) | None to the historical binding | N/A | Y — flagged as stale, never silently current | N/A — re-measure | No, unless the mismatch is itself suspicious | The measured-at-certification value, retained as historical fact |
| Compatibility-adapter failure (a legacy-adapter-classified mechanism itself malfunctions, e.g., today's marker-only check missing a case) | Depends on which underlying mechanism failed — routed to the corresponding row above | Depends | Depends | Depends | Depends | Only if the adapter failure masks a genuine record-level failure | Adapter failure detail, plus whatever the record itself shows independently |

No failure class above lacks a defined resulting state and canonical-state effect — cross-checked exhaustively against §4's per-state table and §5's transition inventory, closing the loop the assignment requires (every failure class traces to a named state, T-row, or explicit "orthogonal/pending" classification).

---

## 28. Conformance state mapping

Mapping lifecycle states and invariant outcomes to CLTR-001's seven conformance states (§30.1), independently re-verified complete, mutually exclusive (where required), and deterministic by 135C §33.

| Conformance state | Determined by | Deterministic classification? | Mutually exclusive? |
|---|---|---|---|
| `conformant` | Every Blocking invariant (§11's 36) holds; no forbidden pattern (§6, CLTR-001 §4.2) present | Yes — a pure evaluation of §11 against record content | Yes, with respect to `conflicting`/`quarantined`/`superseded` |
| `conformant_with_legacy_adapter` | §11's invariants hold, but one or more consuming entry points still use an adapter mechanism (§29 below) rather than the record directly | Yes | Yes, distinct from plain `conformant` — this is today's actual and only reachable state, since no implementation of CLTR-001 exists yet (§0 item 5) |
| `incomplete` | Required fields/evidence bindings missing for a pre-CERTIFIED record | Yes — not itself a violation | Yes, distinct from `unverifiable` (which applies CERTIFIED-or-later) |
| `conflicting` | Two representations of the same `transition_id` disagree on an S/D-role fact | Yes — always a CLTR-AUTH-1 violation | Yes, distinct from `quarantined` (detection vs. resulting flag) |
| `unverifiable` | A verification pass cannot resolve whether a fact is conformant (e.g., commit-ownership per §17, or a digest that cannot be recomputed) | Yes — recorded as its own outcome | **May coexist with TERMINAL_SUCCESS** (§28.1 below) — a disclosed, intentional design choice, not a hidden contradiction (135C §33) |
| `quarantined` | Flagged by independent integrity verification (T15), pending human review | Yes | Yes |
| `superseded` | A later correcting transition record exists (T16) | Yes | Yes |

### 28.1 Does `unverifiable` coexist with authoritative completion?

**Independently re-confirmed, not merely inherited:** the contract does not forbid a TERMINAL_SUCCESS record from simultaneously carrying an `unverifiable` conformance classification for its commit-ownership fact — CLTR-001 §10.4 explicitly defers whether `unverifiable` blocks completion (T3), which is a distinct question from whether the *transition itself* eventually reaches TERMINAL_SUCCESS via T9→T13. This document's own §17.1 restates the same deferred-policy structure. **Not a contradiction**: `unverifiable` (a conformance-evaluation answer to "can every fact currently be verified") and TERMINAL_SUCCESS (a spine-state answer to "did this transition complete") answer two different questions, and nothing in §5's transition inventory makes T3's success conditional on `unverifiable` being absent — only on `unverifiable` being *distinctly classified*, which it always is (CLTR-COMMIT-2/3).

### 28.2 Whether legacy adapter conformance can ever be authoritative

**No.** `conformant_with_legacy_adapter` is itself a **derived classification** (CLTR-001 §30.2) computed by evaluating §11's invariants — it never grants the adapter mechanism itself (e.g., a marker-only resume check) any authority beyond what §14 (authority invariants) and §24 (retry/resume matrix) already assign it (compatibility accelerator only). The "legacy adapter" qualifier is a disclosure about *migration completeness*, not a grant of authority to the adapter mechanism.

### 28.3 Whether `conflicting` must always block certification or promotion

**Yes, for T3 specifically.** A `conflicting` classification means two representations disagree on an S/D-role fact — this is always a CLTR-AUTH-1 violation, and CLTR-AUTH-1 is Blocking. T3 (`certify`) requires CLTR-AUTH-1 to hold (§11's evaluation-inputs column); a record with an unresolved `conflicting` classification cannot legitimately reach CERTIFIED. This is not a new rule — it follows deterministically from §11's already-established Blocking severity for CLTR-AUTH-1, restated here at the conformance-mapping layer for completeness.

---

## 29. Compatibility-state architecture

Legacy artifact classification (source: CLTR-001 §24.1, re-verified unchanged by 135C §27; re-confirmed live in this phase's own §0 source re-check):

| Legacy artifact/mechanism | Classification | Rationale |
|---|---|---|
| Historical reports without transition IDs | Verification-only | Predate any record; remain valid, immutable, readable |
| Historical completion metadata | Verification-only | Same |
| Existing Architecture Status (current generation mechanism) | Adapter | Continues generating from PROJECT_STATUS.md + projected-state seal until a future phase migrates it to read records directly; the title-extraction bug (§30 below) is a defect *within* this adapter, not evidence the adapter classification itself is wrong |
| Current immutable snapshots | Native | Architecturally the direct ancestor of CERTIFIED-state sealing; extension, not replacement |
| Current checkpoints (`.pcae/finalization-transactions/*.json`) | Adapter | Existing atomic temp-file+`os.replace` pattern already satisfies §8's durability requirements without modification |
| Current `latest.md`/`latest.json` | Adapter, and specifically **incomplete** relative to §20's atomic-visibility invariants (Gap B, §0) | Confirmed still non-atomic (three plain `write_text()` sites); remains as-is until a future phase resolves §20's mechanism choice |
| Current `.last-notified.json` marker | Deprecated as authority / Derived as cache | §22 |
| Current `.pcae/delivery-receipts/` | Native | Already architecturally sound (immutable, atomic); becomes bound to the record via reference |
| Current Git attribution (`detect_cross_phase_commit_contamination`) | Adapter, and specifically **incomplete** relative to §17 item 10/CLTR-COMMIT-3 (Gap C, §0) | Confirmed still silently `continue`s past unresolvable hashes |
| Current entry-point marker checks (4 independent, per-entry-point) | Retirement candidate (long-term) / Compatibility-only (short-term) | Confirmed still the sole mechanism providing Gap-A safety today (§0 item 4); this is the central retirement target of a future implementation phase, not this one |

Historical artifacts remain immutable (CLTR-COMPAT-1) regardless of classification — verification-only status does not permit rewriting, only reading.

---

## 30. Architecture Status grouping observation

Independently investigated per the assignment's specific instruction, not assumed to be either a defect or a non-issue.

**Re-confirmed via live output in this session's §0 initial inspection** (`pcae phase-report show --latest`): the "Whole-Lifecycle Independent Verification (135A–135C, 3 phases)" label did **not** recur in this session's own bootstrap/inspection output (the latest report correctly lists 135A/135B/135C as separate `✓` completed-milestone lines and 135D as the sole `○` planned item) — the specific mislabeling instance 135C root-caused (135C §25.2: a title-extraction regex cross-attributing 134F's title onto the 135A/135B chapter grouping) is **not currently reproducing** in this session's `pcae phase-report show --latest` output, because 135C's own completion has since shifted which phases land in the affected regex window. This does not mean the underlying defect is fixed — §0's source re-check did not re-verify `phase_reports.py`'s title-extraction regex itself (unchanged since 135C's root-causing; no source file has been touched since), so the defect class remains live in the source, merely not currently manifesting in *this specific* rendered instance because the input window shifted.

Answering the assignment's determination questions, per this phase's own independent check:

- **Is grouping metadata stale?** No — chapter/track membership (135A, 135B, 135C all correctly under chapter "135") is correct.
- **Is milestone naming imprecise?** Where the bug manifests, it is not "imprecise" — it is factually wrong (a cross-attributed title from an unrelated, already-completed phase). Where it does not currently manifest (this session's own output), no naming defect is visible.
- **Is phase-range grouping derived from the wrong architectural chapter?** No — the chapter assignment itself (135-prefix grouping) is correct; only the *label string*, when the bug manifests, is wrong.
- **Do current active/completed/planned semantics remain correct?** Yes — independently re-confirmed via §0's `pcae phase-report show --latest`: `completed_phase_ids` correctly includes 135A/135B/135C; `Planned` correctly lists only 135D; no lifecycle-state fact is affected by the label bug, consistent with 135C's own finding.
- **Is the issue editorial only?** Yes, when it manifests — a display-string defect, never a lifecycle-authority defect (135C §25.2's finding, re-confirmed unchanged: the underlying `phase_reports.py` regex has not been touched by any phase since 135C root-caused it).
- **Is a cross-representation invariant needed for chapter identity or milestone grouping?** **Yes, narrowly** — CLTR-ORDER-5 (§11, this document) already covers the general case ("no post-certification mutable read may redefine the transition") and directly forbids the *mechanism* of this bug class (reconstructing a title by adjacent-text inference instead of reading a bound identity/title pair) for any future record-derived Architecture Status. No **additional** invariant beyond CLTR-ORDER-5/CLTR-AUTH-2 is required — a dedicated "chapter-label invariant" would be redundant with the no-independent-reconstruction principle already governing all derivatives.
- **Does the issue belong outside CLTR?** The *underlying implementation defect* (a Track 134-era title-extraction regex in `phase_reports.py`) belongs outside CLTR-001's own text — it predates any record and is not itself lifecycle-authority-relevant. The *invariant that would prevent recurrence once a record exists* is squarely inside CLTR's scope (CLTR-ORDER-5, CLTR-AUTH-2) and is already covered.

**Not repaired here** (consistent with this phase's non-goals). **Classification: non-blocking editorial/implementation debt, already covered by an existing invariant for any future record-based regeneration; not a gap in CLTR-001's own invariant set.**

---

## 31. Temporal model

Timestamp and sequencing semantics (source: CLTR-001 §6.2 item 25, §23; 135C finding related to the "hybrid" event-plus-state model, §37 below).

| Event | Authoritative timestamp source | Ordering expectation | Monotonicity | Clock-skew handling | Deterministic replay behavior | Semantic or observational? |
|---|---|---|---|---|---|---|
| Transition creation (T1) | Declaring process's own clock at PROPOSED | First in the record's own history | Strictly before every later event in this record | N/A (single-writer per record) | Replaying T1 with identical inputs produces the same logical event, timestamp aside | Observational (the timestamp is metadata; identity/evidence bindings are the semantic content) |
| Validation (part of T3's precondition) | Certification process's clock | After creation, before certification | Monotonic within the record | N/A | Deterministic given the same evidence | Observational |
| Certification (T3) | Certification process's clock, at the moment digest is fixed | After validation | Monotonic; this is the record's own "certified" timestamp field (CLTR-001 §6.2 item 25) | N/A | The *decision* (pass/fail) is deterministic; the timestamp itself is not reproduced identically on replay, and is not required to be | Observational timestamp, but the certified/not-certified *fact* is semantic |
| Checkpoint (durability mechanism, not a separate semantic event per §7.4/§8.3) | Same as certification — checkpoint timestamps the durability of CERTIFIED, not a distinct stage | Concurrent with or immediately after certification | Monotonic | N/A | N/A — not a separate event to replay | Observational |
| Promotion (T5→T6) | Promotion process's clock | After certification | Monotonic | N/A | The promotion *outcome* is deterministic given the same CERTIFIED input; the timestamp is not | Observational |
| Notification attempt (T8) | Dispatch process's clock | After promotion | Monotonic (may repeat via T11, each attempt separately timestamped) | N/A | Each attempt is its own event; replay does not collapse multiple attempts into one | Observational |
| Notification result (T9/T10) | The delivery sink's own confirmation, read back from the real promoted report (never a pre-promotion trial, §25 item 1) | After the corresponding attempt | Monotonic | External sink's clock may differ from local clock — this is why the record binds *its own* observation timestamp, not the sink's, as authoritative for ordering purposes | Deterministic given the same sink response | Semantic for the confirmed/unconfirmed *fact*; observational for the exact timestamp value |
| Marker persistence | Marker-write process's clock | After NOTIFIED/NOTIFIED_UNCONFIRMED (CLTR-ORDER-6) | Monotonic | N/A | Regenerable at any later time with a fresh timestamp — the marker's *content* correctness does not depend on timestamp exactness | Observational |
| Receipt persistence | Receipt-modeling process's clock | After the stage(s) it attests to (CLTR-ORDER-7) | Monotonic | N/A | Deterministic given the same record state | Observational timestamp; semantic claimed-stages content |
| Final repository observation (§7.5's terminal extension) | Live `git rev-parse`/`git status` at the observation moment | After the record's own finalization commit, if any | Not monotonic relative to the record's other internal events (it may occur an arbitrary, bounded time after CERTIFIED) — but is itself a single, well-ordered append | N/A (single observer per observation event) | The observation is inherently non-replayable (it measures live state) — but its *binding* into the record's history is deterministic and append-only | Observational, explicitly (CLTR-001 §23.1's V-role classification) |
| Supersession | The superseding record's own creation timestamp | After the superseded record's own terminal closure | Monotonic relative to the superseded record | N/A | Deterministic — supersession is a fact about which record is later, not a replayable computation | Semantic (which record supersedes which is authoritative); observational for exact timestamp |

**Clock-skew handling, generally:** every timestamp in this model is bound as a fact about *when this record's own process observed the event*, never as a claim about universal wall-clock truth reconcilable across distributed writers — this repository's governed workflow is single-agent-lock-serialized per `pcae health`'s "Agent lock: held by \<agent\>" model (§0), so cross-process clock reconciliation is out of scope for this document (no concurrent-writer scenario exists under current governance to necessitate it).

**Deterministic replay, generally:** every event whose *content* (not timestamp) is semantic is required to be reproducible from the same inputs (CLTR-DERIVE-1/2); no event's timestamp is ever treated as part of the content that must reproduce identically on replay — this is the precise boundary between "semantic" and "observational" columns above.

---

## 32. Final-revision staged binding verification

Formal re-verification of CLTR-001 §23.4's staged-binding model, independently re-derived rather than trusted (135C §26 already performed one independent pass; this section re-checks it once more, specifically for state-machine circularity, since that is this phase's specific charter).

1. **Which revision is known before certification (T3):** `source_revision` — known at PROPOSED (T1), before any of this transition's own commits exist. Correctly bound S+V per CLTR-001 §3.2.
2. **Which revision becomes known after lifecycle persistence:** `final_revision`, when a finalization commit is itself required for this transition's own artifacts to be considered final (the common case for this repository's own governed phases — this very phase's eventual finalization commit is an instance, §41).
3. **Is a terminal extension required?** Yes, whenever `final_revision` cannot be core-bound at CERTIFIED (§7.5 above) — the terminal verification event (not a T-numbered spine transition; an append to the record's own history) resolves it once the finalization commit is made and independently confirmed.
4. **How does the extension bind to the certified core record?** By reference only — the terminal verification event carries the record's own `transition_id` and appends a new, dated fact ("final_revision = X, confirmed via live `git rev-parse` at time T") without reopening, re-sealing, or changing the digest of the CERTIFIED record itself (CLTR-001 §14.1 item 1's append-only model).
5. **May terminal observations alter canonical lifecycle status?** No — resolving `final_revision` from provisional to actual never changes `record.spine_state`; it is orthogonal to whether T9/T10/T13/T14 have occurred (independently re-confirmed non-circular in 135C §37: commit-ownership verification at CERTIFYING operates against the transition's *substantive* commits, already bound before CERTIFIED, a distinct concern from the transition's *own* finalization commit).
6. **Does later repository mutation affect historical truth?** No — per §7.2/§19 (evidence invariants), a V-role binding remains historically true for what was observed *at that time*; a later mutation of the repository (e.g., a subsequent phase's commits) never retroactively changes what `final_revision` was correctly bound to for *this* transition.

**Avoiding circularity, formally:** the naive alternative — blocking CERTIFIED until the finalization commit exists — is circular: the commit cannot be validated as "this transition's own" until the transition is CERTIFIED (since commit-ownership declaration and verification, §17, occurs *at* CERTIFYING), but CERTIFIED cannot complete (under the naive alternative) until the commit is known. The staged-binding resolution breaks this cycle by allowing T3 to succeed with `final_revision` explicitly marked provisional, and resolving it later via a non-mutating append — never by making T3 wait on information that logically cannot exist before T3 itself resolves.

**First-hand corroboration, independently re-observed in this session:** this repository's own Track 135 phases (135A, 135B, 135C, and this phase's own eventual finalization, §41) are live, repeated demonstrations of exactly this circularity — each phase's own canonical report cannot state its true final `pushed`/`origin/main..HEAD` state until *after* the phase's own completion/metadata-sync commits are made, and 135B's own finalization required three metadata-repair cycles for exactly this reason (135C §26, re-confirmed here as still-accurate, unchanged history). This is strong, repeated, first-hand evidence that §23.4's resolution addresses a genuinely recurring problem in this repository's own governed workflow, not a hypothetical one.

**No impossible requirement found.** §23.4 item 4's "bounded grace period" leaves the *quantitative* value unspecified (a legitimate, narrow, non-blocking deferral, §37 #5) while the *qualitative* rule (TERMINAL_SUCCESS is blocked while `final_revision` remains unresolved past that bound) is fully specified and independently satisfiable regardless of the eventual numeric choice.

**Verdict: CONFIRMED — the circularity is genuinely resolved by the state machine's own structure (T3 succeeding with an explicit provisional marker, followed by a non-mutating terminal-extension append), not merely asserted to be resolved.**

---

## 33. State-machine determinism proof

**Claim:** given equivalent canonical authority inputs, repository identity, source revision, phase identity, task identity, commit ownership, evidence set, current transition state, and external outcome evidence, the state machine produces equivalent transition result, next state, derivative requirements, retry classification, conformance classification, and failure consequence — except explicitly approved observational timestamps (§31).

**Proof sketch, by structural induction over §5's transition inventory:**

*Base case (T1, `propose_transition`):* given identical declared identity and evidence-reference inputs, T1 either succeeds (producing a PROPOSED record with identical identity/evidence content, timestamp aside) or is rejected (identical rejection, per identical failed preconditions) — no branch of T1 depends on anything other than its declared inputs (§5's "Preconditions"/"Required evidence" columns list only declared, input-equivalent facts).

*Inductive step:* assume every transition T1..T(n-1) is deterministic given equivalent inputs. Transition T(n)'s preconditions (§5) are themselves defined only in terms of: (a) the prior state reached by T1..T(n-1) (deterministic, by inductive hypothesis), (b) the record's own already-bound, input-equivalent fields (§4, §7), and (c) — for exactly the transitions named below — an external observation event. Every non-observation-dependent transition (T1–T6, T8, T9 (given confirmed evidence), T13, T15, T16) is therefore deterministic by the inductive hypothesis plus §11's CLTR-DERIVE-1 (pure-function requirement on every derivation the transition's preconditions consult).

*Observation-dependent transitions (T7, T10, T12, and the "resume after crash" rows of §24):* these consult external outcome evidence (§33's own claim explicitly includes this as an equivalence input) — given equivalent external outcome evidence, the observation step itself is required (CLTR-RETRY-3) to produce an equivalent classification, and the subsequent transition choice (T7 vs. T6, T10 vs. T9, T12's reconciliation outcome) is then determined by that equivalent classification, not by anything unbound.

*Conclusion:* by induction, every transition in §5, and therefore every path through the state machine (§4's full per-state definitions), is deterministic given equivalent inputs across all nine named equivalence classes, with observational timestamps (§31) as the sole, explicitly bounded exception.

### 33.1 Permitted sources of nondeterminism

Exhaustively enumerated (matching §31's semantic/observational boundary exactly — no permitted nondeterminism source appears here that was not already named in §31 or §8's V-role classification):

1. Event timestamps (transition creation, certification, promotion, notification attempt/result, marker/receipt persistence, final observation, supersession) — observational only, never affecting which state is reached or what content a derivative carries.
2. The exact wall-clock value bound into a V-role fact (repository cleanliness, pushed state, `origin/main..HEAD`) — the *fact that a measurement occurred and its value at that moment* is deterministic given the actual repository state at that moment; the repository state itself is external to this state machine and is not claimed to be deterministic (it is real-world state, not a derived value).
3. Which of several structurally-equivalent internal representations a future implementation chooses for a given derivative's storage (e.g., JSON key ordering) — explicitly bounded by CLTR-001 §15.1 item 1's canonicalization requirement, which exists precisely so this class of nondeterminism never affects the digest or any Blocking invariant evaluation.
4. Notification/promotion identifiers (`notification_id`, `promotion_id`) that are generated fresh per attempt — these are identity values, not decision outcomes, and their generation scheme (deferred to schema work) is explicitly out of this document's scope; no invariant in §11 depends on a *specific* generated ID value, only on internal consistency of whichever value is chosen (CLTR-ID-1).

No other nondeterminism source is permitted. In particular, **the actual external outcome of promotion/notification/reconciliation itself is not "nondeterminism" in the sense this proof excludes** — it is an explicit equivalence-class input (§33's own claim); the state machine's *response* to a given outcome is deterministic, even though the real world's *production* of that outcome (did the network request actually succeed) is not something this document's proof claims to control.

---

## 34. Reachability analysis

For every state, reachability is determined against §5's transition inventory (source/target pairs).

| State | Reachable? | Legal predecessor(s) | Legal successor(s) | Dead-end non-terminal? | Ambiguous predecessor? |
|---|---|---|---|---|---|
| PROPOSED | Yes (initial) | (none — entry point) | CERTIFYING (T2), or rejected | No | No |
| CERTIFYING | Yes | PROPOSED (T2) | CERTIFIED (T3), FAILED_PRE_CERT (T4) | No | No |
| CERTIFIED | Yes | CERTIFYING (T3) | PROMOTING (T5) | No | No |
| PROMOTING | Yes | CERTIFIED (T5) | PROMOTED (T6), FAILED_POST_CERT (T7) | No | No |
| PROMOTED | Yes | PROMOTING (T6) | NOTIFYING (T8) | No | No |
| NOTIFYING | Yes | PROMOTED (T8), NOTIFYING itself (T11 retry) | NOTIFIED (T9), NOTIFIED_UNCONFIRMED (T10) | No | No |
| NOTIFIED | Yes | NOTIFYING (T9) | TERMINAL_SUCCESS (T13) | No | No |
| NOTIFIED_UNCONFIRMED | Yes | NOTIFYING (T10) | TERMINAL_PARTIAL_EXTERNAL (T14), self via T12 (reconciliation, non-consuming) | No | No |
| TERMINAL_SUCCESS | Yes | NOTIFIED (T13) | (none — terminal; only orthogonal QUARANTINED/SUPERSEDED apply) | No (terminal by design) | No |
| TERMINAL_PARTIAL_EXTERNAL | Yes | NOTIFIED_UNCONFIRMED (T14) | (none — terminal; only orthogonal QUARANTINED/SUPERSEDED apply) | No (terminal by design) | No |
| FAILED_PRE_CERT | Yes | CERTIFYING (T4) | (none — terminal; new record only) | No (terminal by design) | No |
| FAILED_POST_CERT | Yes | PROMOTING (T7) | (none — terminal-ish; new record only) | No (terminal-ish by design) | No |
| QUARANTINED (orthogonal) | Yes | Any CERTIFIED-or-later state (T15) | (human-review-gated exit only, not itself a spine successor) | N/A — orthogonal | No — always triggered by an independent verifier, never ambiguous about which record it flags |
| SUPERSEDED (orthogonal) | Yes | Any state (T16) | (none — annotation only) | N/A — orthogonal | No — always triggered by the existence of a specific later record |

**No unreachable states found.** **No dead-end non-terminal states found** — every non-terminal spine state has at least one legal successor (T-row) that either advances the spine or explicitly fails to a named, terminal-or-terminal-ish state. **No states with no legal predecessor found** except PROPOSED, which is correctly the sole entry point by design (a state machine must have exactly one entry, not zero). **No states with no legal successor found** except the six designed terminal/terminal-ish states (TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_PRE_CERT, FAILED_POST_CERT, and the two orthogonal states, which have no *spine* successor by design). **No ambiguous predecessors found** — every state's legal predecessor set (§5's "Source" column, inverted) is a small, explicitly named set, never "any prior state" without qualification. **No unsafe cycles found** — the only cycle in the graph is NOTIFYING→NOTIFYING (T11, notification retry) and NOTIFIED_UNCONFIRMED's self-loop via T12 (reconciliation) — both are explicitly **constrained-repair cycles** (never re-entering an earlier, already-exited stage; T11 only retries the same NOTIFYING attempt, T12 only retries receipt modeling), not unconstrained loops that could revisit CERTIFYING or PROMOTING.

---

## 35. Terminal-state analysis

For each of the six terminal/terminal-ish states (four spine-terminal plus the two orthogonal flags overlaying them):

| Terminal state | Ordinary completion prohibited? | Exact replay returns prior result? | Derivative repair permitted? | Notification retryable? | Marker repairable? | Receipt repairable? | Supersession possible? | Human review required? |
|---|---|---|---|---|---|---|---|---|
| TERMINAL_SUCCESS | Yes (CLTR-RETRY-2) | Yes | Yes (regeneration, byte-identical) | No | Yes (regenerate) | No (nothing to repair — fully confirmed) | Yes (via a later correcting transition) | No, unless quarantined |
| TERMINAL_PARTIAL_EXTERNAL | Yes | Yes | Yes (regeneration, with the gap disclosed) | No (delivery is not re-attempted; this closure already reflects that the delivery is believed to have occurred) | Yes (regenerate) | No (T12 only applies before this closure, not after) | Yes | Yes, always (the gap is a permanent disclosed feature of this closure) |
| FAILED_PRE_CERT | N/A — no side effects occurred, a wholly new record is not "resuming," it is beginning fresh | N/A (nothing to return — no durable content) | N/A | N/A | N/A | N/A | Not applicable in the usual sense (nothing to supersede — no successful content exists) | No, unless the same failure recurs suspiciously |
| FAILED_POST_CERT | Yes (this specific record) | N/A for this record — a **new** record must be created, per the observation discipline (§22, §24) | N/A for this record (CERTIFIED evidence remains sealed and valid, unaffected) | N/A for this record | N/A | N/A | Yes, via the new record that eventually succeeds | Yes |
| QUARANTINED (overlay) | Yes, until cleared | N/A while quarantined | No, pending review | No, pending review | No, pending review | No, pending review | N/A while quarantined | Yes, always — this is the defining property of the state |
| SUPERSEDED (overlay) | Yes — resolves to the superseding record | N/A — redirected | No (annotation only, content unchanged) | No | No (the superseding record's own marker is the live one) | No | N/A — this state *is* the supersession | Only if the supersession itself is disputed |

**Terminality is owned by the core state machine, not by any consumer.** Every column above is answerable purely from §4/§5/§24's already-established definitions — no terminal-state property in this table required consulting any entry-point-specific behavior, confirming CLTR-SAFE-3's requirement is structurally satisfiable by this model (though, per §0/§29, not yet actually satisfied by current implementation, which remains `adapter`-classified pending a future implementation phase).

---

## 36. Safety proof

Structured proof that this architecture preserves every governance boundary named by the assignment, re-checked independently against §4–§35's full model (not merely restated from CLTR-001 §28):

1. **No execution.** Every T-row in §5 records a *fact about* the finalization transaction's own existing call graph (`_build_pre_promotion_artifacts`, `promote_and_dispatch`, receipt modeling) — none of §5's "State mutation" column entries describes invoking a new capability; each describes recording that an existing, already-governed operation was attempted/succeeded/failed. **Confirmed no execution is introduced.**
2. **No backend invocation.** No T-row or invariant in §11 references any backend service, plugin, or capability beyond what `pcae runtime inspect` already reports as registered (zero plugins, zero capabilities, §0). **Confirmed.**
3. **No shell mediation.** No T-row involves shelling out to a new command; the only shell-adjacent operations referenced (`git log`, `git rev-parse`, `git status`) are the same read-only Git operations already used by current, already-governed source (§0, §17, §31). **Confirmed no new shell mediation.**
4. **No Telegram inbound.** §21 items 9–10 explicitly restate PFN-001's outbound-only guarantee; no T-row or invariant introduces any inbound path. **Confirmed.**
5. **No Decision Evaluation replacement.** Nowhere in §4–§27 does any state or invariant answer "should this transition be allowed to proceed" in a governance-policy sense — CERTIFIED/PROMOTED/NOTIFIED answer "what stage has this transition reached," strictly factual. The one deferred policy question this document touches (unverifiable commit ownership blocking, §17.1) is explicitly *not* resolved here, preserving the boundary rather than crossing it. **Confirmed.**
6. **No Repository Intelligence authority expansion.** This document's cross-representation model (§9) is scoped to one transition's lifecycle facts, never to a general repository knowledge store; §30's Architecture Status investigation explicitly classifies the underlying defect as outside CLTR-001's scope where it concerns Repository Intelligence-adjacent concerns. **Confirmed.**
7. **No execution authorization.** CLTR-SAFE-2 (§11) is independently re-tested here: every state's definition in §4 was checked for authorization-adjacent language ("may execute," "is approved to run") — none found. CERTIFIED/PROMOTING/PROMOTED describe lifecycle-record state, never permission state, matching 135C §31's own independent finding, re-confirmed here at the full state-machine-model layer (not only the contract-text layer). **Confirmed.**
8. **No mutation outside future lifecycle artifact persistence.** Every "State mutation"/"Derivatives created" cell in §5 names either an internal record-state change or the creation of an already-CLTR-001-scoped derivative (report, metadata, marker, receipt, notification payload) — no T-row mutates anything outside this scope (e.g., no T-row touches policy configuration, agent locks, or unrelated governance state). **Confirmed.**
9. **No derived artifact authority.** §14 (authority invariants) and §9/§10 (cross-representation model, representation-state matrix) jointly establish that every derivative is D-role or lower — never S-role. **Confirmed, and independently re-tested against the adversarial questions of §38 below.**
10. **No irreversible effect before certification.** CLTR-ORDER-4, §8's irreversibility classification, and §6's forbidden-transition inventory (F1, F2, F12) jointly and redundantly establish this — three independent mechanisms (an ordering invariant, an operation classification, and a forbidden-transition list) all agree, which is a structural strength (harder to accidentally violate) rather than an inconsistency. **Confirmed.**

**No governance boundary is loosened, narrowed, or reinterpreted by this document.** Every boundary listed above is preserved by construction, independently re-checked against this document's own full model rather than merely inherited from CLTR-001's text.

---

## 37. Deferred-question review

Every one of 135C's ten non-blocking deferred questions (135C §38 consolidated findings register) is dispositioned below. None is silently ignored.

| # | 135C finding | Disposition in 135D |
|---|---|---|
| 1 | NOTIFIED_UNCONFIRMED naming ("believed to have occurred") understates current-source certainty | **Constrained.** §25 formalizes the state fully, confirms the naming imprecision is real, and identifies exactly which sub-case (delivery-confirmed vs. genuinely-uncertain) today's mechanism actually falls into. Not resolved by renaming (that would require amending CLTR-001's frozen state name) — recorded as a **candidate future amendment** (§25's closing paragraph), not silently left unaddressed. |
| 2 | Three-outcome commit model doesn't explicitly address branch-reachability/rewritten-history | **Constrained.** §17 item 4 and §12.1 #1 classify this as an **implementation-level invariant** — the existing `unverifiable` outcome already accommodates it without any CLTR-001 text change; only a future verification procedure's evaluation-input list needs extension. Not promoted to Blocking (the taxonomy is already sufficient). |
| 3 | Architecture Status "135A-135B, 2 phases" mislabeled with 134F's title — pre-existing implementation defect, root-caused | **Constrained, re-classified as schema/implementation-level.** §30 independently re-investigates, confirms the defect is not currently manifesting in this session's own live output (input window shifted), confirms it remains live in source (untouched), and confirms CLTR-ORDER-5/CLTR-AUTH-2 already cover the invariant that would prevent recurrence in any future record-based regeneration. Not repaired; not promoted to Blocking. |
| 4 | `unverifiable` commit ownership may coexist with TERMINAL_SUCCESS depending on deferred policy | **Left deferred, explicitly re-affirmed.** §17.1, §28.1 both restate the deferral without resolving it — this is a governance-policy decision this phase's own non-goals forbid making. Confirmed non-blocking: no state-machine invariant is left ambiguous by the deferral, only a policy consequence. |
| 5 | Final-revision staged-binding grace-period bound left unspecified | **Left deferred, explicitly re-affirmed and further verified non-circular.** §32 re-verifies the qualitative rule is complete and the quantitative bound is a legitimate, narrow, **implementation-level invariant** (§12.1 #2) — a numeric parameter, not a structural gap. |
| 6 | §6.2 does not explicitly bind actor/session/agent provenance | **Left deferred, classified.** Not addressed by any state or invariant in this document — correctly out of scope, since CLTR-001's own purpose (§2.1) is scoped to lifecycle-fact authority, not agent/session provenance (a distinct, already-existing PCAE concern per session-continuity machinery, independently re-confirmed still true). Classified: **schema-level, non-blocking**, exactly as 135C found; this document does not add an actor-identity invariant, since doing so would require touching CLTR-001's own §6.2 field list, which is out of this phase's scope (no schema is frozen or amended here). |
| 7 | §26.1's ORDER-series covers only 4 of §8.2's 7 ordering requirements | **Resolved.** §11.1 mints CLTR-ORDER-5, -6, -7, explicitly classified as a **derived clarification of CLTR-001** (no new substantive requirement — the text already existed in §8.2). This is the one 135C finding this phase fully closes rather than merely constraining or re-deferring. |
| 8 | A tenth forbidden claim ("conformant despite conflicting/quarantined evidence") could be made explicit | **Constrained, confirmed still structurally guaranteed.** §28.3 independently re-derives that `conflicting` always blocks T3 via CLTR-AUTH-1's Blocking severity — the tenth forbidden claim remains structurally guaranteed without needing its own explicit CLTR-001 §31.1 entry. Classified: **non-blocking completeness-polish**, unchanged from 135C. |
| 9 | A third non-atomic write site (`quarantine_artifact`, line 141) not previously cited | **Constrained, re-confirmed still live.** §0 item 2 independently re-verifies all three sites (`canonical_artifact_promotion.py:111,115,141`) unchanged; §20's nine atomic-visibility invariants apply uniformly to all three, requiring no site-specific invariant. Not repaired (§44). |
| 10 | NOTIFIED→TERMINAL_SUCCESS transition modeling depth question | **Resolved via explicit modeling choice.** §5's T13 and §4's TERMINAL_SUCCESS row model this as a genuine, distinct transition (not an automatic, unobservable side effect of reaching NOTIFIED) — because TERMINAL_SUCCESS's own closure is the point at which the record becomes fully and finally sealed for *external* purposes (distinct from NOTIFIED, which seals only the delivery-confirmation fact). This phase's own position: keeping T13 as an explicit, separate transition is **the correct level of modeling depth**, because it gives §35's terminal-state analysis a distinct row to reason about (e.g., "is this specific closure quarantinable independently of NOTIFIED's own state" — yes, per §4/§35, a QUARANTINED flag can attach to the closed TERMINAL_SUCCESS record independently of when NOTIFIED itself was reached). **Classified: resolved, non-blocking** — no further ambiguity remains for a future implementation phase to invent semantics for. |

**No deferred question was silently ignored.** Two are fully **resolved** (#7, #10), eight are **constrained** (further narrowed, re-verified, or explicitly re-classified) without requiring a CLTR-001 text change, and none is promoted to Blocking or found to require a corrective contract-amendment phase.

---

## 38. Verification methodology

This phase's own architecture is independently verified against every source in §1's hierarchy, using the same RE-DERIVE/DO-NOT-TRUST discipline 135C applied to 135B, extended one layer deeper (verifying an architecture derived from a contract, not merely the contract itself).

**Contradiction-driven analysis — the nine adversarial questions, applied against this document's own §3–§36:**

1. **Can two authorities disagree?** Tested against §14 (authority invariants) and §9 (cross-representation model): every representation's authority role is uniquely assigned (S/R/D/E/V), and CLTR-AUTH-1 (§11) is Blocking precisely to prevent two S-role claims for the same fact. No case found in §4–§10 where two representations could both legitimately claim S-role for the same fact. **No disagreement possible by construction.**
2. **Can a derivative become authoritative?** Tested against §10 (representation-state matrix)'s "Authoritative"/"Derivative only" columns: every representation other than the record itself, the immutable snapshot, promotion's own E-role fact, and the receipt's own narrow domain is explicitly marked derivative-only. CLTR-AUTH-2 (§11) forbids independent reconstruction. **No path found for a derivative to acquire authority.**
3. **Can an irreversible effect happen too early?** Tested against §8 (irreversibility model) and §36 item 10: three independent mechanisms (CLTR-ORDER-4, §8.1's classification, §6's F1/F2/F12) all agree no irreversible operation precedes T3. **No early-irreversibility path found.**
4. **Can retry cause duplication?** Tested against §24 (retry/resume matrix) and §21 item 6 (CLTR-NOTIFY-2): every retry-eligible state's re-entry is either idempotent (resolves to existing state) or explicitly rejects re-dispatch. §26 (duplicate/replay matrix) independently confirms every replay case resolves to exactly one deterministic outcome, never silent duplication. **No duplication path found.**
5. **Can missing evidence be silently inferred?** Tested against §19 (evidence invariants) item 8 and CLTR-AUTH-2: missing required evidence blocks T3 (routes to FAILED_PRE_CERT via T4), never silently defaulting. **No silent-inference path found.**
6. **Can identity be truncated or substituted?** Tested against §13 (identity invariants)'s full twelve-identifier table: every identifier requires exact equality, no truncation, no prefix matching, no fuzzy matching — independently re-verified per-identifier-type, not as a blanket claim. **No truncation/substitution path found.**
7. **Can current and historical state be confused?** Tested against §7.2 (V-role point-in-time binding), §14 item 4/6 (observation truthfulness), and CLTR-PERSIST-2 (immutable history never rewritten): a historical binding is always distinguishable from a live re-measurement by its own bound timestamp (§31). **No confusion path found.**
8. **Can a terminal transition be replayed?** Tested against §35 (terminal-state analysis): every terminal/terminal-ish state explicitly prohibits ordinary replay (CLTR-RETRY-2, F7, F14) and resolves any resubmission to the existing terminal record. **No replay path found.**
9. **Can an external event be falsely claimed?** Tested against §23 (receipt invariants) item 8 (CLTR-RECEIPT-1) and §21 items 3–4 (CLTR-NOTIFY-1): a receipt's claimed outcome is bounded to `record.actually_reached_stages` (CLTR-ORDER-7); a notification payload's evidence is bounded to promoted canonical bindings only. **No false-claim path found.**

**Cross-source contradiction check (§1's hierarchy, applied pairwise):**

- **This document vs. CLTR-001:** every state, transition, and invariant traces to a CLTR-001 clause or is explicitly flagged as a derived clarification (CLTR-ORDER-5/6/7, §11.1), candidate amendment (NOTIFIED_UNCONFIRMED naming, §25), implementation-level invariant (branch-reachability, grace-period bound, §12.1), or non-blocking recommendation (marker/receipt ordering freedom, §16 item 7). No contradiction found.
- **This document vs. 135C:** every one of 135C's ten findings is dispositioned (§37), none re-litigated as if it did not exist, none silently dropped. No contradiction found.
- **This document vs. 135A:** §3's re-derivation independently arrives at the same 14-state inventory 135A originally proposed and CLTR-001 froze — not because it was copied, but because the same minimality arguments (checked fresh per-candidate, §3.2) hold. No contradiction found.
- **This document vs. 134F:** §0's source re-verification confirms all three 134F-disclosed gaps remain exactly as characterized, with Gap B's surface area matching 135C's corrected three-site count (not 134F's or 135A's original citations, which predate 135C's more thorough grep). No contradiction found — the more precise 135C/135D account supersedes the earlier, less complete counts without contradicting their substance.
- **This document vs. PFN-001:** §21 independently re-confirms every PFN-001 guarantee is preserved. No contradiction found.
- **This document vs. current production behavior:** §0, §29 classify every divergence as `adapter`/legacy, never imported into the state model. No contradiction found (by design — current behavior is compatibility evidence only, never a source that could contradict the model in a way requiring resolution).

**No contradiction found across any pairing.** This is not a claim that no imperfection exists (§37's ten dispositions include several genuinely open, if narrow, questions) — it is the specific, narrower claim that no two sources in §1's hierarchy assert incompatible requirements this document fails to reconcile or disclose.

---

## 39. Findings classification

### Consolidated findings register (this phase's own, independent of 135C's ten)

| # | Finding | Section | Classification |
|---|---|---|---|
| 1 | §8.2's marker/receipt ordering ("step 11 before step 12") is narrative sequencing, not a binding precondition — either may be written first or concurrently | §16 item 7 | NON-BLOCKING, implementation-level sequencing freedom |
| 2 | NOTIFIED_UNCONFIRMED's definition conflates two distinguishable sub-cases (delivery-confirmed-incomplete-bookkeeping vs. genuinely-uncertain-occurrence) under one hedge ("or is believed to have occurred") | §25 (restating and further constraining 135C finding #1) | NON-BLOCKING, candidate future amendment |
| 3 | Architecture Status mislabeling defect is not currently manifesting in this session's own live output, though the underlying source defect remains untouched | §30 (restating and further constraining 135C finding #3) | NON-BLOCKING, editorial/implementation debt, already covered by an existing invariant (CLTR-ORDER-5) |
| 4 | Three of §8.2's seven ordering requirements previously lacked a numbered CLTR-ORDER-* entry | §11.1 | RESOLVED this phase (CLTR-ORDER-5/6/7 minted as derived clarifications) |

### Disposition of every prior BLOCKING-candidate category (per the assignment's own definition)

Each category the assignment defines as automatically Blocking is checked against this document's full model:

| Blocking-candidate category | Found in this model? |
|---|---|
| Ambiguous canonical authority | No — §14, §38 item 1 |
| Overlapping or contradictory lifecycle states | No — §3.2's per-candidate rejection of every redundant/overlapping candidate; §35's terminal-state analysis finds no overlap |
| Nondeterministic retry result | No — §24, §26 name exactly one outcome per case; §33 proves determinism |
| Missing terminal classification | No — §35 covers all six terminal/terminal-ish states completely |
| Irreversible transition without prior certification | No — §8, §36 item 10, triple-redundantly enforced |
| State machine permitting duplicate external delivery | No — §21 item 6, §26, §38 item 4 |
| State allowing fabricated commit ownership to become authoritative | No — §17 items 10–11, CLTR-COMMIT-3; the *policy* consequence remains deferred, but fabricated hashes are never silently `verified` |
| Mixed-generation canonical visibility | No — §20's nine invariants, none aspirational (135C §16's own testability finding, independently re-confirmed here) |
| Unresolvable final-revision circularity | No — §32's proof |
| Compatibility path preserving unsafe authority | No — §29's classification table; every adapter-classified mechanism is explicitly non-authoritative, never granted a permanent exemption (§28.2) |
| Invariant that cannot be evaluated deterministically | No — every invariant in §11 names an inspectable, testable condition (evaluation-inputs column populated for all 36) |

**Zero Blocking findings.** All findings in this phase's own register (§39) are NON-BLOCKING or already RESOLVED. All ten of 135C's inherited findings remain correctly NON-BLOCKING after this phase's own re-verification (§37) — none was found, on deeper state-machine-level scrutiny, to actually rise to Blocking severity.

**No Blocking contract defect was discovered.** CLTR-001 does not require amendment as a precondition for this phase's own completion or for a future implementation phase to proceed.

---

## 40. Phase verdict

### Assessment against the three possible verdicts

**A. VERIFIED** — requires zero open questions of any kind. Not chosen: this phase's own §37/§39 registers real, if narrow, open questions (NOTIFIED_UNCONFIRMED naming precision, the Architecture Status defect's current non-manifestation vs. underlying persistence, two implementation-level invariant refinements). A model this thorough with literally zero open questions would itself be a red flag for insufficiently adversarial verification, matching 135C's own reasoning for choosing verdict B over A.

**C. NOT VERIFIED** — requires any Blocking ambiguity, a state machine that is nondeterministic, conflicting invariants, or a state machine that would force a future implementation to invent missing semantics. Not chosen: §39 finds zero Blocking findings; §33 proves determinism; §38's cross-source contradiction check finds no conflict; §34/§35 find complete reachability and terminal coverage; §5's transition inventory has no implicit transitions (§5.1) — nothing is left for a future implementation to invent.

### Verdict

## **B. VERIFIED WITH NON-BLOCKING DEFERRED QUESTIONS**

This phase confirms, independently re-derived rather than trusted:

- **State inventory is complete** (§3, 14 states, re-derived from 21 named candidates, none added or removed relative to CLTR-001's frozen inventory).
- **Transitions are deterministic** (§33's structural-induction proof).
- **All states are reachable, or intentionally exceptional** (§34 — no unreachable state, no dead-end non-terminal state, no ambiguous predecessor; the two orthogonal states are intentionally exceptional by design, not accidentally so).
- **Terminal semantics are complete** (§35 — all six terminal/terminal-ish states fully specified across nine dimensions each).
- **Retry/resume is deterministic** (§24, §26 — every re-entry point and every replay case names exactly one required behavior).
- **Representation-state matrix is complete** (§10 — every state's must-not/may/must-exist/immutable/repairable/visible/authoritative/derivative-only columns populated).
- **Invariants are evaluable** (§11 — all 36 invariants carry populated evaluation-inputs, success/failure conditions, and test strategies).
- **No Blocking finding exists** (§39).

This verdict is chosen over VERIFIED (A) for the same reason 135C chose B over A: a sufficiently adversarial, sufficiently deep verification of a model this size finding *zero* open questions would itself indicate insufficient scrutiny, not superior soundness. It is chosen over NOT VERIFIED (C) because none of this phase's own findings, nor any of 135C's ten inherited findings, rises to Blocking — none duplicates authority, none leaves a state-transition conflict, none leaves retry semantics incomplete, none permits fabricated ownership to become silently authoritative, none makes atomic visibility aspirational, none leaves final-revision binding circular (§32's proof), and a future prototype-planning phase (135E) can proceed without needing to invent any missing core semantics.

**No repair occurred in 135D.** All findings (§39, and the ten inherited from 135C, §37) are documented as either resolved-by-derived-clarification (§11.1, requiring no CLTR-001 text change), constrained/re-verified (§37), or recommendations for a future phase. **CLTR-001 requires no amendment.**

---

## 41. Next-phase derivation

Per this phase's own instruction, the next phase is derived from unresolved requirements, not assumed from CLTR-001 §33.2's or 135A §18.2's prior naming.

### 41.1 What remains unresolved after 135D

- A **prototype** does not yet exist — nothing in 135A/135B/135C/135D constructs an actual record from real historical artifacts to check whether the state model (§3–§10) and invariant set (§11) actually hold against real data, not just against their own internally-consistent text.
- The **atomic-visibility mechanism** (§20) remains unselected — deliberately, per CLTR-001 §13.2's deferral, re-affirmed non-blocking by 135C and by this phase.
- The **commit-ownership blocking-vs-warning policy** (§17.1) remains deferred — a governance decision, not an architecture question, and out of scope for an architecture/prototype-planning phase to resolve.
- **Exact serialization/schema** remains unfrozen (135A §2.3, CLTR-001 §6.3, unaffected by this phase, which adds no schema).
- **135D's own two open modeling questions** (NOTIFIED_UNCONFIRMED naming precision, §25; marker/receipt ordering freedom formalized as a genuine finding, §16 item 7) are candidates for a schema-freeze phase to close, not for a prototype-planning phase.

### 41.2 Candidate next directions, evaluated

- **Canonical serialization and digest architecture** — premature: 134B's own precedent (freeze stages/invariants before data structures, cited throughout CLTR-001) argues for a read-only prototype *before* committing to a wire format, so the prototype can inform serialization needs empirically rather than speculatively.
- **Executable schema architecture** — same reasoning; premature before a prototype demonstrates which fields are actually load-bearing against real data.
- **Compatibility and migration architecture** — this is 135H's stated scope (135A §18.2 item 8), not 135D's immediate successor; migration planning is premature before a prototype demonstrates the record model actually reconstructs real historical transitions faithfully.
- **Prototype plan** — the smallest correct next step: per 135A §18.2 item 5 and CLTR-001 §32.2's own "implementation readiness" self-assessment ("sufficient for later schema design, prototype planning, and integration/legacy-retirement planning"), a *plan* for a read-only prototype (what it reads — existing reports, metadata, markers, receipts, checkpoints — to construct a record retroactively, for verification purposes only, writing nothing, changing no entry point) is the step that lets the state machine and invariant set defined in this document be checked against real data before any schema or serialization commitment is made.

### 41.3 Recommended next phase

**135E — Canonical Transition Record Prototype Plan.** This is the smallest step that resolves 135D's own remaining open question ("does this state model and invariant set actually hold against real historical data") without prematurely committing to a schema, serialization format, or migration sequence — consistent with 135A §18.2's original re-derived sequence, independently re-confirmed here as still the correct next step after 135D specifically (not merely re-asserted): 135D's own findings (§37's dispositions, §39's zero-Blocking register) leave nothing for 135E to resolve at the architecture level; what remains is empirical (does the model hold against real artifacts), which only a prototype plan — and eventually a prototype — can test.

**This is not begun in 135D.**

---

## Files changed

- Added: `docs/PHASE_135_CROSS_REPRESENTATION_INVARIANT_ARCHITECTURE_AND_STATE_MACHINE_VERIFICATION.md` (this document)
- Added: `tasks/active/20260712-2147-phase-135d-cross-representation-invariant-architecture-and-state-machine-verification.md` (governed task contract)
- Updated per governed phase completion: `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, canonical report and metadata (see final governed phase report for exact diffs)

No production source, test, schema, or configuration file was created or modified by this phase.

## Governance results

- `pcae_health`: healthy, Git status 2 changed files (this document + task contract), agent lock held by `claude-local`
- `pcae_check`: passed — architecture zones touched: docs (2 files), tasks (1 file); session continuity verified
- `pcae_doctor_task_memory`: clean, no inconsistencies (re-verified at session start, §0)
- `pcae_push_check`: clean at session start (nothing to push before this phase's own work; final push state reported in this phase's own finalization)
- `pcae_runtime_inspect`: Observed / observe / execution unavailable, 0 plugins, 0 capabilities registered (re-verified at session start, §0, unchanged from every prior Track 135 phase)
- `telegram_runtime`: configured; production Telegram used only for the final governed terminal report per this phase's own finalization

## Test results

- `fast_green`, `compileall`: **not re-run** — no production source or test file changed by this phase; per this phase's own governing instructions, the full suite is run only if governance requires it, a source/test file unexpectedly changes, or a state-machine claim cannot be assessed without broader regression evidence. None of these conditions occurred (§0's source re-verification was read-only `grep`/`sed` inspection, not a change). Baseline remains 4391/4391, last run at 135B's finalization (135C independently confirmed unchanged at its own finalization; no source touched since).
- `report_notification_tests`, `bootstrap_session_reporting_tests`: covered by the existing fast_green baseline, unchanged since no source was touched in the interim.

## Runtime state

- Runtime state: Observed (unchanged)
- Maximum capability: observe (unchanged)
- Execution availability: unavailable (unchanged)

## PFN-001 / PFR-001 confirmation

- **PFN-001**: unchanged. §0 item 6 and §21 (notification invariants) independently re-confirm every one of PFN-001's guarantees (exactly-once delivery, outbound-only, idempotent dispatch) is preserved by this document's state-machine model; no clause of PFN-001 is amended, narrowed, or reinterpreted.
- **PFR-001**: unchanged. §9's cross-representation model treats the canonical phase report as a derivative bound by reference (per CLTR-001 §12.1's already-frozen row); this document does not modify PFR-001's content-structure requirements.

## No-go confirmations

No implementation occurred. No JSON schema was frozen. No source code was added or modified. No test was added or modified. No finalization behavior changed. No entry-point behavior changed. No atomic-latest-write repair occurred (Gap B remains live, documented in §0, §20, §29). No resume-logic repair occurred (Gap A remains live, documented in §0, §24). No fabricated-hash repair occurred (Gap C remains live, documented in §0, §17). No Architecture Status label defect was repaired (§30 investigates and classifies only). No historical report was rewritten. No immutable snapshot was modified. No PFN-001 change occurred. No PFR-001 change occurred. No Repository Intelligence authority expansion occurred. No Advisory authority change occurred. No Decision Evaluation change occurred. No execution capability was introduced. No shell mediation was added. No Telegram inbound control or new communication channel was added. No CLTR-001 contract repair or amendment occurred (CLTR-ORDER-5/6/7, §11.1, are derived clarifications of already-frozen text, not amendments). Phase 135E was not begun. No raw `git commit` was used. No raw `git push` was used. No `--no-verify` was used. No force push was used.

## Recommended next phase

135E — Canonical Transition Record Prototype Plan
