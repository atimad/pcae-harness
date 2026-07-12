# Phase 135A — Canonical Lifecycle State Authority Architecture

**Phase class:** Architecture (Track 135 opening phase)
**Scope:** Architecture only. No implementation, no schema freeze, no source change, no test change, no repair of any 134F-disclosed gap.
**Predecessor:** Track 134 (134A–134F), closed CONDITIONALLY CLOSED by 134F — Whole-Lifecycle Independent Verification.
**Non-goal:** Begin 135B (Contract Freeze) or any later Track 135 phase.

---

## 1. Track 135 purpose

### 1.1 Why Track 135 exists after Track 134

Track 134 answered the question *"is the current governed finalization lifecycle coherent?"* — and, per 134F, the answer is yes: zero unresolved BLOCKING contradictions across architecture, contract, source, tests, canonical artifacts, immutable snapshots, receipts, markers, and Git history for the full 134A→134F span.

But 134F's own verdict was **CONDITIONALLY CLOSED**, not **CLOSED**, because coherence today is an emergent property of several independently-maintained representations staying in step:

- the finalization transaction's own checkpoint state,
- the legacy `promote_and_dispatch` closure inside each of the four entry points,
- the `.last-notified.json` marker,
- the `.pcae/delivery-receipts/` store,
- the `latest.md` / `latest.json` canonical pointer pair,
- the projected post-completion Architecture Status seal,
- Git commit-ownership attribution,
- and each entry point's own pre-transaction marker check.

Nothing today *forces* these to agree. They agree because Track 134 carefully proved, phase by phase, that they currently do. 134F's three disclosed structural gaps (non-terminal classification of `completed_receipt_best_effort_incomplete` inside the transaction's own resume logic; the non-atomic `latest.md`/`latest.json` pair; the fabricated-hash gap in commit-ownership verification) are not defects in today's behavior — they are demonstrations that today's safety depends on cooperating representations rather than on structural impossibility of divergence.

Track 135 exists to ask a different question than Track 134 asked: *not* "is the current lifecycle coherent," but *"can the lifecycle be redesigned so that incoherence among these representations becomes structurally impossible rather than merely currently avoided?"*

### 1.2 Six distinct concepts this track must keep separate

Track 134 used "lifecycle" as a single word for several distinct concerns. Track 135 requires these to be named separately, because the canonical lifecycle state authority is specifically an authority architecture, not a correctness, representation, projection, verification, or persistence architecture — although it constrains all of those.

| Concept | Definition | Track 134 status | Track 135 relationship |
|---|---|---|---|
| **Lifecycle correctness** | Whether a given governed transition, as it actually executed, was sound | Proven for 134A–134F by 134F | Not re-litigated; 135 does not re-verify Track 134 |
| **Lifecycle authority** | Which representation is the *source of truth* for a given lifecycle fact | Distributed across ~11 cooperating representations (134F §2, §11) | **135's primary subject** — defined in §3 below |
| **Lifecycle representation** | Any artifact that expresses a lifecycle fact (report, metadata, marker, receipt, Architecture Status section) | Multiple representations per fact, kept aligned by contract discipline | Reclassified in §3, §6 as derivative, not authoritative |
| **Lifecycle projection** | An external-facing rendering of lifecycle state for a specific audience (operator report, notification payload, Architecture Status) | Already recognized in 134A/134B as "views," composed from evidence | Formalized as deterministic derivations of one record (§6) |
| **Lifecycle verification** | Independent re-derivation and challenge of a lifecycle claim (what 134F did) | The verification *method*, not a persistent structure | Becomes able to verify against one canonical anchor instead of re-deriving coherence from N representations (§3, "verification anchor") |
| **Lifecycle persistence** | How lifecycle facts are durably stored, made atomically visible, and recovered after a crash | Partially atomic today (checkpoint, receipt store) and partially non-atomic (`latest.*` pair) | Addressed architecturally in §8, without selecting a final mechanism |

Track 134 verified **correctness**. Track 135 targets **authority**: replacing "many representations that currently agree" with "one record that the representations are proven, by construction, to derive from."

### 1.3 What Track 135 does not do

Track 135 does not claim Track 134's implementation is wrong, unsafe, or in need of urgent repair. All three 134F-disclosed gaps are explicitly non-blocking today, and 135A repairs none of them. Track 135 is preventive architecture: it exists so that as the lifecycle grows more entry points, more governance layers, or more downstream consumers (Repository Intelligence, Historical Memory, Dependency Knowledge Graph, strategic governance), the number of representations that must be manually kept in step does not grow linearly with each addition.

---

## 2. Canonical lifecycle transition record

### 2.1 Concept

The **canonical lifecycle transition record** ("the record") is the proposed single artifact that represents one governed lifecycle transition — one execution of the finalization transaction for one phase or task — as a whole, from the moment a transition is proposed through to its terminal outcome (success, quarantine, or superseded).

Every other lifecycle artifact that exists today or is added in the future should be classifiable as exactly one of:

1. an **immutable representation** of the record (e.g., the record itself, once sealed, is never rewritten — only superseded by a new record for a later transition);
2. a **deterministic derivative** of the record (e.g., the rendered phase report, the Architecture Status section, `latest.json`);
3. an **external projection** of the record (e.g., the Telegram notification payload — a representation deliberately shaped for an audience outside the repository);
4. a **verification result** against the record (e.g., a future 134F-style independent verification report, or `pcae check`/`pcae doctor`).

No artifact may claim a fifth category — "independent lifecycle authority" — going forward. §14 (Legacy authority retirement) classifies today's artifacts against this taxonomy.

### 2.2 Field responsibilities and boundaries (not a frozen schema)

135A defines *what the record must be able to answer*, not its wire format, storage format, or exact field names — schema freeze is explicitly out of scope and belongs to 135B. The categories below group the fields listed in the assignment by responsibility, so 135B has a structured starting point rather than an unordered field list.

**Identity fields** (bind the record to exactly one transition, unambiguously — see §9):
schema version; transition ID; phase ID; task ID; report identity; snapshot identity; checkpoint identity; promotion identity; notification identity; marker identity; receipt identity.

**Transition classification fields** (what kind of transition this is, and where it sits in the state machine — see §4, §5):
transition type; prior lifecycle state; projected post-transition state; transition status; failure state; retry classification; supersession state.

**Provenance and ownership fields** (who and what produced this transition — see §10):
explicit phase commit ownership; source repository identity; branch identity; source revision; final revision.

**Evidence-reference fields** (pointers to the evidence this transition certified against, not copies of it — see §6):
metadata identity; Architecture Status projection identity; test evidence references; governance evidence references; notification result.

**Temporal and integrity fields** (when, and how it is protected from silent corruption — see §8):
timestamps (proposed, certified, checkpointed, promoted, notified, terminal); record digest; compatibility metadata.

The record is deliberately **reference-heavy, not copy-heavy**: it should hold identities and digests that bind it to evidence (a report, a snapshot, a receipt), not duplicate that evidence's content. This is what makes derivation (§6) meaningful rather than circular — a derivative is produced *from* the evidence the record points to, verified *against* the record's binding of that evidence's identity.

### 2.3 Why the schema is not frozen here

134B's approach to the 12-stage contract — freeze the stages and invariants first, let 134D/134E work out exact data structures — is the template 135A follows. Freezing exact field names, types, and encodings in 135A without first freezing the authority model (§3), state machine (§4), and invariant set (§11) risks re-litigating structure once those are settled in 135B–135D. 135A defines boundaries and responsibilities; 135B is where the schema is frozen.

---

## 3. Authority model

For each lifecycle fact, this section states whether the canonical transition record is the **sole authority** (S), an **authority reference** — the record holds an identity/digest that binds to a fact whose content lives elsewhere, but no other artifact may reinterpret that identity (R), an **immutable event record** — the fact is one entry in the record's own append-only history, never mutated (E), a **deterministic derivation source** — other artifacts are produced from the record and must not independently reconstruct the fact (D), or a **verification anchor** — the record is what independent verification checks against, not itself the check (V).

| Lifecycle fact | Role of canonical record | Current competing authority (134F) | Must stop being independent authority |
|---|---|---|---|
| Phase identity | S | Parsed independently by ≥5 regex sites (`architecture_status.py`, `phase_reports.py` ×4) | Yes — regex parsing becomes a projection of an identity the record already carries, not a source of truth (§9) |
| Task identity | S | No dedicated task-ID grammar; inferred from phase-ID-shaped strings | Yes |
| Completion state | S | Distributed across transaction checkpoint status, `.last-notified.json`, receipt store, Architecture Status seal | Yes — see §5 |
| Active/inactive state | D (derived from record's transition status) | Inferred from PROJECT_STATUS.md "Current Phase" section + absence of a later completion | Yes |
| Planned successor | D | Free text in the "Recommended Next Phase" field of the prior report | Partially — becomes a derivative of the record's `projected post-transition state`, but the *proposal* of a successor remains human/governance input, not something the record invents |
| Explicit commits | S (as declared at transition proposal) + V (verified against Git) | `phase_commits` metadata field, cross-checked ad hoc by `detect_cross_phase_commit_contamination` | Partially — see §10 |
| Files changed | D | Recomputed per report from `git diff`/`git status` at report-generation time | No — files changed is legitimately re-derivable from source revision + final revision at any time; the record just needs to bind those revisions (R) |
| Tests | R | Free-text summary strings in the report body | Partially — record should hold test evidence *references* (suite name, pass/fail counts, run ID), not narrative prose |
| Governance checks | R | Same as tests — currently narrative | Partially |
| Report completeness | D | `report.report_completeness` field on `PhaseReport`, computed by PFR-001 validation | No — completeness is a derived judgment about the report; the record should hold *whether certification passed*, and the report's own completeness check remains a derivation input |
| Report consistency | V | `validate_derived_correctness`, re-run ad hoc at multiple points (initial certification, 134E.10.1V.1 sealed-snapshot re-check) | Partially — becomes a standing verification against the record's frozen evidence bindings rather than a re-run validation with no fixed anchor |
| Architecture Status | D | Generated from `PROJECT_STATUS.md` + the projected-post-completion seal (134E.10.1V.1) | Yes — both the current-state and projected-state generation should read from the record, not from re-parsing PROJECT_STATUS.md headers independently at each of 5+ call sites |
| Checkpoint | E (one immutable entry per attempt) | `.pcae/finalization-transactions/<phase_id>.json`, mutated in place (`_save_checkpoint`, atomic replace) | Yes — checkpoint becomes the record's own in-progress state, not a separate file with independent resume logic |
| Promotion | E + D | `promote_artifact()`'s `ArtifactState` machine, orthogonal to the transaction's own status | Partially — promotion is a real, independently-necessary state machine (content certification for artifact publishing); it becomes a *stage* the record tracks, not a fact the record must re-derive from artifact inspection |
| Notification | R + E | `.last-notified.json` marker + `notification_result` field on the report | Yes — the marker's *role as terminal-state authority* must retire; its content becomes a derivative/cache of the record's notification identity and result |
| Marker | D (retired as authority) | `.last-notified.json`, currently read by every entry point as the *actual* terminal-state check (134F §11) | Yes — this is the central authority-retirement target of Track 135 (§4.4, §14) |
| Receipt | E | `.pcae/delivery-receipts/`, immutable, correctly modeled today | No — receipts are already architecturally sound as immutable event records; they become bound to the record via receipt identity rather than re-derived |
| Repository clean state | V | Measured live by `git status` at report time, not persisted | No change needed — this must remain a live measurement (§11, invariant 16), but the record should carry the *measured result at certification time* as a binding, immutable fact, distinct from any live re-measurement done afterward for `pcae health` |
| Pushed state | V | Same as above | No change needed for the same reason |
| origin/main..HEAD | V | Same as above | No change needed for the same reason |

The pattern across this table: identity and completion-state facts should collapse onto the record as sole authority; evidence-heavy facts (tests, governance, files changed) remain externally measurable but the record should hold binding references to *which* measurement was certified; live repository facts (clean, pushed, ahead-count) correctly remain live verification, not something the record freezes as historical truth about the *current* repository — only as historical truth about what was true *at certification time* for that transition.

---

## 4. Lifecycle state machine

### 4.1 Re-derivation, not reuse, of state names

The assignment is explicit that current implementation names must not be copied blindly. The finalization transaction today uses `"in_progress"`, `"completed"`, `"resumed_completed"`, `"gate_not_passed"`, `"pre_promotion_certification_failed"`, `"promotion_and_dispatch_failed"`, `"completed_receipt_best_effort_incomplete"` — a flat status string with no explicit machine. The candidate list in the assignment (`prepared`, `validating`, `certified`, `checkpointed`, `promoted`, `notification_pending`, `notified`, `marker_persisted`, `receipt_complete`, `receipt_best_effort_incomplete`, `failed_before_certification`, `failed_after_certification`, `retryable`, `terminal_success`, `terminal_partial_external`, `quarantined`, `superseded`) is itself a candidate, not a freeze. Re-deriving from the actual stages Track 134 proved necessary (134B's 12-stage contract; the transaction's 4 real phases: pre-promotion certification, promotion+dispatch, receipt modeling, terminal) yields the minimum coherent model below.

### 4.2 Minimum coherent state model

```
                    ┌─────────────┐
                    │  PROPOSED   │  (transition identity + evidence bindings declared,
                    └──────┬──────┘   nothing durable yet)
                           │
                           ▼
                    ┌─────────────┐
                    │ CERTIFYING  │  (pre-promotion certification: evidence extraction,
                    └──────┬──────┘   view composition, rendering, sealed-snapshot check)
                 fail      │      pass
        ┌──────────────────┴──────────────────┐
        ▼                                      ▼
┌───────────────────┐                  ┌──────────────┐
│ FAILED_PRE_CERT    │ (terminal,      │  CERTIFIED   │  (record sealed: digest fixed,
│ (retryable: yes)    │  no side       └──────┬───────┘   evidence bindings immutable)
└───────────────────┘  effects)               │
                                               ▼
                                        ┌──────────────┐
                                        │  PROMOTING   │  (artifact promotion +
                                        └──────┬───────┘   delivery dispatch)
                                  fail          │        pass
                     ┌──────────────────────────┴─────────────────┐
                     ▼                                             ▼
            ┌───────────────────┐                          ┌──────────────┐
            │ FAILED_POST_CERT   │ (terminal-ish;          │   PROMOTED   │
            │ (retryable: only    │  CERTIFIED record       └──────┬───────┘
            │  via new attempt,   │  is NOT reversed —             │
            │  never by mutating  │  see §5.5)                     ▼
            │  this record)       │                          ┌──────────────┐
            └───────────────────┘                            │ NOTIFYING    │
                                                               └──────┬───────┘
                                                     delivery         │    delivery
                                                     confirmed        │    unconfirmed
                                        ┌──────────────────────────────┴──────────┐
                                        ▼                                          ▼
                                ┌──────────────┐                         ┌─────────────────────┐
                                │   NOTIFIED   │                         │ NOTIFIED_UNCONFIRMED │
                                └──────┬───────┘                         │ (best-effort receipt  │
                                       │                                  │  modeling incomplete; │
                                       ▼                                  │  delivery itself       │
                                ┌──────────────┐                         │  already irreversible) │
                                │TERMINAL_SUCCESS│                       └──────────┬────────────┘
                                └──────────────┘                                    │
                                                                                     ▼
                                                                          ┌─────────────────────┐
                                                                          │TERMINAL_PARTIAL_     │
                                                                          │EXTERNAL               │
                                                                          └───────────────────────┘

Orthogonal states (apply to any CERTIFIED-or-later record, not part of the main spine):
  QUARANTINED   — record or its bound evidence failed post-hoc integrity verification
  SUPERSEDED    — a later transition record for the same phase/task correction exists
```

### 4.3 Naming rationale

- **PROPOSED** replaces the assignment's `prepared` — chosen to make explicit that nothing durable exists yet; this is the state before the transaction has written even a checkpoint.
- **CERTIFYING** / **CERTIFIED** collapse the assignment's `validating`/`certified` and map directly onto the real pre-promotion certification stage (`_build_pre_promotion_artifacts`) and the sealed-snapshot digest check that already exists in `finalization_transaction.py:564-594`.
- **CHECKPOINTED** from the candidate list is deliberately **not** a separate state in the minimum model: today's checkpoint write is an *implementation mechanism* for crash recovery within CERTIFYING/CERTIFIED, not a distinct semantic stage the outside world needs to observe. §8 addresses checkpointing as a persistence concern, not a state-machine stage.
- **PROMOTING** / **PROMOTED** map onto `promote_and_dispatch()` — deliberately kept as one transition-record stage even though it wraps two sub-concerns (artifact promotion and delivery dispatch), because 134B's contract already treats "Delivery Adapter Dispatch" as inseparable from "Repository/Governance Certification" in ordering (promotion before dispatch, both within one legacy call), and 135 architecture should not force a split the current contract doesn't require.
- **NOTIFYING** / **NOTIFIED** / **NOTIFIED_UNCONFIRMED** replace the assignment's `notification_pending`/`notified`/`receipt_best_effort_incomplete`. This is the direct architectural answer to §5's central question: `completed_receipt_best_effort_incomplete` is renamed and reclassified as **NOTIFIED_UNCONFIRMED**, a *terminal-ish* state the record itself recognizes, not an opaque status string that only entry-point marker checks happen to intercept.
- **FAILED_PRE_CERT** / **FAILED_POST_CERT** replace `failed_before_certification`/`failed_after_certification`, kept because the distinction is architecturally load-bearing: failure before CERTIFIED has no side effects and is freely retryable; failure after CERTIFIED (i.e., during PROMOTING) may have already produced irreversible external effects and must never be treated as "as if nothing happened."
- **retryable** and **terminal_success** from the candidate list are not separate *states* in this model — they are **properties of** states (every state above is tagged retryable: yes/no in §5), not additional nodes. Making them states would double the state count without adding information the state itself doesn't already imply.
- **QUARANTINED** and **SUPERSEDED** are kept as orthogonal (cross-cutting) states rather than spine states, because both can apply to a record regardless of where in the main spine it terminated — a QUARANTINED record and a SUPERSEDED record answer "what happened to this record after the fact," not "how did this transition conclude."

---

## 5. Transition semantics

### 5.1 Allowed transitions

PROPOSED→CERTIFYING; CERTIFYING→CERTIFIED; CERTIFYING→FAILED_PRE_CERT; CERTIFIED→PROMOTING; PROMOTING→PROMOTED; PROMOTING→FAILED_POST_CERT; PROMOTED→NOTIFYING; NOTIFYING→NOTIFIED; NOTIFYING→NOTIFIED_UNCONFIRMED; NOTIFIED→TERMINAL_SUCCESS; NOTIFIED_UNCONFIRMED→TERMINAL_PARTIAL_EXTERNAL. Any CERTIFIED-or-later state → QUARANTINED (orthogonal, triggered by independent integrity verification, not by the transaction itself). Any terminal state → SUPERSEDED (orthogonal, triggered only by the existence of a later transition record for a correction of the same phase/task).

### 5.2 Forbidden transitions

No state may transition backward along the spine (PROMOTED can never return to CERTIFIED; NOTIFIED can never return to PROMOTING). No state may skip a required predecessor (nothing may reach PROMOTING without having been CERTIFIED — this is the direct generalization of the existing invariant that promotion never occurs without passing pre-promotion certification). FAILED_PRE_CERT can never transition to PROMOTING (a failed-before-certification record is dead; a *new* record, referencing a new PROPOSED, is what retries). TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, and FAILED_PRE_CERT never transition to any other spine state — only the orthogonal QUARANTINED/SUPERSEDED apply to them henceforth.

### 5.3 Terminal states and retry states

**Terminal** (no further spine transition possible): FAILED_PRE_CERT, TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL. **Retryable via a new record** (the failed/incomplete record itself is never mutated; a new PROPOSED record referencing the same phase/task is created instead): FAILED_PRE_CERT (freely — no side effects occurred), FAILED_POST_CERT (carefully — see §5.5), NOTIFIED_UNCONFIRMED is **not** retried in the sense of re-attempting delivery; it is terminal for the transition's own purposes and retryable only in the narrow sense of re-attempting *receipt confirmation*, never re-attempting the delivery itself (this mirrors 134F's confirmation that a successful `promote_and_dispatch` is never undone or repeated).

### 5.4 Idempotent re-entry, duplicate ordinary completion, replay

Idempotent re-entry (the same PROPOSED transition submitted again with identical evidence bindings) must, at any point after CERTIFIED, resolve to the existing record's current state without re-executing PROMOTING — this generalizes today's resume check (`finalization_transaction.py:596-607`) but extends it to recognize **NOTIFIED_UNCONFIRMED as terminal for resume purposes**, closing the exact gap 134F disclosed: the record's own resume logic, not an external marker, must recognize that PROMOTING has already occurred and must never occur again for this transition. Duplicate ordinary completion (a second, distinct PROPOSED transition for a phase/task the record already shows TERMINAL_SUCCESS for) is a data-entry/governance error, not a resume — it must be rejected at PROPOSED with a reference to the existing terminal record, never silently accepted as a new success. Replay (re-submitting an old CERTIFIED record's evidence after a new record already exists for the same phase/task) must be rejected via the identity and supersession rules in §9.

### 5.5 Partial failure recovery

FAILED_POST_CERT recovery is the most architecturally delicate transition semantics in this model, because PROMOTING may have partially executed irreversible external effects (e.g., an artifact was promoted but delivery failed, or delivery occurred but receipt modeling failed — the current `completed_receipt_best_effort_incomplete` case, now NOTIFIED_UNCONFIRMED). The architecture must never allow recovery logic to *infer* what happened by re-executing PROMOTING; instead, recovery must **observe** the actual external state (was the artifact promoted? was delivery sent?) and record a new, separate observation event before deciding whether a new record's PROMOTING may safely proceed. This is a generalization of the existing sealed-snapshot / receipt-honesty design (`finalization_transaction.py` only records delivery success by reading it back from the actually-promoted report, never from the pre-promotion trial report) — the future authority must own this observation discipline structurally, not leave it to each entry point's judgment.

### 5.6 Notification retry, promotion retry, marker recovery, receipt recovery

Notification retry: only from NOTIFYING (never from NOTIFIED or NOTIFIED_UNCONFIRMED — those are terminal-ish for the delivery attempt they represent; a *new* notification attempt is a new record's NOTIFYING). Promotion retry: only from CERTIFIED (never from PROMOTED — promotion is idempotent-by-identity, not repeatable-by-effect, matching today's `ArtifactState` machine where only `CERTIFIED`-source calls write files). Marker recovery: under this architecture, the marker becomes a *derivative* of the record (§14); recovering from a missing or corrupt marker means re-deriving it from the record's NOTIFIED/NOTIFIED_UNCONFIRMED state, never inferring completion from the marker's absence or presence as today's entry points do. Receipt recovery: receipts remain immutable event records (§3); "recovery" here means re-attempting the receipt-modeling *step*, never re-attempting delivery, and binding any recovered receipt to the same record via receipt identity.

### 5.7 Supersession and quarantine

Supersession applies when a later, correcting transition record exists for the same phase/task (mirroring 134B's "historical preservation, correction-only after Completed" invariant). A superseded record's content is never deleted or rewritten — supersession is an annotation, not a replacement. Quarantine applies when independent verification (a future 134F-style pass, or automated integrity checking) finds that a record's bound evidence no longer matches its digest, or that a derivative was found to have drifted from the record. Quarantine does not delete the record; it flags it as untrusted pending human review, mirroring the existing `canonical_artifact_promotion.py` `QUARANTINED` `ArtifactState`.

---

## 6. Derivation architecture

### 6.1 Principle

Every derived representation must be producible by a pure function of `(canonical transition record, the evidence it binds to by reference)`. No derivation function may consult any *other* derivative to reconstruct a fact the record itself does not carry — this is the direct fix for today's pattern where, e.g., Architecture Status generation, receipt-honesty checks, and notification dispatch each independently re-derive "is this transition actually done" from different sources (transaction checkpoint, `.last-notified.json`, report fields) that happen to agree.

### 6.2 Derivation map

| Derived artifact | Derived from | Must not independently reconstruct |
|---|---|---|
| Canonical phase report | Record's evidence-reference fields (metadata identity, test/governance evidence references) + the evidence itself, fetched by reference | Completion status, notification result — both come from the record's transition state, not from re-checking markers |
| Completion metadata | Record's identity + classification fields | Phase/task identity — never re-parsed from free text |
| Architecture Status | Record's phase ID + transition status + projected post-transition state | Current/In Progress/Planned classification — must read the record's projected state, not re-scan PROJECT_STATUS.md headers independently at each of today's 5+ call sites |
| Immutable snapshot | Record's CERTIFIED-state evidence bindings, sealed at the same moment the record enters CERTIFIED | Nothing — the snapshot *is* the record's certified evidence, not a second independent certification |
| Checkpoint | Record's own in-progress spine position | N/A — checkpoint is retired as a separate artifact; it becomes how the record itself is persisted mid-transition (§8) |
| Promoted latest report / metadata | Record's PROMOTED-state binding, one atomic write (§8) | The report/metadata content — always sourced from the record's sealed evidence, never regenerated post-hoc |
| Notification payload | Record's NOTIFYING-state evidence bindings | Delivery success/failure — this is an *observation written back into the record* (§5.5), not something the payload generator decides |
| Completion marker | Record's NOTIFIED/NOTIFIED_UNCONFIRMED state | Terminal-ness — the marker becomes informational/cache, never the thing entry points check to decide whether to resume (§14) |
| Finalization receipt | Record's receipt identity binding | Nothing — receipts remain their own immutable event class, bound to but not derived in content from the record |
| Git attribution view | Record's commit-ownership fields, verified against live Git at CERTIFYING time | Nothing new — this generalizes today's `detect_cross_phase_commit_contamination`, but ties its result into the record rather than a per-report ad hoc check |
| Repository transition view | Record's source/final revision bindings | Nothing — "what changed" is always computable from the two bound revisions, never stored redundantly |

### 6.3 The no-independent-reconstruction rule

If a future derivative needs a fact the record does not carry, the correct fix is to add that fact (or a reference to it) to the record's schema in 135B — not to let the derivative infer it from context, naming convention, or a sibling artifact. This is the structural answer to 134F's finding that safety today depends on cooperating representations: derivatives that are *mathematically* functions of the record cannot drift from it, whereas representations that each do their own inference can.

---

## 7. Projected post-completion state

### 7.1 Relationship between current state, transition, and projection

134E.10.1V.1 already established the core idea this section generalizes: at certification time, the transaction seals a deterministic projection of what the world will look like *after* this transition completes (e.g., the completing phase removed from "In Progress," its recommended successor added to "Planned" but never to "In Progress"), and that projection — not a fresh re-scan of mutable state — is what gets used for every subsequent derivative (rendering, promotion, delivery).

Under the canonical authority model, this generalizes cleanly: **prior lifecycle state** and **projected post-transition state** are both first-class fields on the record (§2.2), computed once at CERTIFYING and frozen at CERTIFIED. Every externally visible derived state (Architecture Status, operator report, notification payload) reads the *projected* state once the record reaches PROMOTED, never the current mutable repository/PROJECT_STATUS.md state re-scanned independently.

### 7.2 When projected state becomes authoritative

Projected state is **advisory** while the record is CERTIFYING (it is a plan, not yet certified) and **authoritative** from CERTIFIED onward (once sealed, no later derivative may compute a different projection for the same record — this is exactly the sealed-snapshot re-check already present at `finalization_transaction.py:564-594`, generalized to the full record rather than just the report digest pair).

### 7.3 Preventing known failure modes

- **Completed phase appearing active**: prevented structurally because "active" derivatives (Architecture Status "In Progress") must be computed from the *most recent record's* projected post-transition state, not from independent PROJECT_STATUS.md header scanning — there is exactly one place a phase's active/inactive fact can come from.
- **Planned successor becoming active prematurely**: prevented because the record's projected state explicitly separates "recommended successor" (a Planned-only projection) from "current/active phase" (only ever set by that successor's *own* future CERTIFIED record) — these must never be the same field or conflated by a derivative.
- **Mutable post-certification reads**: prevented because every derivative reads the record's frozen CERTIFIED-or-later fields, never live-queries PROJECT_STATUS.md or `.last-notified.json` for facts the record already owns.
- **Post-certification regeneration**: prevented because regeneration of a derivative (e.g., re-rendering a report) must reproduce byte-identical output from the same sealed record — any divergence is a derivation bug to fix, never a signal to "regenerate from current state instead."
- **Active-phase inference from naming or reports**: prevented because active-phase determination becomes a lookup against the record's own identity and status fields, never a heuristic over report titles, filenames, or prose.

---

## 8. Persistence architecture

### 8.1 Conceptual requirements

The canonical transition record must support: an **immutable history** (every record, once CERTIFIED, is permanent and append-only — corrections happen via supersession, §5.7, never mutation); a **mutable current pointer** (something must answer "what is the latest/current record for phase X" cheaply, without scanning full history); **crash consistency** (a crash at any point in CERTIFYING/PROMOTING/NOTIFYING must leave the system able to determine, on restart, exactly which spine state the record reached, with no ambiguous intermediate state); **write ordering** (the record's own state transition must be durable *before* any derivative that depends on that state is produced — e.g., promotion must not be observable as having happened before the record itself durably reflects CERTIFIED); **atomic visibility** (any reader must see either the fully-old or fully-new state of the current pointer, never a mix); **durability expectations** (each spine-state transition should be fsync'd or equivalently durable before the transaction proceeds to the next stage — this generalizes the existing checkpoint's atomic temp-file+`os.replace` pattern to the record as a whole); **partial-write detection** (a reader must be able to distinguish "no write attempted" from "write attempted but truncated/corrupted"); **latest-pointer recovery** (if the mutable current pointer is itself corrupted or missing, it must be reconstructible from the immutable history, never requiring the history to be reconstructed from the pointer); **tamper detection** (via the record digest — any modification to a sealed record's bound evidence must be detectable); **cross-file consistency** (if the record's canonical representation spans more than one file, all files must become visible together or not at all).

### 8.2 The latest.md / latest.json non-atomicity finding, analyzed architecturally

134F confirmed (and the research for this document re-confirmed at `canonical_artifact_promotion.py:108-116`) that `promote_artifact()` writes `latest.md` and `latest.json` as two independent `path.write_text()` calls with no shared transaction boundary. A crash, concurrent read, or concurrent competing writer between these two calls can observe a `latest.md` from one transition paired with a `latest.json` from a different (older or newer) transition — a **mixed-generation read**, which is exactly the failure mode invariant 16 in §11 must forbid going forward ("current pointer cannot expose mixed-generation report and metadata").

This is non-blocking today because: (a) `promote_artifact()` is only reachable from within the already-serialized finalization transaction, so today's single-agent, single-process usage pattern makes a genuine race unlikely in practice; and (b) both files are regenerated from the same sealed report object in the same call, so even a torn read only exposes a brief window, not permanently divergent content. But it is a structural gap: nothing in the current design makes mixed-generation reads *impossible*, only *unlikely under current usage*.

### 8.3 Candidate mechanisms (architecture only — no selection required to establish invariants)

The assignment offers five candidate mechanisms; each is evaluated against the requirements in §8.1 without committing to one, since 135A's job is to establish that *an* atomic mechanism is required, not which one:

- **Single canonical record plus derived files** — the record itself becomes the atomically-written unit (one file, one write), and `latest.md`/`latest.json` become derivatives regenerated from it, read-through or cached. Strongest alignment with §6's derivation principle; the cache-coherence problem moves from "two primary files" to "one primary file, N caches," which is a strictly easier problem (caches can be regenerated; they don't need to be atomically written *together*, only individually consistent with the record they were derived from).
- **Atomic directory promotion** — write a new directory of derivatives, then atomically rename/swap the "current" symlink or directory pointer. Guarantees full cross-file atomicity for an arbitrary number of derivative files, at the cost of directory-rename semantics needing OS/filesystem support (POSIX rename is atomic per-directory-entry but not guaranteed atomic across all target filesystems the harness might run on).
- **Manifest-based promotion** — write all derivative files first (each individually named uniquely, e.g. by digest), then atomically write a small manifest file that is the *only* thing pointed to as "current," listing which derivative files are the current set. Similar atomicity guarantee to the single-record approach but keeps derivatives as separate files rather than embedding them.
- **Generation directories plus pointer switch** — each transition's full derivative set lives in its own generation directory (`generations/<transition-id>/`), and a single small "current generation" pointer file is atomically swapped. Closely related to atomic directory promotion but avoids directory rename by keeping generation directories permanent and only swapping a pointer value.
- **Transactional local storage** (e.g., an embedded transactional store) — strongest consistency guarantees, but introduces a new dependency and a new failure mode (store corruption) not present in today's plain-file design, and is likely disproportionate given the harness's stated principles (§17: deterministic, inspectable, auditable — plain files are more directly inspectable than an opaque store format).

**135A does not select among these.** The invariant this section establishes is: *whichever mechanism 135B/135D ultimately specifies, it must guarantee that no reader can ever observe a partially-promoted derivative set* — single canonical record plus derived files is the candidate most consistent with §6's "no independent reconstruction" principle and is worth weighting first when 135B makes the freeze decision, but that decision is explicitly deferred.

---

## 9. Identity architecture

### 9.1 Canonical identity rules

Every identity type listed in the assignment (phase IDs, dotted/multi-dotted phase IDs, verification/corrective suffixes, task IDs, transition IDs, report IDs, snapshot IDs, receipt IDs, notification IDs, commit ownership records) must be **bound once, at PROPOSED, from an unambiguous declared source** — never inferred, parsed from free text, or reconstructed by regex at each consuming site. This directly generalizes 134B's existing "single phase identity bound at Stage 1, no free-text parsing, no precedence fallback" contract clause (§4) from phase identity alone to every identity type the record carries.

### 9.2 Dotted and multi-dotted phase IDs, verification/corrective suffixes

Today's phase-ID grammar (`architecture_status.py:51`, `r"^(\d+)([A-Za-z])((?:\.\d+[A-Za-z]?)*)$"`) is itself the product of two Track 134 repairs (134E.10.1.1's trailing-letter collision fix, generalized across 5 regex sites; 134E.10.1V.1's further fix to a Repository Transition adapter's parser) — a direct demonstration of the exact failure mode this section must architect away: **the same grammar, independently reimplemented at multiple sites, drifted out of sync at least twice within a single track.** Under the canonical authority model, the phase-ID grammar becomes a property of *identity parsing at PROPOSED time only* — once a phase ID is bound into a record, every other site that needs to work with that identity reads it from the record (or a derivative bound to the record), never re-parses it from a string. This does not eliminate the need for a phase-ID grammar (something must still parse "134E.10.1V.1" the first time), but it eliminates the need for that grammar to be reimplemented at five-plus independent sites, because only one site — record creation — ever needs to parse identity from raw text.

### 9.3 Rejected identity sources

The architecture explicitly rejects, as authority for any identity field: **prefix inference** (assuming a longer ID's prefix identifies its parent phase); **regex truncation** (any parsing that silently drops trailing components, the exact 134E.10.1.1/134E.10.1V.1 failure mode); **commit-subject parsing as authority** (a commit message is evidence a human/agent *claims* a relationship, never proof — this generalizes the existing `detect_cross_phase_commit_contamination`'s use of commit subjects as a contamination *signal*, explicitly not as ground truth); **recent Git fallback** (the exact pattern 134E.10.1.1 already removed — `_gather_commits()`'s unconditional `git log --oneline -5` — must never return as an implicit identity source anywhere else in the future architecture); **report field presence as proof** (a report merely *containing* a phase_id field does not make that field authoritative — the sealed-snapshot cross-check at `finalization_transaction.py:564-594` already treats this correctly, and that discipline generalizes); **ambiguous aliases** (no identity may have more than one canonical string form — if both "134E.10.1V.1" and some abbreviated or historical alias could refer to the same transition, the record must define exactly one canonical form and treat aliases purely as display/search convenience, never as independently resolvable identities).

### 9.4 Transition IDs as the new identity primitive

The record introduces one identity type that does not exist explicitly today: the **transition ID**, uniquely identifying one execution of the lifecycle (as distinct from the phase ID, which may have multiple transitions across its history — e.g., a failed attempt followed by a successful retry, or an original completion followed by a correction). Today, the closest equivalent is the `(report_digest, finalization_snapshot_id)` pair used for checkpoint/receipt/marker keying — 135B should evaluate whether the transition ID subsumes this pair or is derived from it, but 135A establishes that *some* single identity must exist that is finer-grained than phase ID and coarser-grained than any individual artifact's own ID (report ID, snapshot ID, etc.), because phase ID alone is insufficient to distinguish multiple transitions for the same phase.

---

## 10. Commit ownership architecture

### 10.1 Commit ownership as part of the canonical transition

Explicit phase commit ownership must be a **declared field at PROPOSED**, bound into the record at CERTIFIED, and verified against live Git as part of CERTIFYING — never inferred after the fact and never left as a purely advisory report field the way `phase_commits` is treated today for consumers other than the gate check.

### 10.2 Cases the architecture must address

- **No-commit phases** (pure documentation/architecture phases like this one) — the record must support an explicitly empty commit set as a valid, first-class declaration, not an implicit default reached by falling through an unhandled case (mirroring 134E.10.1.1's fix: no silent `git log` fallback when no commits are declared).
- **One-commit and multiple-commit phases** — both must be representable without special-casing; the record's commit-ownership field is a set, not a scalar.
- **Documentation completion commits, repair commits, verification-only commits** — the record should be able to classify *why* a commit belongs to this transition (which 134's phase taxonomy already distinguishes informally via phase-ID suffixes like corrective/verification phases), so that ownership verification can apply appropriately different expectations (e.g., a verification-only phase legitimately owning zero source-changing commits).
- **Prior-phase commits and unrelated commits** — must never be attributable to the current transition merely by recency; this is precisely what `detect_cross_phase_commit_contamination` defends against today and what the removed `_gather_commits()` fallback violated.
- **Fabricated hashes** — see §10.3.
- **Commit existence verification, repository identity binding, branch and revision binding, push-state verification** — these become explicit record fields (source repository identity, branch identity, source/final revision) rather than facts computed ad hoc at report-generation time; the record binds *which* repository, branch, and revision range a transition's commit claims are checked against, so verification is reproducible against the record rather than only reproducible by re-running the same live check.

### 10.3 The fabricated-hash gap, re-evaluated architecturally

The current gap (`phase_reports.py`, `detect_cross_phase_commit_contamination`, ~lines 1848–1856): when `git log -1 <hash>` fails (nonexistent hash) or returns non-zero, the check `continue`s — silently skipping verification rather than flagging the hash as unverifiable. 134F re-confirmed this as non-blocking by design, citing the codebase's extensive synthetic/fabricated-hash convention in its own hermetic test suite (tests intentionally use fake hashes to test contamination detection without touching real Git state) as the reason a blanket "unverifiable hash is fatal" rule would be disproportionate — it would break every test relying on this convention.

**135A does not repair this.** It re-evaluates the gap architecturally: under the canonical authority model, commit ownership verification is a CERTIFYING-time check that must produce one of three outcomes — *verified* (hash exists, subject doesn't contradict phase identity), *contaminated* (hash exists, subject names a different phase), or *unverifiable* (hash cannot be resolved against the bound repository identity/revision). Today's silent `continue` on git-log failure collapses "unverifiable" into "verified" by omission. The future contract must guarantee that **unverifiable is always a distinct, recorded outcome**, never silently equivalent to verified — whether that outcome is then treated as blocking, warning, or informational (a governance decision, not an architecture decision) is left to 135B/135D, but the record must at minimum be able to *represent* the distinction, which today's flat pass/fail contamination check cannot.

---

## 11. Cross-representation invariants

The mandatory invariant set, generalizing 134B's 17 lifecycle invariants (§7) and 134F's own findings into invariants specifically about *authority*, not just correctness:

1. Exactly one transition ID is referenced by every representation of a given transition (report, metadata, marker, receipt, notification payload) — no representation may carry a transition ID the record does not recognize.
2. Exactly one phase ID is referenced across all representations of that phase's most recent transition.
3. A completed phase never appears in any derivative's "active" or "in progress" classification.
4. If no phase's most recent transition record is in an active spine state (PROPOSED through PROMOTING), every derivative's "In Progress" representation is empty — never a stale phase left over from a prior transition's derivative that was not regenerated.
5. A planned successor is never classified as active by any derivative until *its own* transition record reaches CERTIFIED or later.
6. Explicit phase commits declared in the record equal the commits any derivative report claims as phase-owned — no derivative may report a commit set the record does not bind.
7. The promoted report and promoted metadata are both produced from the same CERTIFIED record — never from two different records, and never from a record that has not reached CERTIFIED.
8. Notification derives from the record's PROMOTED-state evidence bindings — never from independently re-gathered "current" evidence at notification time.
9. Marker and receipt for a given transition bind the same transition ID — a receipt and a marker referencing different transition IDs for what claims to be "the same" completion is a detectable inconsistency, not a silent acceptance.
10. The receipt reflects the actual observed delivery outcome (§5.5's observation discipline) — never an assumed or optimistic outcome.
11. Checkpoint precedes promotion — no PROMOTING may begin before the record reaches CERTIFIED.
12. Promotion precedes terminal external notification — no NOTIFYING may begin before PROMOTED.
13. No irreversible stage (PROMOTING onward) precedes semantic certification (CERTIFIED) — this generalizes today's sealed-snapshot re-check to a structural rule rather than a defensive check inserted at one call site.
14. Terminal states are recognized consistently by every entry point *and* by the record's own resume logic — this is the direct structural fix for 134F's central finding; no entry point may need its own independent terminal-state inference once the record's own resume check recognizes all terminal-ish states (including NOTIFIED_UNCONFIRMED).
15. The current pointer never exposes a mixed-generation report/metadata pair (§8.2).
16. Repository final-state observations (clean, pushed, ahead-count) are independently measured live and bound into the record as point-in-time facts about the transition — never assumed to still hold at some later read time, and never treated as retroactively true for a transition that occurred before the measurement.

---

## 12. Failure model

For each failure class: whether canonical state changes (Y/N/partial), whether external visibility changes (Y/N), whether retry is allowed, whether the transition is terminal, whether quarantine is required, whether human review is required, and what evidence must remain.

| Failure class | Canonical state changes | External visibility | Retry | Terminal | Quarantine | Human review | Evidence retained |
|---|---|---|---|---|---|---|---|
| Input authority failure (declared identity/evidence references don't resolve) | N (rejected before PROPOSED durably recorded) | N | Yes, freely | N/A — never entered the spine | No | No, unless repeated | The rejected proposal, for audit |
| Identity failure (ambiguous/malformed ID) | N | N | Yes, freely | N/A | No | No, unless repeated | The malformed input |
| Commit ownership failure (contaminated or unverifiable) | Partial — record notes the outcome, transition may still proceed or block per governance policy (135D) | Depends on policy | Yes, freely if pre-CERTIFIED | No, unless policy makes it blocking | No | Yes if unverifiable and policy treats it as suspicious | The specific hash and resolution attempt |
| Semantic disagreement (sealed evidence contradicts declared identity — today's `pre_promotion_certification_failed`) | N (fails at CERTIFYING, before CERTIFIED) | N | Yes, freely | Yes (FAILED_PRE_CERT) | No | No, unless repeated | The contradiction detail |
| Certification failure (rendering/composition exception) | N | N | Yes, freely | Yes (FAILED_PRE_CERT) | No | No, unless repeated | The exception |
| Checkpoint failure (durable write itself fails) | Ambiguous — must be resolved by durability guarantees in §8, not left as an open question | N (if write never completed) | Yes | Depends on whether any prior durable state exists | No | Yes if durability cannot be confirmed on restart | Whatever partial write exists, for forensic inspection |
| Promotion failure | Y — record reaches FAILED_POST_CERT; CERTIFIED evidence remains sealed and valid | Possibly Y if partial promotion occurred | Only via new record, never by re-running this record's PROMOTING | Yes-ish (terminal for this record; a new record may retry the transition) | Yes, if partial external state is ambiguous | Yes | Full CERTIFIED evidence plus the observed partial-promotion state |
| Notification failure (delivery itself fails, distinct from receipt modeling) | Y — record notes NOTIFYING failed | Y (delivery genuinely did not happen) | Yes, retry NOTIFYING for the same PROMOTED record | No — not terminal until delivery is confirmed one way or the other | No | Only if repeated failures | Delivery attempt evidence |
| Marker failure (marker write itself fails) | N to the record — marker is a derivative | N to the record's own state; Y to marker-dependent legacy readers until marker is regenerated | Yes — regenerate marker from record | No | No | No, unless marker cannot be regenerated at all | The record itself remains the source of truth regardless |
| Receipt failure (best-effort modeling incomplete — today's `completed_receipt_best_effort_incomplete`) | Y — record reaches NOTIFIED_UNCONFIRMED | N — the underlying delivery already succeeded; only receipt bookkeeping is incomplete | Retry receipt modeling only, never delivery | Yes-ish (terminal-ish: TERMINAL_PARTIAL_EXTERNAL) | No | Only if receipt can never be reconciled | The delivery evidence that did succeed |
| Mutable pointer failure (current pointer corrupted/missing) | N to history | Y until pointer is reconstructed | N/A — this is a recovery operation, not a transition retry | N/A | No | Only if reconstruction from history is itself ambiguous | Full immutable history, from which the pointer is reconstructed |
| Digest failure (record's bound evidence no longer matches its digest) | N — the record's own content is not rewritten | Y — flagged, not silently trusted | N/A | N/A | Yes, always | Yes, always | The mismatch details and both digests |
| Replay conflict (old evidence resubmitted after a newer record exists) | N — rejected | N | N/A — rejected, not retried | N/A | No | Only if replay appears adversarial/repeated | The rejected replay attempt |
| Duplicate completion (second transition claims to complete an already-TERMINAL_SUCCESS phase) | N — rejected at PROPOSED | N | N/A — rejected | N/A | No | Yes — this indicates a governance-process error, not a technical one | The rejected duplicate proposal, referencing the existing terminal record |
| Stale artifact conflict (a derivative was regenerated from an older record than the current pointer) | N to the record | Y — the derivative itself is wrong and must be regenerated | N/A — regenerate the derivative | N/A | No, unless the derivative was already externally delivered | Only if externally delivered | Which record the stale derivative actually matched |
| Cross-phase substitution (a derivative or evidence reference resolves to the wrong phase's data) | N to the record if caught at CERTIFYING (rejected); Y if caught later (quarantine) | Y once discovered | Depends on when caught | Depends | Yes if discovered post-hoc | Yes, always | The substitution details |
| Strategic governance reference staleness | Out of scope for this record — see §16 | N/A | N/A | N/A | N/A | N/A | N/A |

---

## 13. Resume and recovery architecture

### 13.1 Principle: resume from record state, not entry-point inference

The single most important behavioral change this architecture targets (to be realized in later Track 135 phases, not in 135A) is: **every resume decision must be answerable by reading the record's own current spine state**, never by an entry point independently checking a marker, a receipt store, or a checkpoint file and inferring what must have happened. This directly retires the pattern 134F found load-bearing today — four independent entry points, each running its own `certify_notification_transition`/`notification_dispatch_state` check against `.last-notified.json` before ever reaching the transaction.

### 13.2 Recovery by record state

- **Resume before CERTIFIED**: record shows PROPOSED or CERTIFYING with no terminal marker — safe to retry from scratch; no side effects to account for (matches today's `pre_promotion_certification_failed` — zero side effects).
- **Resume after CERTIFIED, before PROMOTING started**: record shows CERTIFIED — safe to proceed to PROMOTING; the sealed evidence is still valid and does not need re-certification (matches today's resume check treating a completed checkpoint as reusable — generalized to an intermediate CERTIFIED state, which today's flat status model cannot represent explicitly).
- **Resume after PROMOTING started but outcome unknown (crash mid-stage)**: this is the case §5.5 and §12's checkpoint-failure row flag as needing an explicit **observation step** before any retry decision — the architecture must never assume PROMOTING did or did not complete; it must check.
- **Resume after PROMOTED**: record shows PROMOTED or later — PROMOTING must never be re-attempted; only NOTIFYING may proceed or be re-attempted.
- **Resume after NOTIFYING (delivery attempted, outcome unknown)**: same observation discipline as PROMOTING — never assume, always check actual delivery-sink state where feasible, or bound the ambiguity explicitly.
- **Resume after NOTIFIED or NOTIFIED_UNCONFIRMED**: both are terminal-for-resume-purposes; this is the exact structural fix for the 134F gap — the record's own resume logic must recognize NOTIFIED_UNCONFIRMED as "do not re-run PROMOTING or NOTIFYING," matching what only the external marker check accomplishes today.
- **Incomplete receipt**: retry only the receipt-modeling step, bound to the existing record, never touching PROMOTING/NOTIFYING.
- **Best-effort external failure**: recorded as NOTIFIED_UNCONFIRMED; recovery is reconciliation (confirm delivery happened via some independent signal, then upgrade to NOTIFIED) or acceptance of the permanent partial state (TERMINAL_PARTIAL_EXTERNAL) — never a silent retry of delivery itself.
- **Repeated invocation**: idempotent at every spine state per §5.4.
- **Crash between durable writes**: bounded by §8's durability/write-ordering requirements — the architecture's job here is to guarantee that "between durable writes" is always a well-defined, detectable state, not an ambiguous one.
- **Stale current pointer**: recoverable from immutable history per §8.1's latest-pointer-recovery requirement.
- **Partially promoted derivative set**: prevented structurally by §8's atomicity requirement, but if it occurs anyway (e.g., during a migration period before the new mechanism is fully in place), it must be detectable (via record digest cross-check) and treated as a stale-artifact-conflict failure (§12), not silently accepted.

---

## 14. Legacy authority retirement

| Current authority/fallback | Classification | Rationale |
|---|---|---|
| Active task inference (from PROJECT_STATUS.md "Current Phase" free text) | Deprecate | Becomes a derivative of the record's active-transition lookup (§7.3); free-text inference is exactly the pattern §9 rejects for identity |
| Report status as authority (`report.report_completeness`, `report.status` fields treated as ground truth by consumers other than the gate check) | Retain as derivative | The report remains PFR-001's canonical content structure; its status fields become derived-and-displayed, not independently authoritative for lifecycle-state decisions |
| Completion metadata as independent authority | Retain as derivative | Same reasoning — metadata is a legitimate, necessary artifact; it stops being consulted as a *second* source of truth alongside the record |
| Architecture Status as authority | Retain as derivative | Already partially this way after 134E.10.1V.1's projected-state seal; 135 completes the transition by making the record the single computation source instead of PROJECT_STATUS.md header re-scanning |
| Latest marker (`.last-notified.json`) as sole terminal detector | Deprecate (as authority) / Retain as derivative (as a fast local cache) | This is the central retirement target (§13.1); the file itself can remain as a performance cache, but must never again be the *only* thing standing between a safe resume and a duplicate dispatch |
| Receipt as independent success authority | Retain as canonical (for its own narrow domain: delivery outcome), Retain as verification evidence (for the record's NOTIFIED/NOTIFIED_UNCONFIRMED classification) | Receipts are already well-designed (immutable, atomic); they become bound to the record via reference, not competing with it |
| Recent Git history attribution (`git log --oneline -N` fallback) | Retire | Already partially retired by 134E.10.1.1 for the primary code path; 135 architecture forbids its reintroduction anywhere, including future entry points |
| Commit subject parsing as authority | Retain as verification evidence only | Never authority (§9.3), but legitimately useful as a contamination *signal* the way `detect_cross_phase_commit_contamination` already uses it |
| Mutable latest-file inspection (reading `latest.md`/`latest.json` directly to determine "what happened") | Deprecate (as authority) / Retain as derivative (as the human/tool-facing artifact it should remain) | Consumers that need lifecycle *facts* should eventually read the record (or a record-bound derivative); consumers that want the human-readable report should still read `latest.md` — the distinction is authority, not existence |
| Entry-point-specific resume checks (each of the 4 entry points' own marker-check-before-transaction logic) | Retire (long-term) / Compatibility-only (short-term, during migration) | This is the other central retirement target; each entry point's bespoke pre-transaction check becomes unnecessary once the record's own resume logic is authoritative — but retiring these checks is implementation work for a later Track 135 phase, not 135A |

No retirement is implemented in 135A. This table is a classification for 135B–135H to act on.

---

## 15. Compatibility architecture

### 15.1 Historical immutability

No historical phase report, metadata file, immutable snapshot, marker, or receipt from before the canonical authority exists may be rewritten, migrated in place, or reinterpreted as if it had been produced under the new model. Track 134's own invariant ("historical preservation") extends directly: the canonical lifecycle state authority is additive going forward, not retroactive.

### 15.2 Compatibility surface

- **Historical phase reports and metadata**: remain readable and valid as PFR-001-conformant artifacts; the record architecture does not require them to have a corresponding transition record. A future migration phase (135H's stated scope) may choose to *backfill* records for historical transitions from existing artifacts, but that is explicitly a later decision, not assumed here.
- **Existing immutable snapshots**: remain valid; the record architecture's snapshot identity binding is a forward-looking addition, not a requirement retroactively imposed on existing snapshots.
- **Existing markers and receipts**: remain valid as-is; §14 classifies them as retained derivatives/evidence, not deprecated data.
- **PFN-001 and PFR-001**: both remain unchanged by this architecture (§17, §18 no-go confirmations). The record architecture must be designed so that it can satisfy PFN-001's delivery guarantee and PFR-001's content structure requirement without either contract needing amendment — the record supplies *authority*, not new content or delivery requirements.
- **All four production entry points**: none are behaviorally changed by 135A. A future implementation phase must design each entry point's eventual integration with the record such that the entry point's external behavior (what commands do, what they output, what side effects they have) is unchanged, only its internal source-of-truth for resume/completion decisions changes.
- **task finish / phase complete / phase-report create / notify send-report**: same as above — compatibility is entry-point-behavior-preserving, authority-source-changing.
- **Existing Repository Intelligence consumers**: any consumer reading lifecycle facts today (via reports, metadata, or Architecture Status) must continue to receive the same facts, sourced differently. This architecture introduces no new Repository Intelligence authority (§17).
- **Existing governance checks** (`pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push check`): unaffected — these check different concerns (repo cleanliness, task memory, push readiness) than lifecycle transition authority, and none is redefined by this document.

---

## 16. Strategic governance relationship

The IRG challenge run during this phase's initial inspection surfaced 6 persistent advisory concerns (SRR-66C-002 age, SLR-69P-001/SRR-66B-001 lineage mismatch, OBJ-004 thin primary coverage, strategic_governance capability growth, 69P missing registered successor, and the associated contradiction-synthesis pairs). Each is evaluated against the four categories the assignment specifies:

| Concern | Lifecycle state authority concern? | Strategic governance authority concern? | Repository Intelligence concern? | Separate future review debt? |
|---|---|---|---|---|
| SRR-66C-002 age / staleness after 24 completed phases | No | Yes | Partially (RI surfaces the staleness signal) | Yes |
| SLR-69P-001 citing SRR-66B-001 while SRR-66C-002 is latest | No | Yes | No | Yes |
| OBJ-004 thin primary coverage (2 primary / 13 supporting) | No | Yes | No | Yes |
| strategic_governance capability growth (21 capabilities) | No | Yes | Partially | Yes |
| 69P missing registered successor | No | Yes (it concerns strategic-governance phase sequencing, not lifecycle-transition sequencing) | No | Yes |
| Contradiction-synthesis pairs (TP-002 through TP-005) | No | Yes | Partially | Yes |

**Conclusion: none of these six concerns is a canonical-lifecycle-transition-authority concern.** They are about the *content and freshness of strategic governance review artifacts* (SRR/SLR documents, objective coverage) — a different authority domain than "which representation is the source of truth for a governed phase's finalization transition." The record this architecture defines does not model strategic review lineage, objective coverage, or strategic-governance phase sequencing at all; extending it to do so would be exactly the kind of unbounded scope growth §1.3 and the assignment's non-goals warn against.

There is one narrow point of architectural contact worth naming for future reference, not for action: if a future phase decides strategic governance reviews should themselves be tracked as governed lifecycle transitions (i.e., an SRR or SLR review becomes a "phase" with its own finalization), then the canonical transition record architecture defined here would apply to that review's transition the same way it applies to any other phase. That is a hypothetical extension, not a current requirement, and is explicitly not adopted into Track 135's scope by this document.

---

## 17. Governance boundaries

This architecture preserves every boundary the assignment specifies, by construction:

- **Runtime Observed / maximum capability observe / execution unavailable**: unaffected — this document defines a state-authority architecture for artifacts the harness already produces; it introduces no new execution path, no new capability, and no runtime state change. Confirmed via `pcae runtime inspect` in §Initial inspection: unchanged.
- **No backend invocation, no shell mediation, no Telegram inbound, no new communication channel**: the record's NOTIFYING stage in §4 explicitly reuses the existing PFN-001 delivery mechanism (the same `promote_and_dispatch` closure pattern) — it does not introduce a new channel, sink, or inbound control path.
- **PFN-001 / PFR-001**: both explicitly unchanged (§15.2); this architecture is designed to satisfy both without amendment.
- **Deterministic, inspectable, explainable, auditable**: directly advanced by this architecture — a single canonical record with deterministic derivatives is *more* inspectable and auditable than today's multi-representation model, which is the whole motivation for Track 135.
- **Historical artifact immutability**: preserved explicitly (§15.1).

---

## 18. Track 135 roadmap

The assignment's candidate sequence (135A–135I+) is evaluated and re-derived rather than assumed correct.

### 18.1 Evaluation of the candidate sequence

The candidate sequence's shape — Architecture → Contract Freeze → Contract Verification → Cross-Representation Invariant Architecture & State-Machine Verification → Prototype Plan → Read-Only Prototype → Prototype Verification → Integration & Legacy Retirement Plan → later implementation — mirrors Track 134's own proven A/B/C/D/E/F shape (Architecture → Contract → Contract Verification → Implementation Plan → phased Implementation → Whole-Lifecycle Independent Verification) and Repository Intelligence's repeatedly-reused shape (Architecture → Contract Freeze → Contract Verification → Prototype Plan → Prototype → Verification, reused across Change Impact, Historical Memory, Cross-Artifact Knowledge Integration, Unified Query, and the Repository Intelligence Service itself). This repeated shape across three prior tracks is strong evidence it is the right granularity, not an assumption to discard casually.

One adjustment is warranted: the candidate sequence's 135D ("Cross-Representation Invariant Architecture and State-Machine Verification") bundles two different activities — *architecting* the invariant set (which 135A already substantially begins in §11, and which 135B's contract freeze will need to finalize) and *verifying* the state machine (which requires the state machine to already be frozen, i.e., it logically follows contract freeze, not precedes or parallels it). Keeping it as one phase is defensible only if "state-machine verification" here means verifying the *contract's* description of the state machine for internal consistency (134C-style contract verification, applied specifically to the state-machine subset) rather than verifying an *implementation* (which does not exist until 135F). Read this way, 135D is coherent as written.

### 18.2 Re-derived sequence

1. **135A — Canonical Lifecycle State Authority Architecture** *(this document)*
2. **135B — Canonical Lifecycle Transition Record Contract Freeze** — freeze the record's schema (§2.2's categories, made concrete), the state machine (§4), transition semantics (§5), authority table (§3), and invariant set (§11) into a binding contract, following 134B's precedent of freezing structure before implementation exists.
3. **135C — Canonical Lifecycle Transition Record Contract Verification** — 134C-style independent verification that 135B's frozen contract is internally consistent, that it does not contradict 134B/PFN-001/PFR-001, and that it honestly represents what is architecture-only versus what remains a future obligation.
4. **135D — Cross-Representation Invariant Architecture and State-Machine Verification** — finalize the invariant set (§11) against the frozen contract, and verify the frozen state machine's transition table (§5) for completeness (every state has a defined set of allowed/forbidden transitions) and soundness (no invariant in §11 is violated by any allowed transition sequence).
5. **135E — Canonical Transition Record Prototype Plan** — plan a read-only prototype: what it will read (existing reports, metadata, markers, receipts, checkpoints) to *construct* a record retroactively for verification purposes, without writing anything or changing any entry point.
6. **135F — Canonical Transition Record Read-Only Prototype** — implement the read-only prototype per 135E's plan; produces records from existing artifacts for inspection/comparison only; no entry point behavior changes; mirrors the discipline every prior "Read-Only Prototype" phase in this repository's history has followed (Repository Intelligence 120, Change Impact, Historical Memory, Cross-Artifact Knowledge Integration, Unified Query, Repository Intelligence Service).
7. **135G — Canonical Transition Record Prototype Verification** — independent verification (134F/134C-style) that the prototype's constructed records faithfully match the real historical transitions they were built from, with zero fabrication or silent gap-filling.
8. **135H — Lifecycle Integration and Legacy Authority Retirement Plan** — *plan* (not execute) how the four entry points and the finalization transaction itself would be changed to make the record the live, write-time authority, and how §14's deprecate/retire classifications would actually be carried out, in what order, with what compatibility guarantees during migration.
9. **135I+ — later implementation only if architecture and contracts support it** — actual write-time integration, entry-point changes, and legacy retirement execution; explicitly gated on 135A–135H's architecture and plan surviving verification, per the assignment's own framing.

This sequence is not started beyond 135A by this document.

---

## 19. Architecture decision record

| # | Decision | Rationale | Rejected alternatives | Risks | Deferred questions |
|---|---|---|---|---|---|
| 1 | **Canonical authority location**: one record per transition, not one record per phase, not a single global ledger row per fact | A phase can have multiple transitions (failed attempt, successful retry, later correction); binding authority at the transition level is the only granularity that can represent §5.4's replay/duplicate/supersession semantics correctly | Global per-fact ledger (rejected: reintroduces the "many representations, one per fact" problem the whole track exists to solve, just centralized instead of distributed); per-phase single record (rejected: cannot represent multiple transitions without either mutation of history or an implicit sub-record concept, which is just a transition record by another name) | A transition-per-record model requires a clear way to find "the current one for phase X" (addressed by §8's mutable pointer) | Exact transition-ID generation scheme (135B) |
| 2 | **Lifecycle event vs. state model**: hybrid — the record's spine is a state machine (§4), but state transitions are themselves recorded as an append-only sequence of timestamped events within the record | A pure state model loses "how did we get here" forensic value; a pure event model requires every reader to replay events to know current state, which is expensive and error-prone to reimplement at each consumer | Pure current-state-only record (rejected: loses crash-forensics and audit value that 134F's own investigative method depended on); pure event-sourced model with no materialized current state (rejected: forces every derivative to replay history, reintroducing the "independent reconstruction" problem §6.3 forbids) | Hybrid model has two representations (event log + current state) to keep consistent — mitigated because both live inside one record, not across separate artifacts | Exact event schema (135B) |
| 3 | **Current state vs. immutable history**: current state is a derived materialization of the immutable event sequence within one record; across records, immutable history is the sequence of sealed records for a phase, and current state is "the latest non-superseded terminal (or in-flight) record" | Matches §8.1's requirement that the mutable pointer be reconstructible from immutable history, never the reverse | Mutable history with append-only current-state log only (rejected: violates immutability requirement, §5.7) | None beyond the general persistence risks in §8 | Mechanism selection (§8.3, deferred to 135B) |
| 4 | **Derived artifact status**: every non-record artifact is a derivative, projection, or verification result — none is an independent authority going forward | This is the track's central thesis (§1, §2.1) | Keep multiple cooperating authorities but formalize their cooperation contractually (rejected: this is what Track 134 already did, and 134F's gaps show contractual cooperation alone does not eliminate structural drift risk) | Derivation functions must be kept correct as the record's schema evolves — a derivation bug now has one cause (bad derivation logic) instead of N causes (N independently-wrong representations), which is a risk reduction, not a risk elimination | How strictly "pure function of the record" is enforced in practice (135B/135D) |
| 5 | **Transition identity**: introduce a transition ID distinct from phase ID (§9.4) | Phase ID alone cannot distinguish multiple transitions for the same phase | Reuse `(report_digest, finalization_snapshot_id)` pair as-is (rejected as the *final* answer, though it may become the transition ID's implementation, because the pair is currently scoped to report content, not the full record's identity) | None beyond ordinary identity-scheme risk | Whether transition ID subsumes or wraps the existing digest pair (135B) |
| 6 | **Atomic visibility**: required as an invariant (§8, §11.15); mechanism deferred | The requirement is provable necessary now (§8.2's analysis); the mechanism choice is not yet necessary to prove that necessity | Selecting a mechanism now (rejected: assignment explicitly scopes architecture-only, and premature mechanism selection risks anchoring 135B's contract freeze to an unexamined choice) | None from deferring; risk would come from *not* establishing the invariant, which this document avoids | Mechanism selection (135B) |
| 7 | **Resume authority**: the record's own resume logic, not entry-point-specific checks, is authoritative (§13.1) | Directly resolves 134F's central disclosed gap | Keep entry-point checks as primary, formalize them further (rejected: this is the status quo Track 134 already proved works but disclosed as structurally fragile) | Migration risk: entry points currently provide real safety; retiring them (a later-phase concern, §14) must be sequenced carefully so safety is never reduced during transition | Exact migration sequencing (135H) |
| 8 | **Retry classification**: retry is always a new record referencing the same phase/task, never mutation of a failed/incomplete record | Preserves immutability (§8.1) and makes forensic history complete — every attempt, successful or not, remains visible | Mutate the existing record in place on retry (rejected: destroys the "what actually happened on attempt 1" forensic trail, and reintroduces ambiguity about whether a "completed" record was always completed or became so after edits) | Multiple records per phase requires the "current" pointer logic to correctly select the right one (§8) | None beyond already-covered persistence questions |
| 9 | **Terminal-state ownership**: the record itself, not any derivative or marker, owns terminal-state determination, including the new NOTIFIED_UNCONFIRMED state | Direct fix for 134F's gap | Leave marker as terminal-state authority, just document it better (rejected: documentation does not close a structural gap; a future entry point could still be added without the marker check and reintroduce the exact risk 134F flagged) | None new | None |
| 10 | **Commit ownership**: declared at PROPOSED, verified at CERTIFYING, with unverifiable as a distinct recorded outcome (§10) | Closes the "unverifiable silently equals verified" gap at the architecture level without prematurely deciding governance policy for how unverifiable should be treated | Repair the fabricated-hash gap now by making unverifiable always blocking (rejected: explicitly out of scope — "do not repair" — and would break the existing synthetic-hash test convention without a governance decision first) | Leaves the actual gap open until a later phase decides policy | Whether unverifiable should block, warn, or be informational (135D) |
| 11 | **Historical compatibility**: fully additive, zero retroactive rewriting (§15) | Matches 134B's historical-preservation invariant and general governance principle of auditability | Backfill historical records immediately as part of 135 (rejected: out of scope for an architecture phase, and premature before the record schema itself is frozen) | None from deferring | Whether/how to backfill historical records (135H, explicitly flagged as a later decision) |
| 12 | **Fallback retirement**: classified (§14) but not executed | 135A is architecture only | Begin retiring fallbacks immediately (rejected: explicitly forbidden by the assignment's non-goals) | None from deferring | Retirement sequencing and safety verification (135H) |
| 13 | **Notification relationship**: NOTIFYING/NOTIFIED/NOTIFIED_UNCONFIRMED stages reuse PFN-001's existing delivery mechanism; the record adds authority over *when* and *whether* delivery is attempted/confirmed, not a new delivery mechanism | Preserves PFN-001 unchanged (§15.2, §17) while closing the resume-authority gap | Design a new notification mechanism as part of the record (rejected: unnecessary scope expansion; PFN-001 already correctly separates content/delivery concerns, §2 of PFN-001) | None new | None |
| 14 | **Receipt relationship**: receipts remain their own immutable event class, bound to but not subsumed by the record | Receipts are already well-designed (134F confirmed no changes needed); subsuming them into the record would be a regression, not an improvement | Merge receipt content directly into the record (rejected: receipts serve a distinct purpose — external-delivery-outcome evidence — and conflating them with the record's own transition-state tracking would blur that distinction) | None new | Exact reference mechanism between record and receipt identity (135B) |

---

## Files changed

- Added: `docs/PHASE_135_CANONICAL_LIFECYCLE_STATE_AUTHORITY_ARCHITECTURE.md` (this document)
- Updated per governed phase completion: `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, active task contract, canonical report and metadata (see final governed phase report for exact diffs)

No production source, test, schema, or configuration file was created or modified by this phase.

## Governance results

- `pcae_health`: healthy (idle), Git status clean
- `pcae_check`: passed (no active task, idle)
- `pcae_doctor_task_memory`: clean, no inconsistencies
- `pcae_push_check`: clean, nothing to push (this document is committed as part of governed finalization, see final phase report)
- `pcae_runtime_inspect`: Observed / observe / execution unavailable (unchanged)
- `telegram_runtime`: configured; production Telegram used only for the final governed terminal report per this phase's own finalization

## Runtime state

- Runtime state: Observed (unchanged)
- Maximum capability: observe (unchanged)
- Execution availability: unavailable (unchanged)

## PFN-001 / PFR-001 confirmation

- PFN-001: unchanged. This document does not modify notification delivery guarantees, sinks, or the "exactly one trusted canonical phase report delivered" requirement.
- PFR-001: unchanged. This document does not modify canonical phase report content structure requirements.

## No-go confirmations

- No implementation occurred. No transition record was built. No schema was frozen. No source code was added or modified. No test was added or modified. No finalization behavior changed. No entry-point behavior changed. No atomic-latest-write repair occurred. No resume-logic repair occurred. No fabricated-hash repair occurred. No historical report was rewritten. No immutable snapshot was modified. No PFN-001 change occurred. No PFR-001 change occurred. No Repository Intelligence authority expansion occurred. No Advisory authority change occurred. No Decision Evaluation change occurred. No execution capability was introduced. No shell mediation was added. No Telegram inbound control or new communication channel was added. 135B was not begun. No raw `git commit` was used. No raw `git push` was used. No `--no-verify` was used. No force push was used.

## Recommended next phase

Phase 135B — Canonical Lifecycle Transition Record Contract Freeze
