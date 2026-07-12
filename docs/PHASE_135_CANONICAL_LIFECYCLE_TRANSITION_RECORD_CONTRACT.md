# Phase 135B — Canonical Lifecycle Transition Record Contract

**Phase class:** Contract Freeze (Track 135, second phase)
**Scope:** Contract freeze only. No implementation, no JSON schema, no runtime behavior change, no repair of any disclosed gap (134F's three; 135A re-confirmed all three still present in current source).
**Predecessor:** 135A — Canonical Lifecycle State Authority Architecture (architecture only).
**Non-goal:** Begin 135C (Contract Verification) or any later Track 135 phase.

---

## 1. Contract identity

- **Contract name:** Canonical Lifecycle Transition Record Contract
- **Contract identifier:** **CLTR-001**
- **Contract version:** **1.0**
- **Contract status:** FROZEN (normative, binding on all future Track 135 phases from 135C onward)
- **Compatibility status:** Additive-only relative to 134B (Canonical Phase Finalization & Reporting Lifecycle Contract), PFR-001 (Canonical Phase Report Specification), and PFN-001 (Phase Finalization Notification Contract). No clause in this contract amends, weakens, or supersedes any clause of 134B, PFR-001, or PFN-001. Where this contract and a prior document appear to describe the same concern from a different angle (e.g., identity binding, invariant numbering), this contract's numbering is independent and the two are cross-referenced, not merged.
- **Authority:** This contract is binding on any future phase (135C and later) that designs, verifies, prototypes, or implements the canonical lifecycle transition record. It is advisory only with respect to Track 134's existing, already-governed finalization transaction and entry points — nothing in this contract requires or authorizes any change to `src/pcae/core/finalization_transaction.py`, the four production entry points, or any other production source in 135B or any phase before 135B's obligations are themselves implemented.
- **Applicability:** Applies to the canonical lifecycle transition record concept introduced by 135A (§2) and to every future derivative, projection, and verification result of that record. Does not apply to, and does not redefine, any artifact's *current* behavior.
- **Relationship to 135A:** This contract converts 135A's architecture (concepts, candidate state model, authority table, derivation map, invariant list, roadmap) into explicit, numbered, binding normative requirements. Every section below cites the 135A section it derives from. Where 135A left a question open (e.g., §8.3's mechanism choice, §9.4's transition-ID scheme), this contract either resolves it with a binding decision or explicitly classifies it as deferred (§32).
- **Relationship to Track 134:** Track 134 (134A–134F) is not re-litigated, re-verified, or amended by this contract. 134B's 12-stage contract, its Phase Identity Authority Contract (§4), its Evidence Normalization Contract (§7), and its Compatibility (§30) and Versioning (§32) contracts remain frozen exactly as 134B defines them. This contract's own §27 (Versioning) and §24 (Compatibility) are modeled on 134B's precedent but are independent clauses of CLTR-001, not amendments to 134B.
- **Relationship to PFN-001:** Unchanged, unamended. §21 of this contract freezes how the future record relates to PFN-001's existing delivery guarantee without altering that guarantee.
- **Relationship to PFR-001:** Unchanged, unamended. §12 of this contract freezes how the future record relates to the canonical phase report (PFR-001's twelve required sections, PFR-001 §5) without altering PFR-001's content structure.

---

## 2. Purpose contract

### 2.1 What the record exists to do

Restating and freezing 135A §1–§2: the Canonical Lifecycle Transition Record ("the record") exists to represent **one governed lifecycle transition** — one execution of the finalization transaction for one phase or task, from proposal through terminal outcome — as a single authoritative transaction record. The record must:

1. identify the exact governed transition (one transition ID, §5.1);
2. bind its authoritative inputs (declared identity, declared commit ownership, evidence references, §3, §10, §11);
3. bind its projected and certified outcome (§9);
4. bind all irreversible lifecycle stages (§7, §8);
5. expose deterministic state (§7);
6. support independent verification (§3's V role; a future 134F-style pass checks *against* the record, §32);
7. support retry and recovery (§16);
8. prevent derived artifacts from becoming competing authorities (§4, §12).

### 2.2 What the record must never do

1. execute commands, or authorize execution — the record is a lifecycle-fact authority, never an execution-authorization mechanism (§28);
2. replace Decision Evaluation — the record answers "what is the state of this transition," never "should this transition be allowed to proceed" in the governance-policy sense;
3. become Repository Intelligence — the record is scoped to one transition's lifecycle facts, not a general knowledge store about the repository;
4. infer missing facts — if the record does not carry a fact or a binding reference to it, no derivative may invent, guess, or reconstruct it (§6.3 of 135A, restated as §12.3 below);
5. reconstruct provenance from heuristics — commit ownership, identity, and evidence bindings are declared and verified, never inferred from naming, recency, or prose (§10, §11);
6. permit silent fallback authority — every failure-to-resolve case must produce a recorded, distinct outcome (§18), never a silent default to "verified" or "authoritative."

---

## 3. Authority contract

### 3.1 Authority roles

Restating 135A §3's five roles as binding classifications. Every lifecycle fact in §3.2 is assigned exactly one role:

| Role | Code | Meaning |
|---|---|---|
| Record-authoritative | **S** (sole) | The record is the only source of truth for this fact within a transition. No other artifact may independently establish it. |
| Externally authoritative and record-bound | **R** (reference) | The fact's content lives outside the record (e.g., in Git, in a test run, in a report body), but the record holds the binding identity/digest that authorizes treating that external content as *the* certified version for this transition. |
| Deterministic derivative | **D** | The fact is computed as a pure function of the record (and, where stated, the evidence it binds by reference). Derivatives may reproduce it; they may never independently reconstruct it by a different path. |
| Immutable evidence reference | **E** | The fact is one entry in the record's own append-only internal history — recorded once, at the stage it occurs, never rewritten. |
| Verification-only observation | **V** | The fact is, by nature, a live measurement of current external state (e.g., repository cleanliness) — the record binds the *measured value at a point in time*, but no artifact may treat a stale V-role value as still true without re-measuring. |

### 3.2 Per-fact authority table

Each row below is a binding requirement: authority source, which record field/reference category (per 135A §2.2's field grouping) carries it, the derivatives permitted, the fallback sources forbidden, and the required failure behavior when the authoritative source is unavailable.

| Lifecycle fact | Role | Record field category | Allowed derivatives | Forbidden fallback sources | Failure behavior when unavailable |
|---|---|---|---|---|---|
| Phase identity | S | Identity field | Any derivative displaying/filtering by phase ID | Regex re-parsing of free text at consuming sites (135A §3, §9.3); prefix inference; alias resolution | Record creation (PROPOSED, §5.2) fails closed — no record, no transition proceeds |
| Task identity | S | Identity field | Same as phase identity | Inference from phase-ID-shaped strings | Same — fails closed at PROPOSED |
| Transition identity | S (new primitive, 135A §9.4) | Identity field | Every representation's binding key (§11 invariant CLTR-ID-1) | Reuse of `(report_digest, finalization_snapshot_id)` as an implicit substitute without an explicit transition ID | Fails closed — no transition ID, no CERTIFIED state reachable |
| Transition type | S | Transition classification field | Rendering/labeling derivatives | Inference from phase-ID suffix pattern alone | Fails closed at PROPOSED if type cannot be declared |
| Prior lifecycle state | R (bound to the referenced prior record, or explicitly "none") | Transition classification field | Architecture Status "what changed" derivatives | Re-scanning PROJECT_STATUS.md for "what was true before" | Fails closed — a transition cannot be CERTIFIED without a declared, resolvable prior state (possibly the explicit value "no prior transition") |
| Projected post-transition state | S once CERTIFIED (advisory before, §9.2) | Transition classification field | Architecture Status generation, operator report "what will be true" sections | Re-derivation from mutable state after CERTIFIED (135A §7.3) | If projection cannot be computed deterministically at CERTIFYING, the transition fails at CERTIFYING (FAILED_PRE_CERT, §7.2) |
| Certified post-transition state | S from CERTIFIED onward | Transition classification field | All post-CERTIFIED derivatives | Any recomputation that could disagree with the sealed value | N/A — by definition this field only exists once CERTIFIED succeeds |
| Completion status | D (derived from the record's own spine state, §7) | Transition classification field (spine state) | Report status field, metadata status field, Architecture Status "Completed" section | Report status, metadata status, or marker presence treated as authority (§4) | If the record's spine state is itself unavailable, completion status is unknown, never assumed complete or incomplete |
| Active/inactive state | D | Derived from projected/certified state | Architecture Status "In Progress" section | PROJECT_STATUS.md "Current Phase" free-text inference (135A §14) | If no record's certified projected state names an active transition, active state is the explicit empty set, never inferred absence-as-something-else |
| Planned successor | D, with the proposal itself as human/governance input (135A §3 row) | Derived from projected state's "recommended successor" field | Architecture Status "Planned" section | Free-text "Recommended Next Phase" parsing as the sole source once a record exists | A missing successor proposal yields an explicit "no successor declared" derivative, never a guess |
| Phase-owned commits | S (declared) + V (verified against Git) | Provenance/ownership field | Git attribution view, operator report commit list | `git log --oneline -N` recency-based inference (135A §9.3); commit-subject parsing as authority | Each declared commit resolves to `verified`, `contaminated`, or `unverifiable` (§10.4) — never silently `verified` by omission |
| Repository identity | S (declared) + V (verified) | Provenance/ownership field | Git attribution view | Assumption of "the current working directory's repo" without binding | Fails closed at CERTIFYING if repository identity cannot be verified against the declared value |
| Branch | S (declared) + V (verified) | Provenance/ownership field | Repository transition view | Live branch read substituted for the declared/bound value post-certification | Same as repository identity |
| Source revision | S (declared) + V (verified) | Provenance/ownership field | Repository transition view, "files changed" derivative | N/A | Fails closed at CERTIFYING if unresolvable |
| Final revision | S (declared, but see §23 for the circularity this creates) + V (verified) | Provenance/ownership field | Repository transition view | N/A | See §23's staged-binding resolution |
| Files changed | D (recomputed from bound source/final revision, R role for the revisions themselves) | Evidence-reference field | Report "files changed" section | Independent `git diff` at report-generation time using unbound revisions | If revisions are unbound, files changed is not computable and must be recorded as unavailable, never empty-by-default |
| Tests | R (reference to suite name, pass/fail counts, run ID — not narrative prose) | Evidence-reference field | Report "Test Results" section | Free-text summary treated as the record of what ran | Unavailable test evidence blocks CERTIFIED (§7.2) unless the record explicitly declares a no-test-required transition type |
| Governance checks | R (same pattern as tests) | Evidence-reference field | Report "Governance Results" section | Free-text narrative treated as the record | Same as tests |
| Report identity | S (once bound) | Identity field | Every derivative that must point at "the" report for this transition | A report matched by filename convention or recency instead of bound identity | Fails closed — no CERTIFIED record without a bound report identity |
| Metadata identity | S (once bound) | Identity field | Same pattern as report identity | Same | Same |
| Architecture Status projection | D | Derived from projected/certified state | The rendered Architecture Status document itself | Independent PROJECT_STATUS.md header re-scanning at any of today's 5+ call sites (135A §3, §9.2) | If the record cannot supply a projection, Architecture Status generation must fail visibly, never silently regenerate from mutable state |
| Snapshot | E | Identity + evidence-reference field | Nothing — the snapshot is sealed at CERTIFIED and referenced, not regenerated | A second, independent certification pass | N/A once sealed; before sealing, absence blocks CERTIFIED |
| Checkpoint | E | Persistence mechanism for in-progress spine position (135A §4.3 — not a spine state) | Crash-recovery reads | An external checkpoint file with independent resume logic, disjoint from the record | Fails closed — if checkpoint state cannot be durably written, the transition cannot proceed past the stage requiring that durability (§8) |
| Promotion | E + D | Transition classification field (spine state) + evidence-reference (artifact identity) | Promoted-artifact derivatives | Artifact inspection used to infer promotion happened, instead of reading the record's PROMOTED state | §16 governs unknown-outcome recovery |
| Notification | R + E | Evidence-reference field (notification identity) + transition classification (spine state) | Notification payload, receipt | Marker-presence treated as proof notification occurred (§19) | §16, §21 govern recovery and retry |
| Marker | D (retired as authority, §19) | N/A — not a record field; a cache derived from NOTIFIED/NOTIFIED_UNCONFIRMED state | Fast local resume-acceleration reads only | Marker treated by any consumer as sufficient proof of terminal state on its own | Missing/stale marker never blocks correctness — it can always be regenerated from the record; it may cause a slower resume path, never an incorrect one |
| Receipt | E | Identity binding (receipt identity field) | Operator-facing delivery evidence | Receipt content re-derived instead of read | §20 governs receipt-specific failure |
| Repository cleanliness | V | Repository-final-state field (§23) | `pcae health`-style live checks | Treating a bound V-role value as still true without re-measurement | A stale cleanliness claim is never treated as current; only the point-in-time binding is authoritative for *that transition's* history |
| Pushed state | V | Repository-final-state field | Same pattern | Same | Same |
| `origin/main..HEAD` | V | Repository-final-state field | Same pattern | Same | Same |

### 3.3 Reading the table

The pattern this table freezes (restating 135A §3's closing paragraph as a binding rule): identity and completion-state facts collapse onto the record as sole (S) or derivative (D) authority; evidence-heavy facts (tests, governance, files changed) remain externally measurable but the record holds the binding reference (R) that says *which* measurement is certified; live repository facts (V) correctly remain live measurements, bound into the record as point-in-time historical facts about the transition, never treated as retroactively or perpetually true.

---

## 4. Sole-authority invariant

### 4.1 The invariant

**A lifecycle fact may have only one authoritative source within a transition.** This is the primary invariant of this contract (formalizing 135A §2.1, §3's closing paragraph, and §6.3). Other representations may reproduce, reference, project, summarize, or verify a fact. They may never independently establish it.

### 4.2 Explicitly prohibited competing-authority patterns

The following are frozen as **forbidden**, effective from the point any implementation of this contract exists (135F onward; not retroactively required of current Track 134 source, per §24):

1. Report status treated as a competing authority to the record's spine state.
2. Metadata status treated as a competing authority to the record's spine state.
3. Architecture Status treated as a competing authority — it is always D (derivative), never S.
4. Marker presence treated as complete lifecycle authority (only a cache/derivative, §19).
5. Receipt presence treated as complete lifecycle authority (E role for its own narrow domain — delivery outcome — never for the transition's overall completion status).
6. Recent Git history (`git log --oneline -N` or equivalent recency-based scans) treated as commit authority.
7. Commit-subject parsing treated as identity authority (subjects remain a contamination *signal*, §10.4, never proof).
8. Active-task inference (from free text, naming, or absence-of-later-completion) treated as post-completion authority.
9. Mutable "latest" files (`latest.md`/`latest.json` or their future equivalents) treated as certification authority — they are always D, sourced from the record's sealed evidence.

### 4.3 Enforcement scope

This invariant governs the *design* frozen by this contract. It does not itself change which artifacts are currently treated as authoritative in production (that remains 134F's already-verified, already-safe status quo, per §24, §25). A future implementation phase (135F onward) is bound by this invariant when it wires the record into any entry point.

---

## 5. Record identity contract

### 5.1 Canonical identifiers

The record introduces or formalizes the following identifier types. Each is defined by **role**, **format constraints**, and **binding rules** — not by a frozen wire encoding (deferred to schema work, §6 preamble).

| Identifier | New or existing (135A) | Role | Binding requirement |
|---|---|---|---|
| `transition_id` | New (135A §9.4) | Uniquely identifies one execution of the lifecycle for one phase/task — finer-grained than phase ID, coarser than any single artifact's own ID | Bound once at PROPOSED; immutable thereafter; every representation of this transition carries it (§11, CLTR-ID-1) |
| `phase_id` | Existing (134A/134B, generalized) | Identifies the governed phase | Bound once at PROPOSED from an unambiguous declared source (134B §4's clause, extended to the record); preserves dotted/multi-dotted/verification-suffix forms without truncation (§5.2) |
| `task_id` | Existing, informally defined today | Identifies the governed task, where applicable | Same binding discipline as `phase_id`; explicitly nullable for phase-only transitions |
| `repository_id` | New (formalizing implicit today) | Identifies the repository the transition is bound to | Bound at PROPOSED; verified against live Git identity at CERTIFYING |
| `report_id` | New (formalizing PFR-001's report as an identified artifact) | Identifies the canonical phase report this transition certifies | Bound at CERTIFIED; immutable thereafter |
| `metadata_id` | New | Identifies the completion metadata this transition certifies | Bound at CERTIFIED |
| `snapshot_id` | Existing (`finalization_snapshot_id`, generalized) | Identifies the sealed evidence snapshot | Bound at CERTIFIED |
| `checkpoint_id` | New (formalizing today's file-keyed checkpoint) | Identifies the in-progress persistence record for this transition (§8, this is a persistence-mechanism identifier, not a spine-state identifier) | Bound at PROPOSED, exists for the life of CERTIFYING/PROMOTING |
| `promotion_id` | New | Identifies one promotion event | Bound at PROMOTED |
| `notification_id` | New | Identifies one notification dispatch attempt | Bound at NOTIFYING; may exist in multiple instances across retries (§17) bound to the same `transition_id` |
| `marker_id` | New (formalizing today's implicit single-marker-per-phase model) | Identifies a derived marker instance | Always bound to exactly one `transition_id`; never independently generated |
| `receipt_id` | Existing (`compute_logical_delivery_id()`, 135A §12) | Identifies one delivery receipt | Bound to exactly one `transition_id` |

### 5.2 Normalization rules

1. **Dotted and multi-dotted phase IDs are preserved exactly**, including verification and corrective suffixes (e.g., `134E.10.1V.1`), per the existing generalized grammar (`architecture_status.py:51`, confirmed current). This contract does not redefine the phase-ID grammar; it freezes that the grammar is applied **once**, at identity-binding time, and never re-derived at each consuming site (135A §9.2).
2. **No truncation** — any parsing that would silently drop trailing components is forbidden for identity binding (135A §9.3, generalizing the 134E.10.1.1 repair from a bug fix to a standing rule).
3. **No fuzzy matching** — an identifier either matches exactly or does not resolve; partial/prefix matches are never treated as a resolution.
4. **No alias resolution unless explicitly declared** — if a transition or phase is ever given more than one display name, exactly one canonical string form must be declared as authoritative; any other form is a display/search convenience only, never an independently resolvable identity (135A §9.3).
5. **Exact identity equality across bound representations** — every representation of a transition (report, metadata, marker, receipt, notification payload) must carry identifiers that compare equal, byte-for-byte, to the record's own bound identifiers. Case-insensitive or whitespace-normalized comparison is permitted only if explicitly declared as part of the normalization rule for that identifier type (matching 134B §7's evidence-normalization discipline); silent case-folding without declaration is forbidden.
6. **Repository binding** — every identifier that is not itself the `repository_id` is implicitly scoped to the `repository_id` bound at PROPOSED; the same `phase_id` string in two different repositories never refers to the same transition.
7. **Transition binding** — every identifier below the transition level (`report_id`, `metadata_id`, `snapshot_id`, `promotion_id`, `notification_id`, `marker_id`, `receipt_id`) is bound to exactly one `transition_id` and never shared across two transitions, even for the same `phase_id` (e.g., a failed attempt and its successful retry are two transitions with two disjoint identifier sets, linked only by sharing the same `phase_id`).
8. **Phase binding where applicable** — `task_id`, when present, is bound to the `phase_id` it was declared under; a `task_id` is never resolved independently of its declaring phase's identity.

### 5.3 Forbidden normalization

1. Silent case-folding of any identifier not explicitly declared case-insensitive.
2. Whitespace trimming that could conflate two distinct declared identifiers.
3. Any normalization that changes an identifier's dotted-segment count or ordering.
4. Treating an identifier's presence in a filename, commit subject, or free-text prose as equivalent to its explicit binding.

---

## 6. Transition record content contract

### 6.1 Preamble — semantic, not wire, requirements

Per 135A §2.3, this section freezes **what the record must be able to answer**, not field names, types, or encodings. A future schema-design phase must satisfy every requirement below; it may choose any concrete representation that does so.

### 6.2 Required semantic content

The record must be able to answer, for the transition it represents:

1. **`schema_version`** — which version of the (future) record schema produced this instance.
2. **`contract_version`** — which version of this contract (CLTR-001) the record conforms to.
3. **`transition_id`** — this transition's unique identity (§5.1).
4. **`transition_type`** — what kind of transition this is (e.g., ordinary phase completion, retry, correction/supersession — the exact enumeration is deferred to schema work, but the record must be able to express at least these three categories).
5. **`phase_id`**, **`task_id`** (nullable) — per §5.1.
6. **`repository_identity`**, **`branch_identity`** — per §5.1, §3.2.
7. **`source_revision`**, **`final_revision`** — per §3.2, §23.
8. **`prior_state`** — the declared/referenced state before this transition (§3.2).
9. **`projected_state`** — the deterministic projection computed at CERTIFYING, frozen at CERTIFIED (§9).
10. **`certified_state`** — the sealed, immutable outcome once CERTIFIED (§3.2).
11. **`transition_status`** — the current spine state (§7).
12. **`phase_commit_ownership`** — the declared and verified commit set (§10).
13. **changed-file evidence** — a binding to source/final revision sufficient to compute files changed (§3.2; not a copy of the diff).
14. **test evidence references** — suite name(s), pass/fail counts, run identity (§3.2; not narrative prose).
15. **governance evidence references** — same pattern as tests, for `pcae health`/`pcae check`/`pcae doctor task-memory`/`pcae push check`/`pcae runtime inspect` results at certification time.
16. **report binding** — `report_id` plus a digest sufficient to detect drift (§15).
17. **metadata binding** — `metadata_id` plus a digest.
18. **Architecture Status binding** — a reference sufficient for the Architecture Status derivative to be regenerated byte-identically (§9.3, §12).
19. **snapshot binding** — `snapshot_id`.
20. **checkpoint binding** — `checkpoint_id`, only meaningful while the transition is in-progress (§8).
21. **promotion binding** — `promotion_id`, once PROMOTED.
22. **notification binding** — `notification_id` (possibly plural across retries, §17).
23. **marker binding** — `marker_id`, once a marker derivative exists.
24. **receipt binding** — `receipt_id`, once a receipt exists.
25. **timestamps** — at minimum: proposed, certified, checkpointed, promoted, notified, terminal (135A §2.2).
26. **failure classification** — per §18, when applicable.
27. **retry classification** — whether and how this transition may be retried (§16).
28. **supersession state** — whether a later correcting transition exists for the same phase/task (§14, §5.7 of 135A).
29. **compatibility metadata** — which contract/schema versions this record's derivatives must remain compatible with (§27).
30. **record digest** — per §15; excludes itself from its own input.

### 6.3 What this section does not freeze

Exact serialization (JSON, structured file, embedded database row, or other) is explicitly out of scope for 135B, per the assignment's non-goals. §6.2's list is the acceptance criterion a future schema must satisfy, not a schema.

---

## 7. State-machine contract

### 7.1 Re-derivation discipline

Per the assignment's instruction, every state below is re-justified from first principles, not retained merely because 135A or the assignment's candidate list named it. 135A §4 already performed this re-derivation once; this contract re-examines that result and freezes it as binding, making one adjustment (§7.4).

### 7.2 Minimum coherent state model (frozen)

The spine, restated from 135A §4.2, is frozen as the binding minimum state model:

```
PROPOSED → CERTIFYING → CERTIFIED → PROMOTING → PROMOTED → NOTIFYING → NOTIFIED → TERMINAL_SUCCESS
                  │            │                      │
                  ▼            ▼                      ▼
          FAILED_PRE_CERT  FAILED_POST_CERT   NOTIFIED_UNCONFIRMED → TERMINAL_PARTIAL_EXTERNAL

Orthogonal (apply to any CERTIFIED-or-later record): QUARANTINED, SUPERSEDED
```

### 7.3 Per-state definitions

For each retained state: entry conditions, exit conditions, permitted next states, forbidden next states, terminality, retryability, canonical-state effect, externally visible effect.

| State | Entry conditions | Exit conditions | Permitted next | Forbidden next | Terminal | Retryable | Canonical-state effect | External visibility |
|---|---|---|---|---|---|---|---|---|
| **PROPOSED** | Transition identity + evidence bindings declared; nothing durable yet | Certification begins | CERTIFYING | Any state other than CERTIFYING | No | N/A (pre-durable) | None yet — no record exists durably | None |
| **CERTIFYING** | Checkpoint/durable marker of "attempt in progress" written | Certification succeeds or fails | CERTIFIED, FAILED_PRE_CERT | PROMOTING, any post-CERTIFIED state | No | N/A (in progress) | Evidence extraction, view composition, rendering, sealed-snapshot check occur; no irreversible effect | None externally visible yet |
| **CERTIFIED** | Sealed-snapshot check, identity check, evidence validation all pass | Promotion begins | PROMOTING | Any pre-CERTIFYING or CERTIFYING-only state (no backward transition) | No | Yes — but see §16 (safe re-entry, not a new attempt at CERTIFYING) | Record digest fixed; evidence bindings immutable | Still no external side effect — this is the last "free to abandon safely" state |
| **PROMOTING** | CERTIFIED reached; artifact promotion + delivery dispatch begins | Promotion+dispatch succeeds or fails | PROMOTED, FAILED_POST_CERT | CERTIFYING, CERTIFIED (no backward) | No | Only via a new record (§16); this record's PROMOTING is never re-entered | May produce partial irreversible external effects | Possibly Y — artifact may become visible before dispatch completes or fails |
| **PROMOTED** | Promotion + dispatch both completed | Notification begins | NOTIFYING | Any state before PROMOTING | No | N/A — promotion itself is never retried once reached (§16) | Artifact promoted; canonical pointer updated (§13) | Y — promoted artifact is externally visible |
| **NOTIFYING** | PROMOTED reached; delivery attempt in progress | Delivery confirmed or unconfirmed | NOTIFIED, NOTIFIED_UNCONFIRMED | Any state before PROMOTED | No | Yes — from NOTIFYING only (§21) | Delivery attempted | Y — external delivery may occur |
| **NOTIFIED** | Delivery confirmed | — | TERMINAL_SUCCESS | Any other state | No (transitions to TERMINAL_SUCCESS) | No — terminal-for-resume (§13.2 of 135A) | Delivery outcome sealed | Y |
| **NOTIFIED_UNCONFIRMED** | Delivery occurred (or is believed to have occurred) but receipt modeling could not confirm it | — | TERMINAL_PARTIAL_EXTERNAL | Any other state, including back to NOTIFYING (delivery itself is never re-attempted from here, §5.6 of 135A) | Terminal-ish (terminal for delivery re-attempt; only receipt reconciliation may proceed, §20) | Only receipt-modeling retry, never delivery retry | Delivery believed irreversible; receipt bookkeeping incomplete | Y — the underlying delivery already happened |
| **TERMINAL_SUCCESS** | NOTIFIED reached | — | (none — orthogonal QUARANTINED/SUPERSEDED only) | Any spine state | Yes | No | Fully sealed | Y |
| **TERMINAL_PARTIAL_EXTERNAL** | NOTIFIED_UNCONFIRMED reached and not reconciled to NOTIFIED | — | (none — orthogonal QUARANTINED/SUPERSEDED only) | Any spine state | Yes | No (as a transition; receipt reconciliation is not a spine retry, §20) | Fully sealed with a disclosed gap | Y |
| **FAILED_PRE_CERT** | CERTIFYING fails before CERTIFIED | — | (none — orthogonal QUARANTINED/SUPERSEDED only, rarely applicable) | Any spine state, especially PROMOTING | Yes | Yes, freely, via a **new** record (no side effects occurred) | None — nothing durable beyond the failed attempt | N |
| **FAILED_POST_CERT** | PROMOTING fails after CERTIFIED | — | (none — orthogonal QUARANTINED/SUPERSEDED only) | Any spine state, especially back to CERTIFIED (the CERTIFIED record is never reversed, §5.5 of 135A) | Yes-ish (terminal for this record; a new record may retry the transition) | Only via a **new** record, and only after the observation discipline of §16.3 | CERTIFIED evidence remains sealed and valid; this record does not proceed further | Possibly Y, if partial promotion occurred |
| **QUARANTINED** (orthogonal) | Independent post-hoc integrity verification finds the record's bound evidence no longer matches its digest, or a derivative drifted | Human review resolves it | N/A (orthogonal, does not re-enter the spine) | N/A | N/A (a flag, not a spine terminus) | N/A | Record flagged untrusted; content not deleted | Y — flagged as untrusted |
| **SUPERSEDED** (orthogonal) | A later, correcting transition record exists for the same phase/task | — | N/A (orthogonal) | N/A | N/A | N/A | Record annotated as superseded; content not deleted or rewritten | Y — annotated |

### 7.4 Adjustment from 135A's candidate list

135A §4.3 already excluded `CHECKPOINTED` as a spine state (reclassified as a persistence mechanism, §8) and folded `retryable`/`terminal_success` into per-state properties rather than nodes. This contract freezes that reduction and makes one further explicit ruling: **`receipt_complete` is not a spine state.** It is a property of the NOTIFIED state (receipt modeling succeeded) and is represented as part of that state's completeness, not as a separate spine node — introducing it as a distinct state would require a transition from NOTIFIED to `receipt_complete` that has no distinguishable entry/exit semantics from NOTIFIED itself, violating the minimality principle 135A §4.3 already established for `CHECKPOINTED`.

---

## 8. Transition-order contract

### 8.1 Mandatory ordering (frozen)

1. Authoritative input binding (identity, evidence references declared)
2. Identity resolution (§5)
3. Explicit commit ownership validation (§10)
4. Projected state construction (§9)
5. Canonical semantic preparation (evidence extraction, view composition — 134B's Stages 6–7)
6. Cross-representation consistency validation (sealed-snapshot-style check, generalized per 135A §7.2)
7. Certification (→ CERTIFIED)
8. Checkpoint (durable persistence of CERTIFIED state, §8 of this contract — see §8.3 below on ordering relative to CERTIFIED itself)
9. Promotion (→ PROMOTED)
10. Notification (→ NOTIFYING/NOTIFIED/NOTIFIED_UNCONFIRMED)
11. Marker persistence (derivative cache write)
12. Receipt persistence (E-role immutable event)
13. Final transition closure (→ TERMINAL_SUCCESS or TERMINAL_PARTIAL_EXTERNAL)

### 8.2 Ordering invariants

1. **No checkpoint before certification** — a durable "CERTIFIED" checkpoint entry cannot exist before the certification checks (steps 1–7) have actually passed.
2. **No promotion before checkpoint** — PROMOTING cannot begin unless the CERTIFIED state is durably persisted first (so a crash during PROMOTING can be recovered against a known-good CERTIFIED record, per §8's persistence architecture).
3. **No terminal notification before promotion** — NOTIFIED/NOTIFIED_UNCONFIRMED cannot be reached without first passing through PROMOTED.
4. **No marker before required delivery classification** — a marker derivative may only be written once the record has reached NOTIFIED or NOTIFIED_UNCONFIRMED (§19); a marker written from an earlier state would misrepresent terminality.
5. **No receipt claiming completion before actual stage completion** — a receipt's claimed outcome must match the record's actually-reached spine state at the time the receipt is modeled (§20; this generalizes the existing "read delivery success from the real promoted report, never the pre-promotion trial" discipline, 135A §12).
6. **No post-certification mutable read may redefine the transition** — once CERTIFIED, every subsequent stage reads only the sealed record, never re-scans mutable repository/PROJECT_STATUS.md state to change what the transition "is."
7. **No irreversible stage may occur before semantic validation** — PROMOTING (the first stage with potential irreversible external effect) may never begin before step 6 (cross-representation consistency validation) has passed.

### 8.3 Note on checkpoint vs. CERTIFIED ordering

§8.1 step 8 ("Checkpoint") is listed after "Certification" (step 7) for narrative clarity, but per §7.4 and §8.2 invariant 1, the checkpoint's durable write of the CERTIFIED state is not a separate semantic stage — it is the *mechanism* by which CERTIFIED becomes crash-durable (§8 of this contract, persistence architecture). No transition may proceed to PROMOTING while CERTIFIED exists only in memory and not yet durably persisted.

---

## 9. Projected-state contract

### 9.1 Requirements (frozen from 135A §7)

Projected post-transition state:

**Must:**
1. derive only from authoritative transition inputs (declared identity, declared prior state, declared recommended successor — never from mutable state re-scanned later);
2. represent the intended state after successful completion;
3. be deterministic — a pure function of the record's CERTIFYING-time inputs, no I/O, no randomness (135A §6);
4. be complete enough to generate Architecture Status without any additional live lookup;
5. remove the completed phase from active state;
6. never activate a planned successor (a successor becomes active only via its own future CERTIFIED record, §9.4 below);
7. remain stable after certification — no later derivative may compute a different projection for the same record (135A §7.2's "sealed-snapshot" discipline, generalized);
8. be bound into the transition record (§6.2, item 9);
9. be used consistently by every production entry point once implemented (a future-phase obligation, not a 135B constraint on current source).

**Must not:**
1. read mutable latest state after certification;
2. infer activity from report presence;
3. infer activity from phase naming;
4. regenerate independently for each derivative (one projection, computed once, referenced by all derivatives);
5. silently diverge from report or metadata state — any detected divergence is a QUARANTINE-triggering event (§7.3), not a value to be reconciled by picking one side.

### 9.2 Advisory-to-authoritative transition

Projected state is **advisory** while CERTIFYING (a plan, not yet certified — may still change if certification fails) and **authoritative** from CERTIFIED onward (sealed; 135A §7.2, generalizing the existing sealed-snapshot re-check).

### 9.3 Known-failure-mode prevention (frozen, restating 135A §7.3 as binding requirements)

1. A completed transition's phase must never appear in any derivative's "active"/"in progress" classification — enforced because "active" derivatives read only the most recent record's projected state, never re-scan PROJECT_STATUS.md headers.
2. A planned successor must never be classified active by any derivative until its **own** transition record reaches CERTIFIED or later — "recommended successor" and "current/active phase" must never be the same field or conflated by any derivative.
3. No derivative may live-query PROJECT_STATUS.md or `.last-notified.json` for a fact the record already owns, once CERTIFIED.
4. Regeneration of a derivative must reproduce byte-identical output from the same sealed record; any divergence is a derivation bug, never a signal to "regenerate from current state instead."
5. Active-phase determination is a lookup against the record's own identity/status fields, never a heuristic over report titles, filenames, or prose.

### 9.4 Successor activation rule

Restating explicitly: a phase becomes "active" **only** by virtue of its own transition reaching PROPOSED-or-later in the record model — never by being named as another transition's "recommended successor." This is the structural answer to the premature-activation failure mode named in the assignment.

---

## 10. Commit-ownership contract

### 10.1 Declaration and verification lifecycle

1. **Who declares**: phase-owned commits are declared at PROPOSED, by the same authoritative input source that declares phase/task identity (i.e., not inferred, not left to a default).
2. **When ownership becomes authoritative**: the declared set is bound into the record at CERTIFIED, after verification at CERTIFYING (§10.4) has classified every declared commit.
3. **Validation against repository identity**: each declared commit hash is checked against the record's bound `repository_identity` — a hash that resolves in a different repository is not treated as belonging to this transition.
4. **Validation that hashes exist**: each hash must be looked up (e.g., `git log -1 <hash>`) against the bound repository/revision context.
5. **Validation that commits belong to the expected repository**: same as item 3, stated for clarity as a distinct required check.
6. **Ordering requirements**: declared commits are an unordered *set* for ownership purposes (135A §10.2 — "a set, not a scalar"); no ordering claim is made or required by this contract for ownership verification (ordering *within* revision history is a separate, already-existing concern, unaffected by this contract).

### 10.2 Cases addressed (frozen enumeration)

1. **No-commit phases** — an explicitly empty commit set is a valid, first-class declaration (e.g., pure documentation/architecture phases like 135A and this phase, 135B). No implicit default reached by falling through an unhandled case; no silent `git log` fallback when no commits are declared (135A §10.2, generalizing the 134E.10.1.1 repair to a standing rule).
2. **One-commit and multiple-commit phases** — both representable without special-casing; the ownership field is always a set.
3. **Documentation-only completion commits, repair commits, verification-only commits** — the record must be able to classify *why* a commit belongs to the transition, so ownership verification can apply appropriately different expectations (e.g., a verification-only phase legitimately owning zero source-changing commits). The exact classification enumeration is deferred to schema work (§6.3), but this contract freezes that the *capability* to classify is required.
4. **Prior-phase commits and unrelated commits** — must never be attributable to the current transition merely by recency; this generalizes `detect_cross_phase_commit_contamination()`'s existing defense (confirmed current at `phase_reports.py:1819-1870`) into a standing invariant rather than a single check at one call site.

### 10.3 Fabricated hashes — future obligation, not repaired here

**135B does not repair the current fabricated-hash behavior** (confirmed unchanged in current source: `phase_reports.py:1851-1859` silently `continue`s past an unresolvable hash, collapsing "unverifiable" into "verified" by omission). This contract instead freezes the **future** obligation: every claimed commit hash must resolve to exactly one of three distinct, recorded outcomes.

### 10.4 Three-outcome verification contract (frozen)

1. **verified** — the hash exists, resolves within the bound repository/revision context, and its subject does not name a different phase.
2. **contaminated** — the hash exists but its subject (or other available metadata) indicates it belongs to a different phase.
3. **unverifiable** — the hash cannot be resolved against the bound repository identity/revision (nonexistent, synthetic/test hash, lookup error, or timeout).

**Binding rule**: `unverifiable` must always be a distinct, recorded outcome — it must never be silently treated as equivalent to `verified`. Whether `unverifiable` is then treated as blocking, warning, or informational is an explicit **governance policy decision deferred to 135D** (per 135A §10.3) — this contract only freezes that the record must be *able* to represent the distinction, which today's flat pass/fail check cannot.

---

## 11. Evidence-binding contract

### 11.1 Classification of each evidence category

| Evidence | Classification | Requirement |
|---|---|---|
| Changed files | Derived summary (D), computed from bound source/final revision (R) | Never stored redundantly as a copy; always computable from the two bound revisions |
| Test results | Referenced evidence (R) | Suite name, pass/fail counts, run ID — never narrative prose as the sole record |
| Governance checks | Referenced evidence (R) | Same pattern as tests — structured references, not narrative summaries |
| Runtime state | Referenced evidence (R), bound at CERTIFYING time | A snapshot of `pcae runtime inspect`'s output at certification time, not a live re-query later |
| Report completeness | Derived summary (D) | The record holds *whether certification passed*; the report's own PFR-001 completeness check remains a derivation input, not duplicated as record content (135A §3 row) |
| Report consistency | Verification-only observation (V), standing verification against the record's frozen evidence bindings | Generalizes `validate_derived_correctness` from an ad hoc re-run to a standing check against a fixed anchor (135A §3 row) |
| Notification outcomes | Immutable evidence reference (E) once recorded | Bound to `notification_id`; never overwritten, only appended to across retries (§17) |
| Repository cleanliness | Verification-only observation (V) | Point-in-time measurement, bound as historical fact about the transition (§23) |
| Push state | Verification-only observation (V) | Same pattern |

### 11.2 Prohibition on prose-as-evidence

Report prose (free-text narrative in any section of the canonical phase report) may never serve as the **sole** evidence for a fact classified R or E above. Prose may explain or contextualize a fact; it may never be the only place a fact is recorded. This directly addresses the PFN-001/PFR-001-adjacent risk that a well-written narrative could substitute for structured, verifiable evidence.

---

## 12. Derived-representation contract

### 12.1 Per-derivative binding table

For each derivative, restating and freezing 135A §6.2's derivation map as binding requirements — source fields, identity binding, digest binding, permitted additional presentation fields, prohibited independent inference, and consistency/verification requirements:

| Derivative | Source fields | Identity binding | Digest binding | Permitted additions | Prohibited independent inference | Consistency requirement |
|---|---|---|---|---|---|---|
| Canonical phase report | Evidence-reference fields + referenced evidence, fetched by reference | `report_id` | Report content digest bound in record | PFR-001-required prose, formatting | Completion status, notification result (both come from record's transition state) | Must reproduce byte-identical output from the same sealed record on regeneration |
| Completion metadata | Identity + classification fields | `metadata_id` | Metadata digest bound in record | None beyond structured fields already in metadata's own schema | Phase/task identity (never re-parsed from free text) | Same as report |
| Architecture Status | `phase_id` + transition status + projected post-transition state | Reference to `transition_id` for the most recent record per phase | Not separately digested — regenerable at will from the record | Formatting, grouping by track | Current/In Progress/Planned classification (must read record's projected state, never re-scan PROJECT_STATUS.md headers) | Regeneration must be idempotent — same record, same output |
| Immutable snapshot | CERTIFIED-state evidence bindings, sealed at the same moment the record enters CERTIFIED | `snapshot_id` | Snapshot digest bound in record | None — the snapshot *is* the record's certified evidence | Nothing — no second independent certification | Snapshot content never diverges from the record it was sealed with |
| Checkpoint | Record's own in-progress spine position | `checkpoint_id` | N/A — checkpoint is a persistence mechanism, not a separately-digested artifact | None | N/A | Checkpoint state must always be reconstructible as a prefix of the record's own eventual history |
| Promoted "latest" report/metadata | PROMOTED-state binding, one atomic write (§13) | `report_id`/`metadata_id` bound at CERTIFIED, carried through | Same digests as the CERTIFIED artifacts | None — content always sourced from sealed evidence | The report/metadata content itself — never regenerated post-hoc from different inputs | Must always reflect exactly one CERTIFIED record, never a mix (§13) |
| Notification payload | NOTIFYING-state evidence bindings | `notification_id` | Bound to the record's evidence digest at PROMOTED | Audience-specific formatting for the delivery sink | Delivery success/failure (this is an observation written back into the record, §16.3, never a payload-generator decision) | Payload content must trace to exactly one PROMOTED record |
| Completion marker | NOTIFIED/NOTIFIED_UNCONFIRMED state | `marker_id` bound to `transition_id` | Reference to record digest, for staleness detection | Human-readable timestamp/summary | Terminal-ness — never the thing a consumer checks to decide resume behavior instead of the record (§19) | Marker content must be regenerable from the record at any time |
| Finalization receipt | Receipt identity binding | `receipt_id` bound to `transition_id` | N/A — receipts are their own immutable event class | None beyond receipt's own existing structure | Nothing — receipts are bound to but not derived in content from the record | Receipt and record must agree on which `transition_id` they describe (§11, invariant CLTR-MARKER/RECEIPT) |
| Git attribution view | Commit-ownership fields, verified against live Git at CERTIFYING time | `transition_id` | N/A | Presentation of verification outcome per commit | Nothing new — generalizes existing contamination detection | Must reflect the same three-outcome classification as §10.4 |
| Repository transition view | Source/final revision bindings | `transition_id` | N/A | Presentation only | "What changed" is always computable from the two bound revisions, never stored redundantly | Must be reproducible from the two bound revisions at any time |

### 12.2 General derivation principle (frozen from 135A §6.1)

Every derived representation must be producible by a **pure function** of `(canonical transition record, the evidence it binds to by reference)`. No derivation function may consult any *other* derivative to reconstruct a fact the record itself does not carry.

### 12.3 The no-independent-reconstruction rule (frozen from 135A §6.3)

If a future derivative needs a fact the record does not carry, the correct remedy is to add that fact (or a reference to it) to the record's schema in a future schema-freeze phase — never to let the derivative infer it from context, naming convention, or a sibling artifact.

---

## 13. Atomic-visibility contract

### 13.1 Required external visibility invariant

**Consumers must never observe a mixed-generation canonical report and metadata pair.** This is defined independent of implementation (135A §8.3 explicitly declines to select a mechanism; this contract preserves that deferral).

### 13.2 Possible compliant mechanisms (non-binding menu, per 135A §8.3)

Single canonical record plus generated views; manifest-controlled generation; transactional local store; single canonical record plus generated views; atomic promotion unit (directory swap or pointer switch). This contract does not choose among these. The candidate most consistent with §12.2's derivation principle — single canonical record plus derived files — is worth weighting first when a future phase makes the freeze decision, per 135A §8.3, but that decision remains explicitly deferred to 135D or later.

### 13.3 Frozen outcomes (binding regardless of mechanism)

1. **All-or-nothing visibility** — any reader sees either the fully-old or fully-new state of the current pointer, never a mix.
2. **Generation identity** — each atomic promotion is itself identifiable (e.g., bound to a `transition_id`), so a reader can determine *which* transition's output it is looking at.
3. **Cross-file binding** — if the record's canonical representation spans more than one file, all files become visible together or not at all.
4. **Partial-write detection** — a reader must be able to distinguish "no write attempted" from "write attempted but truncated/corrupted."
5. **Deterministic recovery** — recovery from a partial or interrupted promotion must be deterministic, not dependent on timing or retry count.
6. **Stale-pointer detection** — a reader must be able to detect that the current pointer refers to a generation older than the most recent immutable history entry (§8's mutable-pointer-recovery requirement).

### 13.4 Relationship to the current non-atomic gap

135A §8.2 (re-confirmed current in 135B's own research pass: `canonical_artifact_promotion.py:109-116` still writes `latest.md`/`latest.json` via two independent `path.write_text()` calls) is **not repaired by this contract**. §13.3's invariants are the binding target a future implementation phase must satisfy; they do not retroactively apply to current production behavior (§24).

---

## 14. Immutable-history contract

### 14.1 Frozen requirements

1. **Append-only transition history** — every CERTIFIED-or-later record is permanent; the record's own internal event sequence (§2 of 135A, "hybrid" model) is append-only.
2. **Immutable certified record** — once CERTIFIED, a record's evidence bindings and digest never change; corrections happen via a **new** record referencing the same phase/task, never by mutating the existing one (§16).
3. **Immutable historical reports** — a report that was promoted as canonical for a given transition is never rewritten in place.
4. **Immutable historical metadata** — same pattern.
5. **Immutable historical snapshots** — same pattern.
6. **No rewriting of past evidence** — evidence bound by reference at CERTIFYING is never altered after the fact; if the underlying external evidence (e.g., a Git commit) is somehow found to be wrong, the *binding* is what gets superseded (a new transition), not the historical record's claim about what it bound to.
7. **Explicit supersession rather than mutation** — corrections are annotations (SUPERSEDED, §7.3) pointing to a newer transition, never in-place edits.
8. **Digest verification** — any modification to a sealed record's bound evidence must be detectable via digest mismatch (§15).
9. **Cross-transition substitution rejection** — a reader must reject (or flag as QUARANTINED) any derivative whose bound identifiers resolve to a different transition than claimed.

### 14.2 Relationship to 134B's historical-preservation invariant

This section generalizes 134B's existing "historical preservation, correction-only after Completed" invariant (135A §5.7) from Track 134's specific artifacts to the record concept as a whole. It does not amend 134B.

---

## 15. Digest contract

### 15.1 Conceptual requirements (frozen)

1. **Deterministic canonicalization** — the same logical record content always produces the same digest input, regardless of incidental serialization differences (key ordering, whitespace) — mirroring 134B §7's Evidence Normalization Contract discipline, applied to the record's own digest computation.
2. **Algorithm** — SHA-256, unless a future schema-design phase justifies a different existing standard (this contract does not invent a new digest algorithm).
3. **Self-exclusion** — the digest field excludes its own value from its input (a digest cannot include itself).
4. **Full-content binding** — the digest binds all authoritative record content (every S, R, and E role field per §3), not a subset.
5. **Derivative binding includes transition identity** — every derivative that carries a digest reference must also carry the `transition_id` it is bound to; a digest alone, without transition identity, is insufficient to prevent cross-transition substitution (§14.1 item 9).
6. **Tamper detection** — any modification to a sealed record's bound evidence must change the digest, making tampering detectable by comparison.
7. **Stale or cross-phase substitution must fail verification** — a derivative presenting a digest that does not match its claimed record must be rejected or quarantined (§7.3, §18), never silently accepted.

### 15.2 What this section does not freeze

Exact byte-level canonical serialization is not defined here (135A §8.3-style deferral, per the assignment's instruction not to define exact byte serialization unless required for contract clarity — it is not required here, since §15.1's requirements are sufficient to constrain a future schema without prescribing one).

---

## 16. Retry and resume contract

### 16.1 Principle

Restating 135A §13.1 as binding: every resume decision must be answerable by reading the record's own current spine state, never by an entry point independently checking a marker, a receipt store, or a checkpoint file and inferring what must have happened. This is the direct structural resolution of 134F's central disclosed gap.

### 16.2 Resolution of the 134F resume gap (explicit, binding)

**134F's central finding, re-confirmed present in current source during 135B's own research** (`finalization_transaction.py:601`, `existing.get("status") == "completed"` is the *only* condition treated as resumable/terminal — `completed_receipt_best_effort_incomplete` does not satisfy it): this contract freezes that the **core transition authority itself** — not only entry-point marker checks — must classify the record's equivalent state (**NOTIFIED_UNCONFIRMED**, §7) as resume-terminal.

**Binding classification**: NOTIFIED_UNCONFIRMED is:
- **terminal** for the purposes of re-attempting PROMOTING or NOTIFYING — a resumed transition reaching a record in this state must never re-invoke promotion or delivery;
- **terminal with incomplete best-effort external work** — the underlying delivery is treated as already-occurred and irreversible; only the receipt-modeling bookkeeping is incomplete;
- **recoverable only for specific derivative repair** — recovery from this state means re-attempting receipt modeling/reconciliation only (§20), never re-attempting delivery;
- **forbidden for ordinary completion replay** — a second PROPOSED transition for the same phase/task while an existing record sits in NOTIFIED_UNCONFIRMED (or any terminal-ish state) must be rejected as a duplicate (§17.2), not silently accepted as a fresh attempt.

### 16.3 Recovery by record state (frozen, restating 135A §13.2)

| Re-entry point | Required behavior |
|---|---|
| Before CERTIFIED | Safe to retry from scratch; no side effects to account for |
| After CERTIFIED, before PROMOTING started | Safe to proceed to PROMOTING; sealed evidence remains valid, no re-certification needed |
| After PROMOTING started, outcome unknown (crash mid-stage) | Requires an explicit **observation step** before any retry decision — never assume PROMOTING did or did not complete; check actual external state first |
| After PROMOTED | PROMOTING must never be re-attempted; only NOTIFYING may proceed or be re-attempted |
| After NOTIFYING started, outcome unknown | Same observation discipline as PROMOTING — check actual delivery-sink state where feasible, or bound the ambiguity explicitly |
| After NOTIFIED or NOTIFIED_UNCONFIRMED | Both terminal-for-resume; §16.2 |
| Incomplete receipt | Retry only the receipt-modeling step, bound to the existing record, never touching PROMOTING/NOTIFYING |
| Best-effort external failure | Recorded as NOTIFIED_UNCONFIRMED; recovery is reconciliation (confirm delivery via an independent signal, then upgrade to NOTIFIED) or acceptance of TERMINAL_PARTIAL_EXTERNAL — never a silent retry of delivery |
| Repeated invocation | Idempotent at every spine state (§17.1) |
| Crash between durable writes | Bounded by §8's durability/write-ordering requirements — "between durable writes" must always be a well-defined, detectable state |
| Stale current pointer | Recoverable from immutable history (§13.3 item 6) |

### 16.4 Observation discipline (frozen from 135A §5.5)

Recovery logic must never *infer* what happened by re-executing PROMOTING or NOTIFYING; it must **observe** actual external state (was the artifact promoted? was delivery sent?) and record a new, separate observation event before deciding whether a new record's PROMOTING/NOTIFYING may safely proceed. This generalizes the existing sealed-snapshot/receipt-honesty design (delivery success is read back from the real promoted report, never a pre-promotion trial) into a standing recovery discipline.

---

## 17. Duplicate and replay contract

### 17.1 Idempotent re-entry

The same PROPOSED transition submitted again with identical evidence bindings must, at any point after CERTIFIED, resolve to the existing record's current state without re-executing PROMOTING (generalizing today's resume check, extended per §16.2 to recognize NOTIFIED_UNCONFIRMED as terminal-for-resume).

### 17.2 Duplicate ordinary completion

A second, distinct PROPOSED transition for a phase/task the record already shows TERMINAL_SUCCESS (or TERMINAL_PARTIAL_EXTERNAL, or any other terminal-ish state) for is a data-entry/governance error, not a resume. It must be **rejected** at PROPOSED with a reference to the existing terminal record, never silently accepted as a new success.

### 17.3 Exact replay

Re-submitting an old CERTIFIED record's evidence unchanged, before any newer record exists for the same phase/task, is idempotent re-entry (§17.1) — resolved to the existing record's state, not treated as a new attempt.

### 17.4 Conflicting replay

Re-submitting evidence that differs from an existing CERTIFIED-or-later record's bound evidence, for the same `transition_id`, is a conflict — this must be rejected, never silently overwritten (this generalizes §14's immutability requirement to the replay case specifically).

### 17.5 Cross-phase replay

Evidence or identifiers that resolve to a different phase than declared must be rejected at identity resolution (§5), never accepted under the submitting transition's claimed identity.

### 17.6 Retry after partial external failure

Governed by §16.2's NOTIFIED_UNCONFIRMED classification and §16.4's observation discipline — never a bare retry.

### 17.7 Retry after promotion / after marker / after receipt

Promotion is never retried once PROMOTED (§7.3); marker/receipt "retry" means regeneration/reconciliation of the derivative, never re-triggering the underlying stage (§16.3).

### 17.8 Superseded transition replay

Re-submitting evidence for a transition that has been superseded (§7.3, §14) must be rejected with a reference to the superseding record.

### 17.9 Decision table (frozen)

| Case | System must |
|---|---|
| Exact replay of CERTIFIED-or-later evidence, no newer record exists | Return prior result (resolve to existing state) |
| Re-entry after crash, no evidence conflict | Resume (per §16.3) |
| Conflicting replay for the same `transition_id` | Reject |
| Cross-phase replay | Reject |
| Retry after partial external failure | Observe, then reconcile or accept TERMINAL_PARTIAL_EXTERNAL — never bare retry |
| Retry after PROMOTED | Reject re-promotion; permit only NOTIFYING-stage retry |
| Retry after marker/receipt only | Regenerate/reconcile the derivative, do not re-trigger the underlying stage |
| Superseded transition replay | Reject, reference the superseding record |
| Any case where the correct outcome is ambiguous from recorded state alone | Quarantine and require human review — never guess |

---

## 18. Failure contract

### 18.1 Per-failure-class requirements (frozen, restating and completing 135A §12)

For each failure class: canonical-state effect, derivative-state effect, external visibility, retryability, terminality, evidence retention, quarantine requirement, human-review requirement.

| Failure class | Canonical-state effect | Derivative-state effect | External visibility | Retryable | Terminal | Evidence retention | Quarantine | Human review |
|---|---|---|---|---|---|---|---|---|
| Missing authority (declared identity/evidence references don't resolve) | None durably recorded (rejected before PROPOSED persists) | None | No | Yes, freely | N/A — never entered the spine | Rejected proposal, for audit | No | No, unless repeated |
| Identity conflict (ambiguous/malformed ID) | None | None | No | Yes, freely | N/A | Malformed input | No | No, unless repeated |
| Commit ownership conflict (contaminated or unverifiable, §10.4) | Partial — outcome noted; transition may proceed or block per governance policy (135D) | Depends on policy | Depends on policy | Yes, freely if pre-CERTIFIED | No, unless policy makes it blocking | Hash and resolution attempt | Yes if unverifiable and policy treats it as suspicious | Yes if unverifiable and policy treats it as suspicious |
| Semantic mismatch (sealed evidence contradicts declared identity) | None (fails at CERTIFYING, before CERTIFIED) | None | No | Yes, freely | Yes (FAILED_PRE_CERT) | Contradiction detail | No | No, unless repeated |
| Certification failure (rendering/composition exception) | None | None | No | Yes, freely | Yes (FAILED_PRE_CERT) | Exception detail | No | No, unless repeated |
| Checkpoint failure (durable write itself fails) | Ambiguous, resolved by §8's durability guarantees | Depends on whether prior durable state exists | No, if write never completed | Yes | Depends on prior durable state | Partial write, for forensic inspection | No | Yes if durability cannot be confirmed on restart |
| Promotion failure | Record reaches FAILED_POST_CERT; CERTIFIED evidence remains sealed | Possibly affected if partial promotion occurred | Possibly Y | Only via new record, never re-running this record's PROMOTING | Yes-ish (terminal for this record) | Full CERTIFIED evidence plus observed partial-promotion state | Yes, if partial external state is ambiguous | Yes |
| Notification failure (delivery itself fails) | Record notes NOTIFYING failed | — | Y (delivery genuinely did not happen) | Yes, retry NOTIFYING for the same PROMOTED record | No — not terminal until delivery is confirmed one way or the other | Delivery attempt evidence | No | Only if repeated |
| Marker failure (marker write fails) | None to the record — marker is a derivative | N to record's state; Y to marker-dependent legacy readers until regenerated | N to record | Yes — regenerate from record | No | Record itself remains source of truth regardless | No | No, unless marker can never be regenerated |
| Receipt failure (best-effort modeling incomplete) | Record reaches NOTIFIED_UNCONFIRMED | — | N — underlying delivery already succeeded | Retry receipt modeling only, never delivery | Yes-ish (TERMINAL_PARTIAL_EXTERNAL) | Delivery evidence that did succeed | No | Only if receipt can never be reconciled |
| Atomic visibility failure (mixed-generation exposure, §13) | None to the record | Y — a derivative was wrong and must be regenerated | Y | N/A — regenerate the derivative | N/A | Which record the stale derivative actually matched | No, unless already externally delivered | Only if externally delivered |
| Digest failure (record's bound evidence no longer matches its digest) | None — record content not rewritten | Y — flagged, not silently trusted | Y | N/A | N/A | Mismatch details, both digests | Yes, always | Yes, always |
| Replay conflict (§17.4) | None — rejected | None | No | N/A — rejected, not retried | N/A | Rejected replay attempt | No | Only if replay appears adversarial/repeated |
| Duplicate completion (§17.2) | None — rejected at PROPOSED | None | No | N/A — rejected | N/A | Rejected duplicate proposal, referencing existing terminal record | No | Yes — indicates governance-process error |
| Stale derivative (§13, §17.9) | None to the record | Y — the derivative is wrong | Y | N/A — regenerate | No, unless externally delivered | Which record the stale derivative matched | No, unless externally delivered | Only if externally delivered |
| Cross-phase substitution | None if caught at CERTIFYING (rejected); Y if caught later (quarantine) | Y once discovered | Y once discovered | Depends on when caught | Depends | Substitution details | Yes if discovered post-hoc | Yes, always |
| Repository-state mismatch (V-role fact no longer matches at a later read) | None to the historical binding | N/A | Y — flagged as stale, never silently treated as current | N/A — re-measure | N/A | The measured-at-certification value, retained as historical fact | No | No, unless the mismatch is itself suspicious |

---

## 19. Marker contract

### 19.1 Marker status (frozen)

The marker (e.g., today's `.last-notified.json` or its future equivalent) must **not** be an independent lifecycle authority. It is classified as:
- a **terminal-state derivative** (regenerable from the record's NOTIFIED/NOTIFIED_UNCONFIRMED state);
- a **replay accelerator** (a fast local cache that lets a resume decision skip re-reading the full record when the marker agrees, but never substitutes for reading the record when the marker is absent, stale, or in doubt);
- a **compatibility signal** (existing entry points, before they are migrated to read the record directly, may continue to consult the marker during a transition period, §24, §25);
- a **verification aid** (a mismatch between marker and record is itself a useful QUARANTINE-triggering signal, never something to silently reconcile in the marker's favor).

### 19.2 Requirements

1. **Required identity binding**: `marker_id` bound to exactly one `transition_id`.
2. **Transition binding**: the marker must state which transition it derives from; a marker with no transition binding is invalid.
3. **Digest or record reference**: the marker carries a reference sufficient to detect staleness against the record.
4. **Creation timing**: only once the record has reached NOTIFIED or NOTIFIED_UNCONFIRMED (§8.2 invariant 4).
5. **Replay behavior**: a marker's presence may short-circuit a resume decision only when it agrees with the record; it must never be trusted in isolation.
6. **Missing-marker behavior**: never blocks correctness — regenerate from the record.
7. **Stale-marker behavior**: detected via digest/reference mismatch (§19.2 item 3); treated as a signal to regenerate, not a governing fact.
8. **Fabricated-marker behavior**: a marker whose bound `transition_id` does not resolve to any known record, or whose digest does not match, must be rejected — never trusted as evidence a transition occurred.

---

## 20. Receipt contract

### 20.1 Receipt status (frozen)

The receipt remains an immutable event record (E role, §3.1) for its own narrow domain — delivery outcome. It must accurately represent completed and incomplete stages; it must never claim successful completion for a stage that did not occur.

### 20.2 Requirements

1. **Required transition binding**: `receipt_id` bound to exactly one `transition_id`.
2. **Report binding**: reference to the `report_id` the receipt's outcome pertains to.
3. **Metadata binding**: reference to the `metadata_id`.
4. **Commit binding**: reference to the commit-ownership outcome (§10.4) at the time of receipt.
5. **Promotion outcome**: whether promotion succeeded, per the record's PROMOTED-or-later state.
6. **Notification outcome**: whether notification succeeded, per NOTIFIED/NOTIFIED_UNCONFIRMED.
7. **Marker outcome**: whether a marker was successfully derived.
8. **Terminal classification**: which terminal state (TERMINAL_SUCCESS or TERMINAL_PARTIAL_EXTERNAL) the receipt corresponds to.
9. **Best-effort incomplete classification**: an explicit flag distinguishing "fully confirmed" (NOTIFIED) from "best-effort, unconfirmed" (NOTIFIED_UNCONFIRMED) receipts.
10. **Retry information**: whether the receipt itself has been reconciled/updated since first written, and how many times.
11. **Digest/reference requirements**: sufficient to bind the receipt to the exact record content it attests to (§15.1 item 5).

### 20.3 Prohibition

The receipt must never claim successful completion for a stage that did not occur — this generalizes the existing "read delivery success from the real promoted report, never the pre-promotion trial" discipline (135A §12, confirmed current in `finalization_transaction.py`'s post-dispatch receipt modeling) into a standing contractual requirement.

---

## 21. Notification contract

### 21.1 PFN-001 preservation (frozen)

This contract does not amend PFN-001. It freezes how the future record relates to PFN-001's existing guarantees:

1. **One governed terminal external delivery** — per PFN-001's exactly-once guarantee; the record's NOTIFYING/NOTIFIED/NOTIFIED_UNCONFIRMED stages track *when and whether* delivery is attempted/confirmed, without introducing a second delivery mechanism.
2. **Notification after promotion** — NOTIFYING may only begin from PROMOTED (§8.2 invariant 3).
3. **Notification payload derived from promoted canonical evidence** — never from independently re-gathered "current" evidence at notification time (§12.1 row).
4. **No test external delivery** — this contract does not change PFN-001's `PCAE_NOTIFY_ENABLED`/sink-isolation discipline; test/CI runs remain non-dispatching per existing conventions.
5. **No duplicate ordinary terminal delivery** — per §17.1's idempotency requirement.
6. **Explicit retry classification** — per §16.2, §21 (notification retry is only from NOTIFYING, never from NOTIFIED or NOTIFIED_UNCONFIRMED).
7. **Truthful receipt outcome** — per §20.3.
8. **Outbound-only Telegram** — unaffected; this contract introduces no inbound mechanism (§28).
9. **No inbound command authority** — same.

### 21.2 What becomes part of the transition record

The record's notification-related content is limited to: `notification_id` (possibly plural across retries), the notification stage's spine-state history (NOTIFYING entries and their outcomes), and a reference to the delivered payload's evidence bindings. The record does **not** duplicate PFN-001's `notification_result` field structure wholesale — it binds to it by reference, consistent with §12.1's "reference-heavy, not copy-heavy" principle (135A §2.2).

---

## 22. Architecture Status contract

### 22.1 Frozen requirements

Architecture Status is a **deterministic projection**, never an authority (§3.2, §4.2 item 3):

1. **Generated from certified projected state** — never from mutable PROJECT_STATUS.md re-scanning once a record exists for the phase in question.
2. **Completed phase absent from In Progress** — enforced structurally per §9.3.
3. **No active phase means explicit empty state** — never an inferred "probably nothing" from absence of data.
4. **Planned successor remains planned** — never promoted to active by the projection itself (§9.4).
5. **No manual maintenance** — Architecture Status must remain fully generated, as it is today (135A §17, confirming this is "generated automatically... never manually maintained").
6. **No independent active-task inference** — never a heuristic over report titles, filenames, or prose.
7. **No post-certification regeneration from mutable latest state** — regeneration must be idempotent against the sealed record.
8. **Exact transition binding where applicable** — a rendered Architecture Status document should be traceable to which record(s) produced each section, at least in principle (exact mechanism deferred to schema/implementation work).

### 22.2 Duplicate-wording observation carried forward

Per the assignment's explicit instruction and 135A's own finding: generated Architecture Status may present both a chapter-level completion and a named milestone with overlapping wording. This contract freezes that **wording duplication alone is not a lifecycle contradiction** unless authority or state semantics diverge (i.e., unless two representations disagree about *which record* or *which state* is authoritative, not merely about how it is phrased).

---

## 23. Repository-final-state contract

### 23.1 Classification (frozen)

Repository cleanliness, pushed state, `origin/main..HEAD`, branch identity, and final revision are **verification-only observations (V role, §3.1)** — final, point-in-time measurements, not perpetual or retroactive claims.

### 23.2 When measured

These facts are measured **at certification time** (CERTIFYING, and optionally re-measured at a defined terminal-verification point after the transition's own finalization commit, if the harness's governed workflow requires a post-commit confirmation step — see §23.4 for the circularity this creates and its resolution).

### 23.3 Binding, change-after-measurement, and placement

1. **How bound**: the measured value at the moment of measurement is written into the record as a historical fact about *that transition*, tagged with the measurement's own timestamp.
2. **What happens if state changes after measurement**: the bound value remains historically true ("this was the state observed at time T for this transition"); it is never treated as still-currently-true without a fresh measurement. A live consumer (e.g., `pcae health`) always re-measures; it never reads the record's historical binding as current truth.
3. **Where they belong**: inside the canonical record as point-in-time bindings for facts measured *before* the transition's own finalization commit (e.g., cleanliness/pushed-state checks that gate whether the transition may proceed at all); facts that can only be known *after* the transition's own commit (see §23.4) belong in a **terminal verification extension** — a follow-up observation appended to the record's history after closure, not a field that must be populated before CERTIFIED.

### 23.4 Resolving the final-revision circularity

**The problem** (named explicitly by the assignment): a finalization commit is often required before the record can know the true "final revision" — but the record is expected to bind `final_revision` as part of its content. This is impossible to resolve by requiring `final_revision` to be known before CERTIFIED, if the finalization commit itself is what the transition is certifying.

**Binding resolution — staged binding semantics**:
1. At CERTIFIED, the record binds `final_revision` as either (a) the actual final revision, if no further commit is required for this transition's own artifacts to be considered final, or (b) an explicit **provisional** marker meaning "final revision is the transition's own eventual finalization commit, not yet made."
2. If (b), the record's history gains one additional, append-only **terminal verification event** once that finalization commit is made and independently confirmed (e.g., via live `git rev-parse`), recording the actual final revision hash and closing the provisional marker.
3. This terminal verification event never mutates the CERTIFIED record's sealed content — it is an additional immutable history entry (§14.1 item 1), consistent with the append-only model.
4. No transition may claim TERMINAL_SUCCESS while `final_revision` remains provisional and unresolved beyond a bounded, defined grace period (exact bound deferred to schema/implementation work) — an unresolved provisional final revision is itself a condition a future implementation must handle explicitly, not leave ambiguous.

---

## 24. Compatibility contract

### 24.1 Compatibility classification (frozen)

Every existing artifact/mechanism this contract touches is classified into exactly one of: **native**, **derived**, **adapter**, **verification-only**, **deprecated**, **retirement candidate**.

| Artifact/mechanism | Classification | Rationale |
|---|---|---|
| Historical Track 134 artifacts (reports, metadata, snapshots, markers, receipts) | Verification-only | Remain immutable, valid, readable; no record exists for them unless a future migration phase (135H per 135A's roadmap) explicitly backfills |
| Current canonical phase reports | Adapter (until a future implementation binds them to a record) | Continue to be produced exactly as PFR-001 requires; become record-derived only once a future phase implements the binding |
| Current completion metadata | Adapter (same reasoning) | Same |
| Current Architecture Status generation | Adapter | Continues to generate from PROJECT_STATUS.md + projected-state seal (134E.10.1V.1 mechanism) until a future phase migrates it to read from records |
| Immutable snapshots (existing mechanism) | Native | The existing sealed-snapshot mechanism is architecturally the direct ancestor of CERTIFIED-state sealing (§7); no adapter needed, only extension |
| Checkpoints (existing `.pcae/finalization-transactions/*.json`) | Adapter | Existing atomic temp-file+`os.replace` pattern (confirmed current) is compatible with §8's durability requirements; becomes the record's own persistence mechanism once implemented |
| Promotion mechanism (`promote_artifact()`) | Adapter | Existing `ArtifactState` machine (confirmed current: `DRAFT`/`VALIDATED`/`CERTIFIED`/`CANONICAL`/`REJECTED`/`QUARANTINED`) remains a real, independently-necessary state machine (135A §4.3); becomes a stage the record tracks |
| `latest.md`/`latest.json` | Adapter (until §13's atomicity requirement is implemented) | Confirmed still non-atomic in current source; remains as-is until a future phase resolves §13.2's mechanism choice |
| `.last-notified.json` marker | Deprecated as authority / Derived as cache | §19 |
| `.pcae/delivery-receipts/` | Native | Already architecturally sound (immutable, atomic); becomes bound to the record via reference (§20) |
| PFN-001 | Native, unamended | §21 |
| PFR-001 | Native, unamended | §12.1 report row |
| `pcae phase complete` | Adapter (entry-point behavior preserved, internal authority source changes only in a future phase) | 135A §15.2 |
| `pcae task finish` | Adapter | Same |
| `pcae phase-report create` | Adapter | Same |
| `pcae notify send-report` | Adapter | Same |

### 24.2 Historical immutability (frozen)

No historical phase report, metadata file, immutable snapshot, marker, or receipt from before any future record implementation may be rewritten, migrated in place, or reinterpreted as if it had been produced under this contract's model. This extends 134B's historical-preservation invariant to the record concept (135A §15.1).

### 24.3 Compatibility does not imply indefinite authority

Historical artifacts remain immutable **and** remain classified as they are today for their own historical instances. But this contract does not grant current behavior (marker-as-terminal-check, mutable-latest-as-authority) a permanent exemption from eventual retirement — §25 freezes the intended future demotion, without executing it in 135B.

---

## 25. Legacy-authority contract

### 25.1 Frozen future-state classification (restating and completing 135A §14)

No retirement is implemented in 135B. This section freezes what the **required future state** must be, for 135C and later phases to act on.

| Current authority/fallback | Required future classification | Executed in 135B? |
|---|---|---|
| Active-task inference (PROJECT_STATUS.md free-text) | Deprecated as authority; becomes a derivative of the record's active-transition lookup | No |
| Report status authority | Retained as derivative | No |
| Metadata authority | Retained as derivative | No |
| Architecture Status authority | Retained as derivative | No |
| Marker terminal authority | Deprecated as authority / retained as derivative cache | No |
| Receipt success authority | Retained as canonical for its own narrow domain (delivery outcome); retained as verification evidence for NOTIFIED/NOTIFIED_UNCONFIRMED classification | No |
| Recent Git attribution (`git log --oneline -N` fallback) | Retired (forbidden from reintroduction anywhere) | No — retirement of the *rule* is frozen; no source change occurs |
| Commit-subject parsing as authority | Retained as verification evidence only (never authority) | No |
| Mutable-latest inspection as authority | Deprecated as authority / retained as the human/tool-facing derivative it should remain | No |
| Entry-point-specific resume logic (4 independent marker checks) | Retirement candidate (long-term); compatibility-only during migration | No |

### 25.2 Binding note

This table is a classification for 135C onward to act on. No implementation, deprecation warning, code change, or behavioral change is introduced by this contract.

---

## 26. Cross-representation invariants

### 26.1 Numbered invariant inventory (frozen)

Each invariant is unambiguous, independently testable by a future verification phase, scoped, assigned a severity, and assigned a failure consequence.

| ID | Invariant | Severity | Failure consequence |
|---|---|---|---|
| CLTR-ID-1 | All representations of a given transition share exactly one `transition_id` | Blocking | Reject the divergent representation; candidate QUARANTINE |
| CLTR-ID-2 | All representations of a phase's most recent transition share exactly one `phase_id` | Blocking | Same |
| CLTR-AUTH-1 | A lifecycle fact has exactly one authoritative source within a transition (§4.1) | Blocking | Design defect — must be resolved before implementation, not tolerated at runtime |
| CLTR-AUTH-2 | No derivative independently reconstructs a fact the record does not carry (§12.3) | Blocking | Derivation bug — fix the derivation, do not accept the inferred value |
| CLTR-STATE-1 | A completed phase never appears in any derivative's "active"/"in progress" classification | Blocking | Regenerate the derivative from the record's projected state |
| CLTR-STATE-2 | A planned successor is never classified active until its own record reaches CERTIFIED or later | Blocking | Same |
| CLTR-STATE-3 | No state transitions backward along the spine (§7.2, §7.3's forbidden-next column) | Blocking | Reject the transition attempt; candidate QUARANTINE if already persisted |
| CLTR-STATE-4 | No state skips a required predecessor | Blocking | Same |
| CLTR-ORDER-1 | No checkpoint before certification (§8.2.1) | Blocking | Reject; the certification stages must complete first |
| CLTR-ORDER-2 | No promotion before checkpoint (§8.2.2) | Blocking | Reject |
| CLTR-ORDER-3 | No terminal notification before promotion (§8.2.3) | Blocking | Reject |
| CLTR-ORDER-4 | No irreversible stage precedes semantic certification (§8.2.7) | Blocking | Reject |
| CLTR-DERIVE-1 | Every derivative is a pure function of the record plus referenced evidence (§12.2) | Blocking | Derivation bug |
| CLTR-DERIVE-2 | Regeneration of any derivative from the same sealed record is byte-identical | Blocking | Derivation bug |
| CLTR-COMMIT-1 | Explicit phase commits declared in the record equal the commits any derivative report claims as phase-owned | Blocking | Reject the divergent derivative claim |
| CLTR-COMMIT-2 | Every declared commit resolves to exactly one of verified/contaminated/unverifiable (§10.4) | Blocking | Fail closed on ambiguous classification |
| CLTR-COMMIT-3 | Fabricated hashes are never silently equivalent to verified (§10.4) | Blocking (as a representability requirement; blocking-vs-warning policy for the *outcome* is deferred, §10.4) | Record the outcome distinctly, regardless of downstream policy |
| CLTR-EVID-1 | Report prose never serves as sole evidence for an R- or E-role fact (§11.2) | Blocking | Reject the report as insufficiently evidenced |
| CLTR-PERSIST-1 | The current pointer never exposes a mixed-generation report/metadata pair (§13.1) | Blocking | Reject the read; surface as an atomic-visibility failure (§18) |
| CLTR-PERSIST-2 | Immutable history is never rewritten (§14.1) | Blocking | Reject the write; candidate QUARANTINE |
| CLTR-PERSIST-3 | The mutable current pointer is always reconstructible from immutable history (§8.1, §13.3 item 6) | Blocking | Reconstruct from history; never treat corrupted pointer as ground truth |
| CLTR-RETRY-1 | NOTIFIED_UNCONFIRMED is recognized as resume-terminal by the record's own logic, not only entry points (§16.2) | Blocking | This is the direct 134F-gap-closure invariant — a future implementation that fails this invariant does not satisfy this contract |
| CLTR-RETRY-2 | A duplicate ordinary completion for an already-terminal phase/task is rejected, never silently accepted (§17.2) | Blocking | Reject; reference the existing terminal record |
| CLTR-RETRY-3 | Recovery from an unknown-outcome crash always observes actual external state before deciding, never infers (§16.4) | Blocking | Block the retry decision until observation completes |
| CLTR-NOTIFY-1 | Notification references promoted canonical evidence, never independently re-gathered "current" evidence (§21.1 item 3) | Blocking | Reject the payload; regenerate from the record |
| CLTR-NOTIFY-2 | Notification retry only from NOTIFYING, never from NOTIFIED/NOTIFIED_UNCONFIRMED (§16.2, §21.1 item 6) | Blocking | Reject the retry; direct to receipt reconciliation (§20) instead |
| CLTR-MARKER-1 | Marker and receipt for a given transition bind the same `transition_id` (§19.2, §20.2) | Blocking | Flag as a detectable inconsistency, not silently accept |
| CLTR-MARKER-2 | Marker presence alone is never sufficient proof of terminal state (§19.1) | Blocking | Consult the record before trusting the marker |
| CLTR-RECEIPT-1 | Receipt reflects actual observed delivery outcome, never an assumed/optimistic one (§20.3) | Blocking | Reject a receipt that claims success without matching record state |
| CLTR-COMPAT-1 | Historical artifacts are never rewritten, migrated in place, or reinterpreted as record-produced (§24.2) | Blocking | Reject the mutation |
| CLTR-COMPAT-2 | PFN-001 and PFR-001 remain unamended by any CLTR-001-conformant work (§1, §21.1, §12.1) | Blocking | Reject the change as out of CLTR-001's scope |
| CLTR-SAFE-1 | Runtime remains Observed / observe / execution unavailable throughout any CLTR-001-conformant work (§28) | Blocking | Reject the change |
| CLTR-SAFE-2 | The record never becomes an execution-authorization mechanism (§2.2 item 1, §28) | Blocking | Reject the design |
| CLTR-SAFE-3 | Terminal states are recognized consistently by both the record's own core logic and every consuming entry point once implemented (§16.1) | Blocking | This is the structural fix for 134F's finding — required of any future implementation |

### 26.2 Severity note

Every invariant listed above is **Blocking** because this contract freezes only requirements that, if violated, would reintroduce exactly the class of structural-drift risk Track 135 exists to eliminate (135A §1.1). No Warning- or Informational-severity invariant is introduced in this contract; §10.4's blocking-vs-warning question for the *unverifiable* commit-ownership outcome specifically is the one place this contract defers a severity decision, and it is explicitly flagged as deferred (§32), not silently resolved as non-blocking.

---

## 27. Versioning contract

### 27.1 Contract versioning (frozen)

1. This contract is **CLTR-001, version 1.0**. Future amendments increment the version per semantic-versioning-like discipline: a breaking change to any Blocking invariant, state, or authority classification requires a new major version and a new governed contract-amendment phase; a clarifying, non-breaking addition may be a minor version increment, still requiring governed review.
2. **Record schema-version relationship**: `schema_version` (§6.2 item 1) and `contract_version` (§6.2 item 2) are distinct fields — a record's schema may evolve (new optional fields) under an unchanged contract version, but any change to a Blocking invariant requires a `contract_version` bump.
3. **Backward compatibility**: a future schema must remain able to represent every record produced under an earlier compatible schema version without loss of any field this contract requires (§6.2).
4. **Forward compatibility**: a consumer built against an earlier schema version must be able to safely ignore fields it does not recognize in a later, compatible schema version, without misinterpreting them as absent-and-thus-defaulted.
5. **Unknown-field handling**: unrecognized fields are preserved (never silently dropped) by any tool that reads and rewrites a record, and are never treated as evidence of anything by a consumer that doesn't understand them.
6. **Required-field evolution**: a field may only become required in a new major contract version; a minor version may add optional fields only.
7. **Migration behavior**: migrating a record (or a derivative) from one schema version to a newer compatible one must be lossless for every field this contract requires; migration is explicitly out of scope for what mechanism performs it (deferred to implementation phases).
8. **Historical verifier behavior**: a verifier built for contract version N must correctly reject (not silently accept) a record claiming a `contract_version` it does not recognize, rather than attempting to interpret it under the wrong rules.
9. **Contract supersession**: this contract is superseded only by a future governed contract-amendment phase producing CLTR-00N (N>1) or CLTR-001 version 2.0+; it is never silently reinterpreted.

---

## 28. Governance contract

### 28.1 Preserved boundaries (frozen, unaffected by this contract)

1. Runtime remains Observed.
2. Maximum capability remains observe.
3. Execution remains unavailable.
4. No backend invocation is introduced.
5. No shell mediation is introduced.
6. No Telegram inbound is introduced.
7. No new communication channel is introduced.
8. PFN-001 remains unchanged (§21.1).
9. PFR-001 remains unchanged (§12.1 report row).
10. Deterministic, explainable, auditable design is directly advanced by this contract (a single canonical record with deterministic derivatives is more inspectable and auditable than the current multi-representation model — 135A §17).
11. Historical immutability is preserved (§14, §24.2).

### 28.2 Binding prohibition

The Canonical Lifecycle Transition Record must not become an execution-authorization mechanism. Nothing in this contract — including the record's CERTIFIED/PROMOTING/PROMOTED states — grants, implies, or is a precondition for any execution capability. The record answers "what is the state of this governed transition," never "is this action authorized to run."

---

## 29. Strategic governance boundary

### 29.1 Re-evaluation (frozen, confirming 135A §16's conclusion after independent re-check)

135B's own initial inspection re-ran `pcae irg-challenge` (§Initial inspection) and found the same five persistent advisory concerns 135A found (SRR-66C-002 age/staleness, SLR-69P-001/SRR-66B-001 lineage-citation semantics, OBJ-004 thin primary coverage, strategic_governance capability growth, 69P missing registered successor) plus the same four contradiction-synthesis pairs (TP-002 through TP-005), unchanged since 135A's own run ("calibration: consistent, no change detected").

### 29.2 Scope classification (frozen)

None of these concerns is a canonical-lifecycle-transition-record concern. They concern the *content and freshness of strategic governance review artifacts* (SRR/SLR documents, objective coverage) — a different authority domain than "which representation is the source of truth for a governed phase's finalization transition." This contract, like 135A, does **not** model strategic review lineage, objective coverage, or strategic-governance phase sequencing.

Classification:
- **Inside CLTR scope**: none of the six IRG concerns.
- **Referenced external governance evidence**: none — CLTR-001 does not reference SRR/SLR artifacts at all.
- **Outside scope**: all six concerns.
- **Future separate contract work**: yes, all six remain candidates for a dedicated future strategic-governance-lineage phase, entirely independent of Track 135.

### 29.3 Narrow point of contact (carried forward from 135A, not adopted)

If a future phase decides strategic governance reviews should themselves be tracked as governed lifecycle transitions (i.e., an SRR or SLR review becomes a "phase" with its own finalization), CLTR-001 would apply to that review's transition the same way it applies to any other phase. This is a hypothetical extension, not adopted into Track 135's scope by this contract.

---

## 30. Conformance model

### 30.1 Conceptual conformance states (frozen)

| State | Determined by |
|---|---|
| **conformant** | Every Blocking invariant in §26.1 holds for a given record and its derivatives; no forbidden pattern from §4.2 is present |
| **conformant_with_legacy_adapter** | The record and its derivatives satisfy §26.1, but one or more consuming entry points still use an §24.1-classified "adapter" mechanism (e.g., still reading a marker as a compatibility signal per §19.1) rather than the record directly — permitted during migration, per §25 |
| **incomplete** | Required fields (§6.2) or required evidence bindings (§11) are missing for a record that has not yet reached CERTIFIED — not itself a violation, since PROPOSED/CERTIFYING records are expected to be incomplete until certification |
| **conflicting** | Two representations of the same `transition_id` disagree on a fact this contract classifies S or D (§3.1) — always a CLTR-AUTH-1 violation |
| **unverifiable** | A verification pass cannot resolve whether a given fact is conformant (e.g., a commit-ownership outcome per §10.4, or a digest that cannot be recomputed due to missing referenced evidence) — distinct from "conflicting"; must be recorded as its own outcome, never silently resolved either way |
| **quarantined** | Per §7.3 — flagged by independent integrity verification, pending human review |
| **superseded** | Per §7.3, §14 — a later correcting transition record exists |

### 30.2 Determination rule

A record's conformance state is itself a **derived** classification (D role), computed by evaluating §26.1's invariants against the record and its bound evidence — never a field the record declares about itself.

---

## 31. Forbidden claims

### 31.1 Frozen list

No implementation or derivative may make the following claims without the stated required evidence:

1. "Phase completed" — requires a CERTIFIED-or-later record reaching at least TERMINAL_SUCCESS or TERMINAL_PARTIAL_EXTERNAL; never claimed from report/metadata status alone (§4.2).
2. "Commits owned" — requires explicit, verified ownership per §10.4's three-outcome classification; never claimed from recency or subject-parsing alone (§9.3 of 135A, §10.3–10.4).
3. "Notification sent" — requires dispatch evidence bound at NOTIFYING/NOTIFIED (§21.2); never claimed from marker presence alone (§19.1).
4. "Repository clean" — requires direct measurement (§23.1); never assumed from a prior transition's bound value.
5. "Pushed" — requires a live remote comparison (§23.1); never assumed stale-but-still-true.
6. "Canonical" — requires certification (CERTIFIED) and promotion (PROMOTED); never claimed for a CERTIFYING-stage or FAILED_PRE_CERT artifact.
7. "Active phase" — requires the phase's *own* transition record to be at PROPOSED-or-later (§9.4); never inferred from report or naming.
8. "Terminal" — requires the record's own spine state to be terminal (§7.3); never inferred only from marker presence (§19.1).
9. "Verified" — requires digest and identity binding to have actually succeeded (§15.1 item 7); never claimed when either binding failed.

---

## 32. Contract verdict criteria

### 32.1 Assessment dimensions

The final contract (this document) is assessed against: completeness, internal consistency, determinism, authority clarity, implementation readiness, compatibility, governance preservation, testability, absence of execution-authority leakage.

### 32.2 Self-assessment (135B's own verdict, subject to independent re-verification in 135C)

- **Completeness**: every section required by the assignment's "Contract structure" (§1–§33 of the assignment, mapped to §1–§30 plus this section and §33 below of this document) is present. §6 explicitly does not freeze a wire schema, per instruction; this is a deliberate completeness boundary, not a gap.
- **Internal consistency**: no clause in this contract contradicts another; where two sections address overlapping ground (e.g., §16 and §17 both touch retry), they are cross-referenced rather than duplicated with independent, potentially-diverging wording.
- **Determinism**: every S/D-role fact (§3) is defined as computable without randomness or unbound I/O once its inputs are bound.
- **Authority clarity**: §3's per-fact table leaves no listed fact without an assigned role.
- **Implementation readiness**: sufficient for later schema design (135D+), prototype planning (135E), and integration/legacy-retirement planning (135H), per the assignment's stated purpose — but explicitly **not** implementation-ready in the sense of a wire schema (deliberately deferred, §6.3).
- **Compatibility**: §24 confirms no clause requires any change to current production behavior.
- **Governance preservation**: §28 confirms all governance boundaries preserved.
- **Testability**: every invariant in §26.1 is phrased as an independently checkable condition.
- **Absence of execution-authority leakage**: §28.2 is an explicit, standalone prohibition.

### 32.3 Unresolved questions, classified

| Question | Classification |
|---|---|
| Which atomic-visibility mechanism (§13.2) to select | Deferred (135D, per 135A §8.3) |
| Whether unverifiable commit ownership should block, warn, or be informational (§10.4) | Deferred (135D, per 135A §10.3) |
| Whether transition ID subsumes or wraps `(report_digest, finalization_snapshot_id)` (§5.1) | Deferred (135D, per 135A §9.4) |
| Exact byte-level canonical serialization for the digest (§15.2) | Deferred (schema-design phase) |
| Exact event schema for the hybrid current-state/event-log model (135A Architecture Decision #2) | Deferred (135D/schema-design phase) |
| Exact bound for how long a provisional `final_revision` may remain unresolved before it is itself a failure condition (§23.4 item 4) | Deferred (schema/implementation phase) |
| Whether/how to backfill historical records for pre-Track-135 transitions | Deferred (135H, per 135A §15.2) |
| Exact migration sequencing for legacy-authority retirement (§25) | Deferred (135H, per 135A Architecture Decision #7) |
| None of the above are Blocking for 135B's own completion — no unresolved question prevents this contract from being internally consistent and complete as a contract-freeze deliverable. | Non-blocking (for 135B); Blocking (for the specific future phase each is deferred to, before that phase may close) |

### 32.4 Verdict

This contract is **not internally contradictory** and is judged ready for 135C's independent verification pass. No question above blocks 135B's own completion.

---

## 33. Track 135 roadmap

### 33.1 Confirmation of 135A's re-derived sequence

135A §18.2's re-derived sequence (135A → 135B → 135C → 135D → 135E → 135F → 135G → 135H → 135I+) is **confirmed, not revised**, by this contract-freeze phase. Nothing encountered while writing this contract contradicts that sequence's shape or ordering.

### 33.2 Smallest disciplined next phase

**135C — Canonical Lifecycle Transition Record Contract Verification.** A 134C-style independent verification that this contract (CLTR-001 v1.0) is internally consistent, does not contradict 134B/PFN-001/PFR-001, and honestly represents what is contract-only versus what remains a future obligation (per §32.3's deferred-question list). This is the smallest next step: it re-derives and challenges this document the way 134C challenged 134B and 134F challenged the whole of Track 134, before any schema, invariant-finalization, or prototype work begins.

135B is **not** followed directly by 135D (invariant/state-machine verification) because, per 135A §18.1's own reasoning (confirmed here), verifying the state machine presupposes the contract describing it is itself sound — that soundness check is 135C's job, not skippable.

135B is not the start of 135C. This document stops here.

---

## Files changed

- Added: `docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT.md` (this document)
- Updated per governed phase completion: `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, active task contract, canonical report and metadata (see final governed phase report for exact diffs)

No production source, test, schema, or configuration file was created or modified by this phase.

## Governance results

- `pcae_health`: healthy (idle), Git status clean
- `pcae_check`: passed (no active task at session start; task contract created for this phase's own governed work)
- `pcae_doctor_task_memory`: clean, no inconsistencies
- `pcae_push_check`: clean, nothing to push at session start
- `pcae_runtime_inspect`: Observed / observe / execution unavailable (unchanged)
- `telegram_runtime`: configured; production Telegram used only for the final governed terminal report per this phase's own finalization

## Runtime state

- Runtime state: Observed (unchanged)
- Maximum capability: observe (unchanged)
- Execution availability: unavailable (unchanged)

## PFN-001 / PFR-001 confirmation

- PFN-001: unchanged. This document does not modify notification delivery guarantees, sinks, or the "exactly one trusted canonical phase report delivered" requirement (§21.1).
- PFR-001: unchanged. This document does not modify canonical phase report content structure requirements (§12.1 report row).

## No-go confirmations

- No implementation occurred. No transition record was built. No JSON schema was frozen. No source code was added or modified. No test was added or modified. No finalization behavior changed. No entry-point behavior changed. No atomic-latest-write repair occurred. No resume-logic repair occurred. No fabricated-hash repair occurred. No historical report was rewritten. No immutable snapshot was modified. No PFN-001 change occurred. No PFR-001 change occurred. No Repository Intelligence authority expansion occurred. No Advisory authority change occurred. No Decision Evaluation change occurred. No execution capability was introduced. No shell mediation was added. No Telegram inbound control or new communication channel was added. No structural gap disclosed by 134F or 135A was repaired. 135C was not begun. No raw `git commit` was used. No raw `git push` was used. No `--no-verify` was used. No force push was used.

## Recommended next phase

135C — Canonical Lifecycle Transition Record Contract Verification
