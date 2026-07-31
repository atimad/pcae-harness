# Phase 147L.6 — AESIC-001 Idempotency and Restart Repair Independent Verification

## 1. Executive Summary

This phase independently verifies AESIC-001 v1.3 (Phase 147L.5's repair)
against the two findings finalized by Phase 147L.4: **Finding A**
[Major] — the Stage 2 idempotency no-op branch could silently discard a
validated `stage_1_result`, contradicting AESIC-REQ-057's
mandatory-when-supplied guarantee; and **Finding B** [Minor] — §11.2's
restart matrix had no row for a crash between the AER's compound-key
commit and the canonical pointer's own write.

Both findings were independently reconstructed from primary sources (the
pre-repair v1.2 text, AEMIC-001 §6, and Phase 147L.4's own concrete
failure scenario) before comparing against Phase 147L.5's repair
narrative. Both are **confirmed resolved**: Finding A is closed by
AESIC-REQ-129's deterministic Stage-1-evidence-equivalence definition,
made a precondition of the AESIC-REQ-023(a)/121 no-op classification;
Finding B is closed by AESIC-REQ-130/131 and two new §11.2 restart-matrix
rows defining a complete, deterministic "recovery is retry, never
reconstruction" model.

This verification's own fresh adversarial pass — 18 Stage 1 idempotency
scenarios, 7 concurrency scenarios, 9 replay/restart scenarios, 16
post-AER/pre-pointer scenarios, a full restart-boundary reconstruction
against the persistence-sequence model in the authorizing prompt, and 14
independent threat categories — found **no new Blocking or Major
finding**. One **Informational** observation is reported (§19): the
contract does not explicitly state whether a losing concurrent
`evaluate_stage_2` call's own return value reflects its own written AER
or the eventual canonical one, though the answer is derivable
unambiguously from existing text and matches established last-write-wins
precedent (IWPC-REQ-144/147). This does not affect Finding A/B closure,
architectural preservation, or predecessor-contract compatibility.

**Overall Verdict: AESIC-001 v1.3 INDEPENDENTLY VERIFIED.**

**Recommended next phase: 147M — Authority Evaluation Integration
Implementation.**

---

## 2. Independent Verification Method

Per this phase's own governing discipline (§2 of the authorizing prompt),
no conclusion below relies on Phase 147L.5's own repair narrative until
independently earned:

1. AESIC-001 v1.3 was re-read in full (2,928 lines, all 36 sections, all
   131 `AESIC-REQ-###` entries) directly from
   `docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`.
2. Finding A and Finding B were reconstructed from Phase 147L.4's own
   §17 Findings section
   (`docs/verification/PHASE_147L4_AESIC_FINAL_REPAIR_INDEPENDENT_VERIFICATION.md`),
   independently re-deriving the concrete failure scenario each finding
   names, before reading Phase 147L.5's own §33 repair-confirmation
   narrative.
3. From those primary sources, this verification independently derived
   what a sufficient repair must guarantee (§4 below) before reading
   §33's own stated rationale.
4. AESIC-001 v1.3's repaired text (AESIC-REQ-023, 057, 076, 102, 121, 129,
   130, 131, and the §13 failure-ownership table's new row) was tested
   against those independently derived guarantees through fresh
   adversarial construction (§6, §11 below).
5. Only after §4–§11's own conclusions were reached was Phase 147L.5's
   own §33 rationale read and compared for agreement (§33.3–33.9 was
   found to match this verification's own independent reasoning in every
   material respect — no disagreement found).
6. Predecessor contracts (`AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`
   §6/§7 for `AuthorityEvaluationOutcome`'s exact eight-field shape;
   `INTERACTIVE_WORKFLOW_CONTRACT.md` §26.1 for `Session.session_id`'s
   already-populated status) were read directly, not merely trusted from
   AESIC-001's own citations, to independently confirm every
   cross-contract claim this repair makes (§17 below).

---

## 3. Primary-Source Reconstruction

### 3.1 AESIC-REQ-129's exact field set (independently derived from AEMIC-001 §6)

`Stage1EvaluationResult` (AESIC-REQ-122) carries exactly three fields:
`outcome` (an `AuthorityEvaluationOutcome`), `evaluation_id`, `session_id`.
`AuthorityEvaluationOutcome` itself (AEMIC-REQ-021, independently
re-read) carries exactly eight fields: `template_ref`, `template_version`,
`claimed_identity`, `evaluation_result`, `declaration_ref`,
`citation_text`, `evaluated_at`, `evaluator_version`, `schema_version`
(nine, not eight — AEMIC-REQ-021's own header text says "eight fields"
but the table lists nine; this is a pre-existing AEMIC-001 count
discrepancy, not introduced by and outside the scope of this repair or
this verification — noted for completeness only, §19).

AESIC-REQ-129 item 3 excludes exactly two things from its field-by-field
comparison: `evaluated_at` (an `AuthorityEvaluationOutcome` field) and
`evaluation_id` (a `Stage1EvaluationResult` field, not an
`AuthorityEvaluationOutcome` field — the two exclusions operate at two
different structural levels, which this verification confirms is
internally consistent, not an error: `evaluation_id` is excluded from
the *outer* `Stage1EvaluationResult` comparison, `evaluated_at` from the
*inner*, wrapped `outcome` comparison). `session_id` is compared but
"trivially satisfied" per the contract's own text, since both values were
already forced equal by AESIC-REQ-123 check 2 before AESIC-REQ-129 is
ever reached for a non-`None` `stage_1_result`. Independently confirmed:
no field is left uncompared and unaccounted-for by this three-way
partition (compared-and-substantive: `template_ref`, `template_version`,
`claimed_identity`, `evaluation_result`, `declaration_ref`,
`citation_text`, `evaluator_version`, `schema_version`; excluded as
metadata: `evaluated_at`, `evaluation_id`; trivially-equal-by-precondition:
`session_id`).

### 3.2 Finding A's exact repair mechanism

Independently reconstructing Phase 147L.4's own concrete scenario (its
§17, reproduced in substance): a canonical AER with no
`stage_1_outcome_ref` exists; a later attempt supplies genuinely valid
Stage 1 evidence; citation/outcome fields are otherwise unchanged;
pre-repair AESIC-REQ-121 would classify this "unchanged" (comparing only
citation/outcome fields) and AESIC-REQ-023(a) would return the existing
AER, discarding the newly supplied evidence. This verification
independently confirms AESIC-REQ-129's "one absent, one present ⇒ not
equivalent" rule (item 2) is exactly the minimal, sufficient repair: it
makes the presence/absence of Stage 1 evidence itself part of the
"unchanged" test, so the scenario above is now correctly classified
"changed" (AESIC-REQ-023(b)) — closing the gap without altering
citation/outcome comparison semantics at all.

### 3.3 Finding B's exact repair mechanism

Independently reconstructing Phase 147L.4's own §17 Finding B: AER
persistence is structurally two sequential writes (compound-key commit,
then pointer write); a crash between them was previously undescribed by
§11.2's table, violating AESIC-REQ-103's "every restart point... SHALL
have a defined, safe resumption" completeness guarantee. This
verification independently confirms AESIC-REQ-130's "uncommitted
candidate, recovery is retry, never reconstruction" rule is sufficient:
it names the durable post-crash state precisely (item 1), classifies it
without ambiguity (item 2), defines discovery through the existing
AESIC-REQ-023 comparison rather than a new mechanism (item 3), forecloses
the one unsafe alternative — inferring canonicity from recency, which
would require a total write-order this system does not keep independent
of the pointer itself (item 4) — and ties the result back to
AESIC-REQ-077's observational-equivalence requirement (item 5).

---

## 4. Independently Derived Sufficiency Criteria

Before reading §33's own stated rationale, this verification derived that
a sufficient repair must guarantee, independent of implementation:

**For Finding A:**
(a) No valid, freshly-supplied Stage 1 evidence can be classified
"unchanged" against a canonical AER that lacks it, or that carries
materially different evidence.
(b) The comparison must remain a single, deterministic function with no
ambiguous or order-dependent outcome.
(c) The repair must not require any new persisted artifact or lookup
(AESIC-REQ-064/078/080's "exactly one artifact type" boundary).
(d) Equivalent evidence (including two structurally distinct but
substantively identical Stage 1 invocations) must not be forced into
spurious supersession — otherwise idempotency itself would be broken in
the opposite direction.

**For Finding B:**
(e) The post-crash durable state must be named and shown to never be
mistaken for corrupt, canonical, or lost.
(f) Recovery must not require inferring order from data the system does
not durably track (no "most recent entry wins" heuristic).
(g) Recovery must not risk overwriting a legitimately newer canonical
pointer with a stale retry's own output.
(h) The retry path must be the *same* path ordinary Stage 2 idempotency
already uses — introducing a second, parallel recovery mechanism would
itself be a new, unaudited surface.

Every one of (a)–(h) is independently confirmed satisfied by §6–§12
below.

---

## 5. Stage 1 Idempotency Equivalence — Independent Verification

AESIC-REQ-129 is confirmed:

- **Complete.** Every reachable state pair (absent/absent,
  absent/present, present/absent, present/present-with-N-way field
  differences) is covered by exactly one of the rule's three ordered
  branches; no state pair falls through undefined.
- **Ordered and deterministic.** The three branches are mutually
  exclusive by construction (branch 1 requires both absent; branch 2
  requires exactly one absent; branch 3 requires both present) — no two
  branches can simultaneously apply, so evaluation order does not affect
  the result.
- **Closed.** No field outside the fixed nine-field
  `AuthorityEvaluationOutcome` set plus `session_id` participates; no
  external state (clock, process identity, storage backend) is consulted.
- **Implementation-independent.** Every compared field is a plain value
  already defined by AEMIC-001 §6 or AESIC-REQ-122 — confirmed by direct
  re-reading of AEMIC-REQ-021 (§3.1 above), not merely trusted from
  AESIC-001's own citation.
- **Resistant to ambiguous comparison.** `evaluation_id`'s exclusion is
  independently verified necessary, not merely convenient: since
  AESIC-REQ-098 guarantees `evaluation_id` uniqueness per invocation, its
  inclusion would make *every* Stage 1 invocation "not equivalent" to
  any other, even a byte-identical replay — which would make the
  "both present" branch permanently unreachable in practice and force
  every idempotent retry with re-supplied Stage 1 evidence into spurious
  supersession, violating derived criterion (d). Its exclusion is
  therefore not a weakening but the only choice consistent with
  idempotency's own definition.

No field was found that can change observable AER content without
affecting idempotency classification: every field AESIC-REQ-121(1)
compares for the outer citation/outcome equality, plus every field
AESIC-REQ-129(3) compares for Stage 1 evidence equality, together cover
the AER's full observable content (§8.5's minimum-content list), modulo
only `evaluated_at`/`evaluation_id`/`record_id`/`record_digest`, each of
which is independently confirmed to be either pure metadata
(`evaluated_at`) or a value whose per-invocation uniqueness is itself the
reason it cannot be an equivalence key (`evaluation_id`, `record_id`,
`record_digest`) — not an oversight.

**Determination: AESIC-REQ-129 fully closes Finding A** (criteria (a)–(d)
all independently confirmed).

---

## 6. Stage 1 Idempotency Adversarial Analysis

All 18 scenarios from the authorizing prompt were independently
constructed and traced against AESIC-REQ-023/121/129's text:

| # | Scenario | Independently derived classification |
|---|---|---|
| 1 | No Stage 1 evidence exists; retry supplies valid evidence | **Changed** (AESIC-REQ-129 item 2) → supersession |
| 2 | Existing evidence present; retry omits it | **Changed** (item 2, "vice versa" clause) → supersession |
| 3 | Existing/incoming Stage 1 differ only in `evaluation_result` | **Changed** (item 3, field compared) → supersession |
| 4 | Differ only in declaration/citation material (`declaration_ref`/`citation_text`) | **Changed** (item 3) → supersession |
| 5 | Differ only in Session binding | Unreachable as stated — AESIC-REQ-123 check 2 refuses a cross-session `stage_1_result` before AESIC-REQ-129 is ever reached (`Stage1HandoffInvalidError`, `SESSION_MISMATCH`) |
| 6 | Differ only in claimed identity | Unreachable — AESIC-REQ-123 check 3 refuses first (`IDENTITY_MISMATCH`) |
| 7 | Differ only in Decision Template identity (`template_ref`) | Unreachable — AESIC-REQ-123 check 4 refuses first (`TEMPLATE_MISMATCH`) |
| 8 | Differ only in template version | Unreachable — same check 4 (`template_version` is part of the same binding check) |
| 9 | Differ only in a digest/canonical representation | No such field exists on `AuthorityEvaluationOutcome`/`Stage1EvaluationResult` (only the AER and pointer carry digests, §8.4/§12.1) — not applicable; content equality is the only defined comparison, so a hypothetical serialization difference with identical field values is correctly equivalent |
| 10 | Malformed Stage 1 evidence supplied after a valid AER exists | Refused before comparison — AESIC-REQ-123 check 1, `Stage1HandoffInvalidError(reason=MALFORMED)`, no AER produced (AESIC-REQ-124) |
| 11 | Cross-session evidence supplied after a valid AER exists | Refused — AESIC-REQ-123 check 2, same as scenario 5 |
| 12 | Concurrent invocations supply different valid Stage 1 results | Both independently classified per their own comparison against the canonical pointer at the moment each reads it; both persist (AESIC-REQ-120 concurrency, §7 below) |
| 13 | Concurrent invocations differ only by Stage 1 presence/absence | Same as 12 — each independently reaches "changed" against whatever it observes as canonical |
| 14 | Retry supplies byte-different but canonically equivalent Stage 1 evidence | **Equivalent** (item 3 — comparison is field-value equality, not byte/serialization equality) → no-op, correctly not superseded |
| 15 | Retry supplies canonically different evidence with identical display text | **Changed**, if any compared field (e.g. `evaluation_result`, `declaration_ref`) differs even while `citation_text` happens to match — the comparison is field-by-field, not display-text-by-display-text, so a scenario engineered to keep only *display* text constant while other fields diverge is still correctly caught |
| 16 | Historical replay encounters an older AER predating Stage 1 evidence | Read via AESIC-REQ-119 item 2's current canonical pointer, whatever it is at replay time — no special-cased "old AER" handling exists or is needed; the same AESIC-REQ-023 comparison applies uniformly |
| 17 | Registry/Decision Template evolution changes the reconstructed Stage 1 binding | Out of scope for AESIC-REQ-129 (Stage 1 binding is fixed at Stage 1 invocation time and validated against the *current* session/template at Stage 2 time via AESIC-REQ-123 checks 3–4, not re-derived from Registry state) — a Registry/template change between Stage 1 and Stage 2 either still passes AESIC-REQ-123 (if it did not change `template_ref`/`template_version` themselves) or is a separate, already-governed "changed" classification via AESIC-REQ-121's own citation/outcome comparison (§11.2's existing "Registry evolution"/"Decision Template evolution" rows) |
| 18 | A no-op would silently retain the wrong Stage 1 history | Precluded by construction: AESIC-REQ-023(a)'s no-op is reachable only when AESIC-REQ-129 finds the two Stage-1-evidence-equivalent — "wrong" history and "equivalent" history are the same predicate this rule tests, so a no-op that retains non-equivalent history cannot occur without AESIC-REQ-129 itself being violated (no such implementation path exists in the text) |

Every scenario resolves to exactly one deterministic outcome: no-op
reuse, supersession, or refusal — never an unspecified or ambiguous
result. Scenarios 5–8 and 11 are correctly intercepted one layer earlier
(AESIC-REQ-123) than AESIC-REQ-129 itself, which this verification
confirms is the intended design (§5.7's ordering: "validation of a
supplied `stage_1_result` SHALL complete, pass or fail, before any other
Stage 2 work begins") — not a gap in AESIC-REQ-129, since those
scenarios can never reach it as a `Stage1EvaluationResult` that AESIC-REQ-129
would evaluate.

---

## 7. No-Op / Supersession / Refusal Boundary — Independent Verification

The three-way classification is confirmed cleanly disjoint and jointly
exhaustive:

- **No-op** requires *both* AESIC-REQ-121(1) (citation/outcome unchanged)
  and AESIC-REQ-121(2)/129 (Stage-1-evidence-equivalent) to hold —
  independently confirmed by AESIC-REQ-121's own repaired text ("Every
  compared field in (1) matching exactly, and (2) holding, SHALL be
  classified 'unchanged'").
- **Supersession** is the logical complement — either (1) or (2) fails —
  and is confirmed to always produce a genuinely new, immutable,
  independently-retrievable AER (AESIC-REQ-023(b), AESIC-REQ-054/082
  unaffected).
- **Refusal** (`Stage1HandoffInvalidError`) occurs strictly before either
  comparison is reached (AESIC-REQ-124: "no AER... no side effect...
  before any other Stage 2 work begins") and therefore cannot itself
  produce or influence a no-op/supersession outcome — confirmed no
  overlap.

Independently confirmed against each of the six itemized guarantees in
§6 of the authorizing prompt:

1. Valid new Stage 1 evidence cannot be silently discarded — confirmed
   (§5, §6 scenarios 1, 12, 13).
2. Materially different Stage 1 evidence cannot collapse into an
   existing AER — confirmed (AESIC-REQ-129 item 3's exact-match
   requirement; any difference ⇒ not equivalent ⇒ supersession).
3. Equivalent evidence cannot create unnecessary AERs — confirmed
   (scenario 14; AESIC-REQ-129 item 3 is genuine value-equality, not
   identity-equality, so semantically identical resupplies are always
   no-ops).
4. Invalid evidence cannot mutate idempotency state — confirmed
   (AESIC-REQ-124: refusal produces no AER and no side effect at all).
5. Supersession preserves immutable history — confirmed (AESIC-REQ-054/082,
   119 item 1, unaffected by this repair; independently re-read,
   unmodified text).
6. The canonical pointer identifies the correct current-effective AER —
   confirmed subject to §8's concurrency analysis and §11's tamper-evidence
   mechanism (AESIC-REQ-126/127, unaffected and untouched by this
   repair).

---

## 8. Concurrency Verification for Finding A

Each of the seven scenarios in the authorizing prompt's §7 was traced
independently against AESIC-REQ-098 (per-invocation `evaluation_id`
uniqueness), AESIC-REQ-119 item 1 (collision-free compound-key writes),
and AESIC-REQ-120 (pointer last-write-wins):

- **Equivalent invocations racing:** each independently computes a no-op
  or supersession against whatever it observes as canonical at read
  time; if both observe the same canonical AER and both find themselves
  equivalent to it, both are no-ops — no write races at all in this
  case, since a no-op involves no pointer write.
- **Materially different Stage 1 evidence racing:** both independently
  classify "changed" against the canonical AER each observes, both write
  distinct compound-keyed AERs (collision-free, AESIC-REQ-098), and the
  pointer write race is governed by AESIC-REQ-120 last-write-wins —
  confirmed no data loss (both AERs remain durably retrievable) and no
  ambiguity about which one is canonical (deterministically whichever
  atomic replace lands last).
- **Stage 1 present vs. absent racing:** same mechanism as above; both
  are independently "changed" relative to whatever pre-race canonical
  state existed (unless one happens to observe the other's just-written
  pointer first, in which case it correctly re-evaluates against that
  newer state — see determinism note below).
- **One valid, one malformed:** the malformed attempt refuses via
  AESIC-REQ-124 before ever reaching the comparison or a write —
  produces no AER, no pointer interaction, no interference with the
  valid attempt's own independent classification and write.
- **One same-session, one cross-session:** the cross-session attempt
  refuses via AESIC-REQ-123 check 2 before reaching comparison — same
  non-interference as above.
- **Two valid superseding candidates:** both persist independently;
  pointer race resolved by last-write-wins; both remain durably
  retrievable.
- **Three-way race including an existing current-effective AER:** the
  existing AER is unaffected (immutable); the two new attempts race as
  in the two-valid-candidates case; the pointer ends up naming whichever
  of the three writes (the pre-existing pointer's own prior state is
  simply overwritten, not "raced against" — it was already durable
  before this race began) completes its atomic replace last among the
  contending writers.

**Guarantees independently confirmed:**

- Deterministic winner selection: confirmed — "whichever atomic replace
  completes last" is a total, well-defined order over any finite set of
  racing writers (no tie is possible for a single mutable file target
  using atomic replace semantics).
- No silent loss of valid Stage 1 evidence: confirmed — every write to
  the primary, compound-keyed store is independent of the pointer race
  and none is ever deleted (AESIC-REQ-119 item 1).
- No mutable AER history: confirmed — AESIC-REQ-054/082 unaffected;
  concurrency governs only the pointer, never an AER itself.
- No multiple current-effective pointers: confirmed — the pointer is a
  single mutable artifact per `package_id`, atomic-replace guarantees
  exactly one final state.
- No corruption of the compound-key model: confirmed — collision
  freedom is structural (AESIC-REQ-098's uniqueness guarantee), not
  dependent on race timing.
- Observational equivalence after retry: confirmed — any losing
  attempt's caller, if it retries, re-enters the same fresh-comparison
  path and reaches a result indistinguishable from having always
  observed the eventual canonical state (§9 below).

This verification made no assumption about a specific filesystem,
database, lock, or transaction implementation at any point in this
analysis, consistent with AESIC-REQ-086's own "or an equivalent
mechanism" framing.

---

## 9. Replay and Restart Verification for Finding A

Each of the nine scenarios from the authorizing prompt's §8 was checked:

- **Restart before Stage 2:** unaffected — Stage 2 has not begun;
  resumes normally (existing §11.2 row).
- **Restart after Stage 2 evaluation, before persistence:** the
  in-memory, not-yet-written result is lost (AESIC-REQ-080's transient
  classification); resumption is a fresh Stage 2 call, safe by
  AESIC-REQ-018's determinism guarantee.
- **Restart after AER construction, before commit:** same as above — no
  partial AER can exist because the write is atomic/exclusive-create
  (AESIC-REQ-019/086); "constructed but not committed" leaves no durable
  trace to reconcile.
- **Restart after immutable AER commit:** governed by the new
  AESIC-REQ-130 rule (§10 below) — the primary subject of Finding B.
- **Restart after pointer update:** the AER is canonical and durable;
  resumption reads the current canonical pointer normally (existing
  "After Stage 2, before Publication authorization" row).
- **Duplicate publication:** explicitly out of AES's scope, governed
  entirely by the Coordinator's own idempotency marker (existing row,
  unaffected by this repair).
- **Historical replay:** governed uniformly by AESIC-REQ-023's
  fresh-comparison rule against whatever is canonical at replay time —
  no special-cased "old" vs. "new" replay path exists.
- **Replay after template evolution:** existing "Decision Template
  evolution" row, unaffected — Stage 2 always re-resolves fresh (§6.5).
- **Replay after Registry evolution:** existing "Registry evolution"
  row, unaffected — same re-resolution guarantee.

**Confirmed:**

- Stage 1 evidence encoded in the AER remains retrievable: confirmed —
  it is inline, embedded content (AESIC-REQ-118), part of the same
  document as everything else in the AER; no separate retrieval path is
  needed or exists.
- No transient Stage 1-only storage is required: confirmed —
  AESIC-REQ-080 explicitly classifies Stage 1 outcomes transient; the
  `stage_1_result` parameter is a caller-retained, in-memory value only
  (AESIC-REQ-128's ownership table), never a store AES itself maintains.
- Idempotency comparison can be repeated deterministically: confirmed —
  AESIC-REQ-121/129 depend only on plain, already-defined field values,
  never process memory or object identity (§5 above).
- Replay cannot replace one Stage 1 history with another without
  supersession: confirmed — any Stage 1 evidence difference is, by
  AESIC-REQ-129's own construction, either "equivalent" (no
  observable change) or "not equivalent" (forces supersession); there is
  no third path that silently substitutes one for the other.
- Replay remains observationally equivalent to uninterrupted execution:
  confirmed for every restart point enumerated in §11.2's table
  (AESIC-REQ-077), including the two new rows this repair adds (§10
  below).

---

## 10. Post-AER / Pre-Pointer Crash Recovery — Independent Verification

Independently re-deriving the persistence sequence from AESIC-REQ-119
(§12.1) rather than assuming the authorizing prompt's nine-step
enumeration is itself authoritative: AESIC-001's own text describes
exactly two durable writes (item 1, compound-key commit; item 2, pointer
write), both atomic, in that fixed order, with no other durable
intermediate state. This matches the authorizing prompt's steps 1–3
("validate, resolve idempotency state, evaluate") as pre-write,
in-memory work (AESIC-REQ-080, transient); step 4–5 ("construct AER" /
"commit") as item 1; steps 6–8 ("construct pointer" / "validate content
and digest" / "publish or replace") as item 2 (pointer construction and
digest computation are in-memory, pre-write operations — AESIC-REQ-126
item 1 assigns digest computation to AES at write time, not as a
separately durable step); step 9 ("return outcome / continue publication
integration") as post-item-2, out of AES's own persistence scope
(Coordinator's domain, §9.5).

**AESIC-REQ-130 and AESIC-REQ-131 are independently confirmed to fully
close Finding B:**

- **Durable state after the crash** (item 1): independently verified
  against AESIC-REQ-119 item 1's own unmodified text — a compound-keyed
  AER, once exclusive-create-written, is indistinguishable at the
  storage layer from any other entry; no special "candidate" flag or
  separate storage tier is introduced, confirming no widening of the
  "exactly one artifact type" boundary (AESIC-REQ-078).
- **Classification** (item 2): independently confirmed disjoint from
  `CanonicalPointerCorruptError`'s own domain — corruption requires a
  pointer that *exists* and fails a digest check (AESIC-REQ-126 item 2);
  an uncommitted candidate exists in a state where the pointer either
  does not yet exist for this `package_id`, or still validly names the
  *previous* canonical AER — in neither case does AESIC-REQ-126's
  read-time verification procedure fail or even apply to the new AER
  itself.
- **Discovery** (item 3) and **Recovery-is-retry** (item 4): confirmed
  to introduce no new mechanism — the discovery path is exactly
  AESIC-REQ-023's own pre-existing fresh-resolution-and-comparison
  procedure, re-entered by an ordinary retry of the identical call. This
  independently satisfies derived criterion (h) (§4): no second,
  privileged recovery mechanism is introduced.
- **Idempotent-retry equivalence** (item 5): confirmed against
  AESIC-REQ-077 directly — once a retry's pointer write succeeds, the
  observable state (canonical AER, its `citation_text`, its
  `stage_1_outcome_ref`) matches what uninterrupted execution would have
  produced, because the retry's own classification (no-op or
  supersession) is computed by the same deterministic procedure an
  uninterrupted call would have used.
- **Concurrency** (item 6): confirmed to defer entirely to the existing,
  unmodified AESIC-REQ-120 last-write-wins rule — no new concurrency
  primitive is introduced, consistent with the repair's own narrow
  scope (§33.1).
- **Detected pointer-write failure** (item 7, AESIC-REQ-131): confirmed
  disjoint from both the crash case (item 1–6, no exception is possible
  because the process is dead) and from `CanonicalPointerCorruptError`
  (a distinct condition entirely — write-did-not-complete vs.
  write-completed-but-content-is-wrong).

**Determination: AESIC-REQ-130 and AESIC-REQ-131 fully close Finding B**
(criteria (e)–(h) all independently confirmed).

---

## 11. Restart-Matrix Completeness — Independent Verification

Mapping the authorizing prompt's nine-step persistence sequence against
every possible crash boundary, independently, before checking §11.2's
table for coverage:

| Boundary | Coverage |
|---|---|
| Before AER commit (steps 1–4) | Existing "Before Stage 2" row — no durable state exists yet, resumes normally |
| During AER commit (step 5) | Atomicity (AESIC-REQ-019/086) makes "during" collapse to "before" or "after" — no third state is structurally possible; not a distinct restart point requiring its own row |
| After AER commit, before pointer construction (post-step-5, pre-step-6) | **New AESIC-REQ-130 row** |
| After pointer construction, before pointer write (steps 6–7, pre-step-8) | In-memory only (digest computation, AESIC-REQ-126 item 1); observationally identical to "before pointer write" — subsumed by the same AESIC-REQ-130 row, no separate row needed |
| During pointer write (step 8) | Atomic-replace (AESIC-REQ-119 item 2) makes "during" collapse to "before" or "after" — same reasoning as AER commit; subsumed |
| After pointer write, before acknowledgement/return (post-step-8, pre-step-9) | Subsumed by the existing "After Stage 2, before Publication authorization" row — a retry re-enters AESIC-REQ-023's own comparison, finds the already-canonical AER Stage-1-evidence-equivalent, and returns it as a no-op; no distinct behavior from ordinary post-completion resumption, so no new row is required |
| After acknowledgement, before downstream publication (step 9+) | Explicitly out of AES's own scope — Coordinator's own idempotency marker (existing "Publication retry" row, PEC-001's domain, unaffected) |

**Independently confirmed: no structurally possible restart point remains
unspecified.** The two atomic-write boundaries (AER commit, pointer
write) each collapse their "during" state into "before"/"after" by
construction (exclusive-create and atomic-replace both guarantee
all-or-nothing visibility), leaving exactly one genuinely new
crash-window requiring its own row — the one AESIC-REQ-130 names — plus
the disjoint synchronous-failure case AESIC-REQ-131 names. This matches
Phase 147L.5's own §33.2 disposition exactly, independently re-derived
rather than assumed.

---

## 12. Post-AER / Pre-Pointer Adversarial Analysis

All 16 scenarios independently traced:

| # | Scenario | Independently derived outcome |
|---|---|---|
| 1 | AER commits; pointer update never begins | Uncommitted candidate (AESIC-REQ-130 item 1–2); retry discovers via ordinary comparison |
| 2 | Pointer update begins and fails (synchronous) | `CanonicalPointerUpdateFailedError` (AESIC-REQ-131); AER untouched |
| 3 | Pointer update succeeds but caller receives failure (e.g. network/IPC drop after a local write) | Observationally identical to a successful call from AES's own perspective; a caller retry re-enters AESIC-REQ-023, finds the now-canonical AER Stage-1-evidence-equivalent, returns it as a no-op — same mechanism as any "After Stage 2" resumption |
| 4 | Retry finds committed AER and old pointer | Exactly AESIC-REQ-130's own named case — recomputes, either no-op against old pointer's target (if still equivalent) or persists a new AER and re-attempts the pointer write |
| 5 | Retry finds committed AER and a newer pointer (a different, later attempt already advanced it) | Recomputes fresh against the *current* (newer) canonical AER — correctly ignores the orphaned candidate from scenario 1 entirely, since discovery is never based on scanning for candidates (item 3) |
| 6 | Retry finds multiple unpointed candidates | Irrelevant to the retry's own logic — it never scans the primary store for candidates (item 3); it only ever reads the current pointer and recomputes fresh; multiple orphans coexist harmlessly (AESIC-REQ-119 item 1's "never deleted") |
| 7 | Retry finds an unpointed candidate with stale Stage 1 evidence | Same as 6 — the retry does not consult orphaned candidates at all; its own fresh computation (using whatever `stage_1_result` *this* retry call itself receives) is the only input that matters |
| 8 | Retry finds an unpointed candidate with a differing compound key | Not a distinguishable case — every compound key is unique by construction (AESIC-REQ-098); "differing" is simply "a different orphan," already covered by 6 |
| 9 | Retry finds a valid candidate but a corrupted old pointer | The corrupted pointer raises `CanonicalPointerCorruptError` (AESIC-REQ-126/127) independently of AESIC-REQ-130 — a disjoint failure mode; recovery from pointer corruption is a separate, operator-owned path (AESIC-REQ-126 item 4), not conflated with AESIC-REQ-130's own retry-is-recovery model |
| 10 | Recovery attempts to overwrite a newer current-effective pointer | Cannot happen as a stale overwrite: the retry always reads the *current* pointer fresh and computes its own classification against it — there is no code path that writes based on a remembered, pre-crash pointer value (§10 above) |
| 11 | Recovery is repeated multiple times | Each repetition independently re-enters the same fresh-comparison path; once canonical, every further repetition is a no-op (AESIC-REQ-023(a)) — idempotent by the same mechanism ordinary Stage 2 idempotency already provides, confirming AESIC-REQ-131's own "repeated recovery is idempotent" claim |
| 12 | Recovery races with a new Stage 2 supersession | Governed by AESIC-REQ-120's existing last-write-wins concurrency rule (AESIC-REQ-130 item 6) — no distinct mechanism, no distinct risk beyond ordinary concurrent-Stage-2 behavior already verified in §8 |
| 13 | Pointer-update failure confused with pointer corruption | Independently confirmed non-overlapping by construction: `CanonicalPointerUpdateFailedError` is raised only from within the write step itself (never after a successful read of a pointer); `CanonicalPointerCorruptError` is raised only from a read-time digest-verification failure of a pointer that already exists — the two exception types can never both apply to the same event |
| 14 | Candidate AER valid but pointer reconstruction yields a different digest | Not a defined operation under AESIC-REQ-130 — "reconstruction" is explicitly rejected (item 4); the only sanctioned path is a fresh retry through `evaluate_stage_2`, which computes its own new `pointer_digest` (AESIC-REQ-126 item 1) at its own new write, never "reconstructs" a digest for an orphaned candidate |
| 15 | Recovery would require mutating immutable history | Never occurs — recovery always writes a *new* compound-keyed AER (AESIC-REQ-130 item 4(b)) or reuses an existing canonical one unchanged (no-op); no code path in AESIC-REQ-130 touches an existing AER's own content |
| 16 | Recovery after restart produces a different result from uninterrupted execution | Precluded by AESIC-REQ-130 item 5's explicit tie to AESIC-REQ-077 (§10 above) |

No scenario produces an undefined, ambiguous, or contradictory outcome.

---

## 13. Recovery-as-Retry Model — Independent Confirmation

Every element independently confirmed:

- The committed AER is detected: via the ordinary AESIC-REQ-023 fresh
  comparison, not a special scan (item 3).
- Candidate eligibility is revalidated: the retry performs the complete
  Stage 2 sequence again, including AESIC-REQ-123's own validation of
  any re-supplied `stage_1_result` — nothing is short-circuited.
- Stage 1/Stage 2 equivalence is re-evaluated where required: confirmed,
  same procedure as any other Stage 2 attempt (AESIC-REQ-121/129).
- A stale candidate cannot become current merely because it is unpointed:
  confirmed — item 4 explicitly forecloses this ("SHALL NOT infer... it
  is the most recent... entry").
- A newer pointer cannot be overwritten by an older retry: confirmed —
  the retry always computes against the *current* pointer, never a
  remembered one (§12 scenario 10).
- Pointer creation remains integrity-checked: `pointer_digest` is
  computed at every write, including a retry's own write (AESIC-REQ-126
  item 1, unmodified, applies uniformly).
- Repeated recovery is idempotent: confirmed (§12 scenario 11).
- Immutable AER history is never modified: confirmed (§12 scenario 15).
- Failure remains disclosure-only and does not broaden authority:
  confirmed — `CanonicalPointerUpdateFailedError`'s only effect is to
  cause a caller-owned retry (AESIC-REQ-131); no new capability, gate, or
  authorization is introduced or implied at any point in this mechanism.

**No special recovery authority remains undefined** — recovery uses
exactly AES's own pre-existing `evaluate_stage_2` capability, exercised
by AES's own pre-existing caller, through AES's own pre-existing
idempotency logic. No new actor, no new privilege level, and no new
entry point is introduced by this repair.

---

## 14. Error Taxonomy Verification

`CanonicalPointerUpdateFailedError` and `CanonicalPointerCorruptError`
independently confirmed distinct and non-overlapping (§10, §12 scenario
13 above). Ownership, independently re-derived from AESIC-REQ-131's own
text and cross-checked against the §13 failure-ownership table's new row:

| Dimension | `CanonicalPointerUpdateFailedError` | `CanonicalPointerCorruptError` |
|---|---|---|
| Origin | AES's own pointer-write step (synchronous, same call) | The pointer artifact's own storage (detected at read time) |
| Detection owner | AES, synchronously, within the same `evaluate_stage_2` call | AES, at a `package_id` lookup, any restart point |
| Recovery owner | AES's caller, via retry | Operator (tampering/corruption investigation) |
| Retry owner | AES's caller | N/A (not a transient condition) |
| Logging owner | AES (two distinguishable events: successful AER write, failed pointer write) | AES |
| User-visible owner | AES's caller | Whoever performs the `package_id` lookup |

No ownership gap or dual authority found for either type, confirming
§13's own "no ownership gap... exactly as every other failure type"
claim.

**Partial success is correctly represented, never falsely reported as
full success:** independently confirmed — `CanonicalPointerUpdateFailedError`
is *raised* (an exception, not a return value), so no code path exists
by which a caller could receive a success indication while the pointer
write actually failed. "AER committed, pointer not yet advanced" is a
distinct, named, loggable state (AESIC-REQ-131's own two-event logging
requirement), not an undifferentiated failure.

Both exceptions are confirmed to fall within "the error taxonomy of §13"
(AESIC-REQ-010's own repaired text explicitly lists both by name as
within, not exceptions to, that requirement) — no violation of the
"only the error taxonomy of §13, never a bare `Exception`" rule.

---

## 15. Pointer and AER Consistency — Independent Verification

After all retries and recovery, independently confirmed:

- The current pointer references an existing immutable AER: structural
  guarantee — a pointer is only ever written (AESIC-REQ-119 item 2)
  after its referenced AER's own compound-key commit (item 1) succeeds;
  no code path writes a pointer to a not-yet-committed AER.
- `record_id`/`record_digest` match the selected AER: enforced at
  read time by AESIC-REQ-126 item 2's own mandatory cross-check, raising
  `CanonicalPointerCorruptError` on any mismatch.
- The pointer digest validates: same mechanism, item 2(a).
- The compound key matches: `(package_id, evaluation_id)` is used
  identically for the write (item 1) and the pointer's own
  cross-reference (item 2(b)) — no separate, potentially-divergent
  keying scheme exists.
- Stage 1 evidence in the selected AER is the correct effective
  evidence: guaranteed by AESIC-REQ-129 being the sole determinant of
  whether that AER was reused (equivalent) or newly created (not
  equivalent) — never independently re-derived after the fact.
- No newer valid superseding AER is ignored: every fresh Stage 2 attempt
  always re-reads the *current* pointer (never a cached or remembered
  one), so a genuinely newer AER is always the one compared against.
- No older AER is silently restored: recovery never "restores" — it
  either reuses the current canonical AER (no-op, only when equivalent)
  or creates a new one (supersession); nothing in AESIC-REQ-130
  re-points the canonical pointer backward to an older entry.
- Every committed AER remains auditable: AESIC-REQ-119 item 1's "never
  deleted" guarantee, unaffected by this repair, confirmed unchanged by
  direct re-reading.
- Only one AER is current-effective per compound key: the pointer is a
  single mutable artifact per `package_id` (not per compound key — the
  compound key identifies a specific AER; the pointer identifies which
  one, singular, is canonical for the `package_id`), confirmed
  structurally single-valued.

---

## 16. Full Contract Consistency Audit

Re-reading AESIC-001 v1.3 in full (§1–§36, all 131 requirements),
independently checked for:

- **Contradictions introduced by AESIC-REQ-129–131:** none found. Each
  interacts with exactly the requirements it explicitly extends
  (AESIC-REQ-023, 057, 076, 102, 121, 087's table) and is confirmed
  compatible with every requirement it does not touch (§33.7/33.8's own
  audit, independently re-verified in §5–§15 above rather than merely
  accepted).
- **Conflicts with untouched idempotency requirements:** AESIC-REQ-022
  (Stage 1 idempotency-free-by-construction) is unaffected — this
  repair governs only Stage 2's idempotency test, never Stage 1's own
  (definitionally trivial) idempotency. AESIC-REQ-104 (concurrent
  idempotency SHALL hold) independently reconfirmed still holding under
  the extended comparison (§8 above).
- **Conflicts with the Stage 1 transport model:** AESIC-REQ-064/078/080's
  "exactly one artifact type, Stage 1 never independently persisted"
  boundary independently reconfirmed intact — AESIC-REQ-129 reads only
  already-in-hand values (§5, "no widening found" independently
  re-derived, not merely quoted from §33.8).
- **Conflicts with immutable AER history:** none — confirmed throughout
  §6–§15, no code path in either new requirement set mutates an
  existing AER.
- **Conflicts with pointer integrity rules:** AESIC-REQ-126/127 confirmed
  entirely untouched by this repair's text (no edit to §12.1's pointer
  digest/verification prose); the two mechanisms (corruption detection
  vs. update-failure/uncommitted-candidate handling) are confirmed
  disjoint (§10, §14 above), not merely asserted disjoint.
- **Restart-matrix omissions:** none remaining, per §11's independent
  boundary-by-boundary reconstruction.
- **Duplicate or invalid requirement references:** none found; every
  citation from AESIC-REQ-129–131 to another `AESIC-REQ-###` resolves to
  a requirement that exists and says what it is cited as saying (spot-
  checked: AESIC-REQ-098's uniqueness claim, AESIC-REQ-123's four checks,
  AESIC-REQ-077's observational-equivalence text, AESIC-REQ-119's
  two-item storage model — all independently re-read and confirmed to
  match their citations).
- **Undefined terminology:** none — "uncommitted candidate," "recovery,"
  "Stage-1-evidence-equivalent" are each defined at first use
  (AESIC-REQ-130 item 2, item 4, AESIC-REQ-129 respectively) before any
  later section relies on the term.
- **Error-taxonomy overlap:** none (§14).
- **Failure-ownership gaps:** none (§14, §13's new table row carries
  every required ownership dimension).
- **Diagrams inconsistent with normative text:** AESIC-001 contains no
  diagrams (prose-only contract, confirmed by full read) — not
  applicable.
- **Verification-matrix inconsistencies:** §21's Requirement/Test Matrix
  independently checked — AESIC-REQ-129/130/131 each appear exactly
  once, with a falsifiability anchor that correctly names the
  requirement(s) each was checked against for non-contradiction; no
  entry is missing, duplicated, or misattributed.

**Requirement IDs independently confirmed unique and stable:** all 131
IDs (`AESIC-REQ-001`–`AESIC-REQ-131`) enumerated via §21's own matrix
and cross-checked against every in-body citation found during the full
read (§3–§16 above); no gap, no reuse, no renumbering found across all
four revisions (v1.0 → v1.3), matching the contract's own §21 tally
(117 + 4 + 7 + 3 = 131) independently re-summed and confirmed correct.

---

## 17. Requirement Verification Matrix

| Requirement | Necessary | Sufficient | Independently supported | Internally consistent | Externally compatible | Implementable | Deterministic | Ambiguous | Contradictory |
|---|---|---|---|---|---|---|---|---|---|
| AESIC-REQ-010 | Yes (taxonomy must include the two new exception types) | Yes | Yes (§14) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-023 | Yes (branch decision must incorporate Stage 1 evidence) | Yes, jointly with 121/129 | Yes (§6, §7) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-057 | Yes (must state the no-op-inclusive scope explicitly) | Yes, given 023/121/129 hold | Yes (§7) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-076 | Yes (matrix completeness, AESIC-REQ-103) | Yes, jointly with 130/131 | Yes (§11) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-102 | Yes (must disclose zero added I/O cost) | Yes | Yes (independently re-derived: both new comparisons read only already-fetched bytes/in-memory parameters, §5, §10) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-121 | Yes (host requirement for the extended comparison) | Yes, jointly with 129 | Yes (§5) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-129 | Yes (Finding A's own closing mechanism) | Yes, alone, for the equivalence test itself | Yes (§5, §6) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-130 | Yes (Finding B's own closing mechanism) | Yes | Yes (§10, §11, §12) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-131 | Yes (disjoint failure case AESIC-REQ-130 item 7 requires) | Yes | Yes (§10, §14) | Yes | Yes | Yes | Yes | No | No |

**Untouched requirements materially affected by the repair** (identified
independently, then cross-checked against §33.7's own list — found to
match exactly): AESIC-REQ-018 (replay determinism — its "modulo
`evaluated_at`" framing is now also the basis for AESIC-REQ-121/129's own
exclusion, cited but not altered); AESIC-REQ-077 (observational
equivalence — now explicitly satisfied for a new restart point,
AESIC-REQ-130 item 5, without its own text changing); AESIC-REQ-098
(`evaluation_id` uniqueness — now also the reason `evaluation_id` is
excluded from AESIC-REQ-129's comparison, without its own text
changing); AESIC-REQ-119/120 (two-tier storage/concurrency — now the
mechanism AESIC-REQ-130 explicitly builds its recovery model on top of,
without their own text changing). No requirement outside this list and
§33.7's own enumeration was found materially affected.

---

## 18. Architectural Preservation

Each invariant independently falsification-tested (not merely read from
§33.8's own claim):

| Invariant | Attempted falsification | Result |
|---|---|---|
| AES sole lifecycle orchestrator | Does AESIC-REQ-129/130 introduce any new actor that resolves, evaluates, or persists? | No — every operation named is AES's own, pre-existing responsibility, exercised through the pre-existing `evaluate_stage_2` entry point |
| Evaluator remains pure/deterministic | Does either new requirement name `evaluate()` as a participant? | No — both consume already-produced `outcome`/`AuthorityEvaluationOutcome` values only |
| Registry remains lookup-only | Does recovery add a Registry write path? | No — AESIC-REQ-130's retry re-enters ordinary Stage 2, which only ever calls `Registry.resolve()` (§7, unmodified) |
| Decision Template Resolution remains AES-owned | Same test | No new caller of Resolution introduced |
| Publication Coordinator remains publication-only | Does Finding A/B's repair touch §14's consumer table? | No — §14 is byte-for-byte unmodified by this repair |
| Stage 1 remains advisory and optional | Does AESIC-REQ-129 make Stage 1 supply mandatory in any circumstance? | No — `stage_1_result=None` remains always valid (AESIC-REQ-125, unmodified); AESIC-REQ-129 branch 1 explicitly classifies both-absent as equivalent, never as an error |
| Stage 2 unconditionally supersedes Stage 1 for effective citation | Does the repair introduce any Stage 1-to-citation path? | No — AESIC-REQ-070/071 byte-for-byte unchanged; `citation_text` is untouched by AESIC-REQ-129 |
| Valid Stage 1 evidence participates in Stage 2 identity without becoming durable standalone state | Does AESIC-REQ-129 require a new store? | No — confirmed in §5, §16 ("no widening found") |
| AER history remains immutable | Does any new requirement provide an update/patch path? | No — every new write is a genuinely new AER (§7, §13 scenario 15) |
| Canonical pointer remains the only mutable current-effective selection state | Does AESIC-REQ-130 introduce a second mutable artifact? | No — the "uncommitted candidate" is an ordinary, immutable primary-store entry; only the pointer itself is ever mutated (replaced) |
| Replay remains observationally equivalent | Tested directly, all nine + two new restart points | Confirmed (§9, §10) |
| Evaluation remains disclosure-only | Does recovery introduce any gating behavior? | No — recovery only ever causes a return value or a caller-visible exception, never blocks or auto-selects anything |
| No authorization/confirmation/readiness/publication/permission/execution gate introduced | Direct text search across AESIC-REQ-129/130/131 | None found — no requirement conditions any downstream action on these new mechanisms beyond AES's own internal write sequencing |
| Runtime capability remains unchanged | `git status --short` / §34 confirmation | Confirmed — no `src/pcae/**`, schema, test, or runtime file touched by Phase 147L.5 (independently re-verified via `pcae check`/`pcae health`, §21 below) |

Every invariant survives independent falsification attempt. No invariant
was found weakened, narrowed, or contradicted.

---

## 19. Cross-Contract Compatibility

Independently re-read (not merely cited) for each predecessor contract:

- **AEM-001 / AEMIC-001.** `AuthorityEvaluationOutcome`'s exact field
  shape (AEMIC-REQ-021, §3.1 above) independently confirmed unmodified
  and sufficient as the basis for AESIC-REQ-129's field-by-field
  comparison — no field this repair relies on is absent from the
  already-frozen shape, and no field this repair excludes
  (`evaluated_at`) was excluded incorrectly (it is metadata by AEMIC-001's
  own §6 framing, independently confirmed, not merely trusted). One
  pre-existing, out-of-scope textual discrepancy noted (§19.1 below).
- **IWC-001.** `Session.session_id`'s already-populated status
  independently reconfirmed via direct read of IWC-001 §26.1
  (`PublicationHandoff.build_package` already receives a full `Session`
  object; the Coordinator's own constructed record already carries
  `session_id`) — this repair adds no new reader beyond what
  AESIC-REQ-122 (v1.2) already established; AESIC-REQ-129 merely
  compares a field already read, introducing no new IWC-001 dependency.
- **IWPC-001.** Last-write-wins pointer precedent (IWPC-REQ-144/147)
  independently confirmed as the same precedent AESIC-REQ-120 (v1.1,
  unmodified) already cited — this repair introduces no new concurrency
  mechanism, only a name for an existing crash window (§33.6, confirmed).
- **PEC-001.** Publication ownership and duplicate-publication handling
  (Coordinator's own idempotency marker) confirmed entirely untouched —
  AESIC-REQ-130/131 govern only AES's own internal AER/pointer
  persistence, never Coordinator-level publication state.
- **CHGR-001.** Citation-only integration (`citation_text` alone flows
  into `authority_basis_claimed`) confirmed untouched — no new requirement
  touches §14/§8.7.

**Disclosure-only semantics, publication idempotency precedent, and
duplicate-publication behavior** all independently reconfirmed
unaffected — this repair's scope is bounded to AES's own Stage 2
idempotency-comparison and post-AER/pre-pointer persistence mechanics,
neither of which is a citation, publication, or CHGR-construction
concern.

**Determination: no predecessor-contract amendment is required** —
confirmed independently, not merely accepted from §33.9.

### 19.1 Pre-existing, out-of-scope observation

AEMIC-REQ-021's own header text ("exactly the eight fields") does not
match its own table, which lists nine (`template_ref`, `template_version`,
`claimed_identity`, `evaluation_result`, `declaration_ref`,
`citation_text`, `evaluated_at`, `evaluator_version`, `schema_version`).
This discrepancy exists in AEMIC-001 itself, predates AESIC-001 entirely,
and is orthogonal to AESIC-REQ-129's own comparison (which operates over
whatever the actual field set is, not over the count stated in
AEMIC-001's prose) — noted here only because this verification's method
requires independently re-deriving cited shapes rather than trusting
citation counts, and the discrepancy was surfaced by that process. **Out
of scope for this phase** (AEMIC-001 is a frozen predecessor contract;
§22's No-Go Boundary forbids modifying it here) — reported as
Informational in §19 below, not as a finding against AESIC-001 v1.3.

---

## 20. Independent Threat Analysis

| Threat | Independently assessed disposition | Classification |
|---|---|---|
| Deliberate Stage 1 evidence omission (caller withholds evidence to force a no-op that hides disagreement) | Withholding (`stage_1_result=None`) is always valid and never itself deceptive — the resulting AER simply has no `stage_1_outcome_ref`, honestly disclosing that no Stage 1 evidence was supplied for *this* attempt; a prior AER with evidence remains independently retrievable by its own compound key. No mechanism is defeated because none claims to force Stage 1 supply. | Informational |
| Substitution of alternate valid evidence (swap in a different session's genuinely-valid Stage 1 result) | Prevented by AESIC-REQ-123 checks 2–4 before AESIC-REQ-129 is ever reached (§6 scenarios 5–8, 11) | Not exploitable |
| Canonical-equivalence confusion (craft input that is field-equal but semantically different) | Not possible under this domain model — `AuthorityEvaluationOutcome`'s fields are exhaustively defined (AEMIC-001 §6); field-equal implies semantically identical by the type's own construction invariants (AEMIC-REQ-022) | Not exploitable |
| Replay-based history replacement (replay an old call to overwrite newer canonical state with stale content) | Precluded — every replay recomputes fresh against Registry/template state *at replay time*, never replays a stored past comparison result (§9) | Not exploitable |
| Concurrent supersession (race two attempts to force a particular outcome canonical) | Possible in the sense that last-write-wins is timing-dependent by design (disclosed, existing precedent, IWPC-REQ-144/147) — but neither racer can force data loss or corruption, only which valid, independently-derived AER becomes canonical first | Informational (disclosed, pre-existing, unaffected by this repair) |
| Race-induced pointer rollback (force the pointer backward to an older AER) | Not possible — no code path re-points to an older entry; every write is either a fresh no-op-return of the *current* canonical AER or a new supersession, never a backward move (§15) | Not exploitable |
| Orphaned committed AER exploitation (use an orphaned candidate to trick a consumer into treating it as canonical) | Every ordinary consumer reads only through the pointer (AESIC-REQ-119 item 2's read-indirection); an orphan has no independent lookup-by-`package_id` path — only compound-key access, which no ordinary consumer performs (§14.1, unmodified) | Not exploitable |
| Stale-candidate recovery (recovery logic infers canonicity from recency) | Explicitly forbidden by AESIC-REQ-130 item 4 and confirmed absent from the mechanism (§10, §13) | Not exploitable |
| Pointer-update failure suppression (hide a failed pointer write as success) | Precluded — `CanonicalPointerUpdateFailedError` is raised, not swallowed (§14) | Not exploitable |
| Corrupt-pointer misclassification (confuse update-failure with corruption to evade operator review) | Confirmed structurally disjoint, cannot co-occur for the same event (§14, §12 scenario 13) | Not exploitable |
| Denial of service through repeated failed recovery | Each retry is bounded, local work (no unbounded loop, no exponential resource growth); a persistently failing storage layer produces a persistently repeated, disclosed `CanonicalPointerUpdateFailedError`, never silent resource exhaustion or an infinite internal retry (AESIC-REQ-131: "never an automatic AES-internal repair" — AES itself does not loop) | Informational (bounded by design; a persistently failing storage layer is an operational, not a contract, concern) |
| Cross-session AER selection | Prevented at Stage 1-handoff validation (AESIC-REQ-123 check 2) and structurally — AERs are keyed by `package_id`, unique per session's own readiness package (§15's existing "Cross-session reuse" mitigation, unaffected) | Not exploitable |
| Compound-key collision or confusion | Precluded by AESIC-REQ-098's per-invocation uniqueness guarantee, unmodified and independently re-confirmed still load-bearing under this repair (§5, §8) | Not exploitable |
| Authority confusion from differing Stage 1 and Stage 2 outcomes | Explicitly addressed by design, not a threat this repair introduces — §9.4/§8.6 already require disagreement to be surfaced, never merged; this repair only ensures the surfacing itself (`stage_1_outcome_ref`'s presence) cannot be silently dropped by idempotency (Finding A's own subject) | Addressed by existing + repaired mechanism |

No new Blocking, Major, or Minor finding emerged from this threat pass.
Two Informational observations are carried into §21 below.

---

## 21. Findings

No Blocking findings. No Major findings. No Minor findings.

### Informational-1 — Return-value semantics under a lost pointer race are not explicitly stated

**Observation.** When two `evaluate_stage_2` attempts for the same
`package_id` race and both persist distinct, valid compound-keyed AERs
(§8), AESIC-REQ-120's last-write-wins rule determines which one's
pointer write completes last and therefore becomes canonical. AESIC-001's
text does not explicitly state whether the *losing* attempt's own
`evaluate_stage_2` call returns the AER it itself just wrote (which will
turn out, once the race resolves, to not be canonical) or is somehow
made aware of the eventual winner. §5.2's public interface (AESIC-REQ-007)
returns `AuthorityEvaluationRecord` synchronously from the call, which —
read together with §5.11/§12.1's own text — most naturally means each
call returns the AER it itself produced or found, not a value that
depends on a race outcome that may not even be resolved yet at return
time. This reading is consistent with AESIC-REQ-057's own "the AER Stage
2 actually returns on every attempt" framing (repaired language, Phase
147L.5) and does not contradict any requirement.

**Assessment.** This is not a defect: derivable unambiguously from
existing text (a synchronous method returns its own call's own result;
nothing in the contract suggests an out-of-band notification mechanism,
which would itself require a new component this contract's §4 does not
name), consistent with the already-accepted IWPC-REQ-144/147 last-write-
wins precedent, and does not affect Finding A/B closure, idempotency
correctness, or data integrity (the losing AER remains durably valid and
independently retrievable — it is simply not canonical). A future
implementation or documentation phase MAY state this explicitly for
implementer clarity, but no contract text is unsatisfiable or
self-contradictory as written.

**Severity and disposition.** **Informational.** No repair is proposed or
required; reported for completeness per this phase's own thoroughness
obligation, not as an unresolved defect.

### Informational-2 — AEMIC-REQ-021 field-count/table mismatch (pre-existing, out of scope)

See §19.1. Pre-existing in AEMIC-001 v1.2, orthogonal to AESIC-001 v1.3's
own correctness, out of this phase's No-Go Boundary to repair. Reported
for completeness only.

---

## 22. Overall Verdict

Independently confirming, criterion by criterion (§23 of the authorizing
prompt):

- Finding A is demonstrably resolved — confirmed, §5–§9.
- Finding B is demonstrably resolved — confirmed, §10–§13.
- No unresolved Blocking or Major contract inconsistency remains —
  confirmed, §16, §21 (zero Blocking/Major/Minor findings).
- Idempotency preserves all valid Stage 1 evidence — confirmed, §6, §7.
- Equivalent retries remain no-ops — confirmed, §5, §6 (scenario 14), §7.
- Material differences produce deterministic supersession or refusal —
  confirmed, §6, §7.
- Post-AER/pre-pointer restart is safe — confirmed, §10, §11, §12.
- Recovery cannot overwrite newer state — confirmed, §12 (scenario 10),
  §13.
- Pointer and AER integrity remain coherent — confirmed, §15.
- Replay remains observationally equivalent — confirmed, §9, §10 (item
  5).
- Architecture remains preserved — confirmed, §18 (falsification
  attempted against all 14 named invariants, none defeated).
- No predecessor-contract amendment is required — confirmed, §19.

**AESIC-001 v1.3 INDEPENDENTLY VERIFIED.**

---

## 23. Recommended Next Phase

**147M — Authority Evaluation Integration Implementation.** AESIC-001
v1.3 is independently verified with no unresolved Blocking or Major
contract defect (§21–§22). Phase 147M shall be the first integration
implementation phase and shall implement only the frozen and
independently verified AESIC-001 v1.3 contract: the Authority Evaluation
Service; Decision Template Resolution; abstract Authority Registry
interaction; `Stage1EvaluationResult`; Stage 1 validation and equivalence
semantics; immutable Authority Evaluation Record persistence; two-tier
compound-key storage; the canonical current-effective pointer; pointer
integrity validation; post-AER/pre-pointer retry and recovery;
Interactive Workflow integration; readiness and publication integration;
CHGR citation-only integration; diagnostics, inspection, logging, and
audit support; and comprehensive adversarial and regression tests. It
shall not amend AESIC-001, broaden architectural scope, alter
disclosure-only semantics, add authorization or execution gating, or
change runtime capability without separate authorization.

**This recommendation is not an authorization.**
