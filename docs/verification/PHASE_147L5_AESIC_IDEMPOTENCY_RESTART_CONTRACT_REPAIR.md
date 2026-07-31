# Phase 147L.5 — AESIC-001 Stage 1 Idempotency and Restart-Matrix Contract Repair

**Phase ID:** 147L.5
**Mode:** Contract Repair (no implementation, no schema change, no
runtime change, no production source change)
**Baseline:** AESIC-001 v1.2
(`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`)
**Result:** AESIC-001 v1.3
**Date:** 2026-07-31

---

## 1. Executive Summary

Phase 147L.4 independently verified AESIC-001 v1.2 and confirmed both
Phase 147L.2 findings (§3.1, §3.2) resolved, but its own fresh adversarial
process surfaced two new, Non-Blocking findings against requirements the
v1.2 repair correctly left untouched:

- **Finding A [Major, Non-Blocking].** The Stage 2 idempotency no-op
  branch (AESIC-REQ-023(a), gated by AESIC-REQ-121's equality procedure)
  compares only `citation_text` and `AuthorityEvaluationOutcome` fields —
  never whether a `stage_1_result` was supplied, or its content. A
  legitimately-obtained, fully-validated `stage_1_result` supplied to a
  Stage 2 attempt that turns out to be a same-outcome retry is therefore
  silently discarded: the no-op branch returns the *existing* canonical
  AER, which may lack the current attempt's own `stage_1_outcome_ref`
  entirely, contradicting AESIC-REQ-057's "MUST carry... whenever
  supplied" guarantee.
- **Finding B [Minor, Non-Blocking].** §11.2's restart matrix, which
  AESIC-REQ-103 requires to name every restart point, has no row for a
  crash between the AER's own compound-key commit (AESIC-REQ-119 item 1)
  and the canonical pointer's own write (AESIC-REQ-119 item 2) — a
  restart point the two-tier storage model itself structurally
  introduces.

This phase performs a strictly bounded repair addressing exactly these two
findings, converting AESIC-001 from v1.2 to v1.3. Finding A is closed by
extending the existing idempotency equality procedure (AESIC-REQ-121) to
also compare Stage 1 evidence, via a new, deterministic
Stage-1-evidence-equivalence definition (AESIC-REQ-129): a same-outcome
no-op is now reachable only when the canonical AER's own Stage 1 evidence
is equivalent to what this attempt supplied; any mismatch — including the
canonical AER carrying none at all — is now classified "changed" and
triggers genuine supersession (AESIC-REQ-023(b)), producing a new,
immutable AER that correctly carries the current attempt's own evidence.
Finding B is closed by two new restart-matrix rows (AESIC-REQ-076) and a
new normative recovery rule (AESIC-REQ-130): a committed-but-not-yet-
pointed-to AER is an uncommitted candidate, never automatically canonical;
recovery is retry, never reconstruction; and a new exception,
`CanonicalPointerUpdateFailedError` (AESIC-REQ-131), covers the distinct,
same-process case where the pointer write itself fails synchronously.

**Overall Verdict: AESIC-001 v1.3 REPAIRED.**

---

## 2. Scope

Per the authorizing prompt's explicit scope boundary, this repair
addresses only:

- the idempotency-no-op-vs.-mandatory-`stage_1_outcome_ref` contradiction
  (Finding A)
- the missing AER-commit/pointer-write restart-matrix row (Finding B)

It does not redesign AES, broaden the public API, change the two-stage
lifecycle, change Stage 2's unconditional supersession principle, change
the compound-key AER model's own storage mechanics, introduce
implementation details, or amend any predecessor contract. Every existing
architectural decision AESIC-001 v1.2 already froze is preserved (§13
below).

---

## 3. Finalized 147L.4 Findings

Both findings are treated as completed, authoritative substantive work
per this phase's own authorization — re-derived here from primary
sources (the specific AESIC-001 v1.2 requirement text each finding names),
not merely restated from Phase 147L.4's own account, before any repair
was drafted.

**Finding A, re-derived from AESIC-001 v1.2's own frozen text.**
AESIC-REQ-057 (v1.2): "The AER MUST carry a `stage_1_outcome_ref` field
whenever the caller supplies AES a valid `stage_1_result` for the same
`evaluate_stage_2` call." AESIC-REQ-121 (v1.2): the idempotency equality
procedure compares "the freshly (re-)resolved `citation_text`" and "every
field of the freshly (re-)computed `AuthorityEvaluationOutcome`" —
excluding `evaluated_at` — against the canonical AER's corresponding
fields; nothing else. AESIC-REQ-023(a) (v1.2): "if the freshly-computed
result is unchanged... return that already-persisted AER unchanged — no
new AER SHALL be written." A concrete instance: a `package_id`'s canonical
AER was established without any `stage_1_result` (none was supplied).
Later, the same caller invokes `evaluate_stage_2` again for the same
`package_id`, this time supplying a genuine, `AESIC-REQ-123`-validated
`stage_1_result`. Because AESIC-REQ-121's comparison never examines Stage
1 evidence, and the underlying `citation_text`/outcome are otherwise
unchanged (nothing in the Registry or Decision Template changed), the
comparison classifies this attempt "unchanged." AESIC-REQ-023(a) then
requires AES to return the existing canonical AER — which has no
`stage_1_outcome_ref` — even though this call's own `stage_1_result` was
genuinely supplied and validated. AESIC-REQ-057's own guarantee is
violated for the AER this call actually returns.

**Finding B, re-derived from AESIC-001 v1.2's own frozen text.**
AESIC-REQ-119 (v1.2, item 1 then item 2): Stage 2 persistence is
inherently two sequential writes — "a first compound-keyed write,
followed by the pointer index's own first, exclusive-create write"
(degenerate/first-ever case), or, for supersession, a new compound-keyed
write followed by an atomic pointer replace. AESIC-REQ-103 (v1.2, §17):
"Every restart point named in §11.2 SHALL have a defined, safe resumption;
no future implementation SHALL introduce a restart point without an entry
in that matrix." §11.2's own table (v1.2), re-read row by row, names ten
restart points plus the three Phase 147L.3 added for the Stage 1 channel
— none of them describes a crash *between* AES's own two sequential
writes within a single Stage 2 attempt. This is a distinct restart point
from "canonical pointer corrupted" (AESIC-REQ-126/127, which governs a
pointer that is present but internally inconsistent, not one that is
simply absent-or-stale because its own write has not yet happened).

Both findings are confirmed, independently, to be genuine — not artifacts
of Phase 147L.4's own framing — before any repair text was drafted.

---

## 4. Finding A Root Cause

**What constitutes the Stage 2 compound evaluation key.** `(package_id,
evaluation_id)` (AESIC-REQ-119 item 1, unaffected by this repair) — this
repair does not touch the storage key.

**What constitutes outcome equivalence (before this repair).**
`citation_text` plus every field of the freshly-computed
`AuthorityEvaluationOutcome`, excluding `evaluated_at` (AESIC-REQ-121, v1.2
text). Stage 1 evidence (`stage_1_result`/`stage_1_outcome_ref`) does not
participate at all.

**Whether Stage 1 evidence participates in equivalence (before this
repair).** No — this is precisely the gap.

**What the existing no-op branch returns.** The already-persisted,
canonical AER, unchanged, byte-for-byte, including whatever
`stage_1_outcome_ref` (or its absence) that AER happened to carry from
whichever earlier attempt established it as canonical (AESIC-REQ-023(a),
v1.2 text).

**Why a valid, newly supplied Stage 1 result can be lost.** Because the
no-op branch's own trigger condition (AESIC-REQ-121's equality procedure)
never inspects Stage 1 evidence, an attempt whose `citation_text`/outcome
are unchanged relative to the canonical AER is classified "unchanged"
regardless of what `stage_1_result` it supplied — including a genuinely
new, valid one the canonical AER does not carry.

**Which requirement requires that evidence to be retained.** AESIC-REQ-057
(§8.6): "MUST carry a `stage_1_outcome_ref` field whenever the caller
supplies AES a valid `stage_1_result` for the same `evaluate_stage_2`
call" — a per-call obligation with no textual carve-out for the idempotent
no-op branch.

**Whether the contradiction affects only retries or also concurrent calls
and replay.** Primarily retries (the scenario constructed above). It also
affects concurrent calls in the following sense: two concurrent attempts,
one supplying `stage_1_result` and one not, racing for the same
`package_id`, could — under the unrepaired v1.2 text — resolve to a
no-op/no-op pair or a no-op/write pair depending purely on race timing and
which attempt's comparison ran against which prior state, with no
guarantee that the attempt supplying valid evidence is the one whose
evidence survives. It does not affect pure replay (a replay of an
already-canonical `package_id` never re-invokes or re-validates a
`stage_1_result` at all, per AESIC-REQ-023(a)'s own unchanged
"return... unchanged" behavior — replay was never the mechanism at fault).

This root cause is fully closed by extending AESIC-REQ-121's own
comparison, not by introducing any new mechanism alongside it (§5, §6
below).

---

## 5. Considered Behavioral Models

**Model 1 — Stage 1 evidence participates in idempotency equivalence**
(selected). A same-outcome no-op is permitted only when the existing
canonical AER is also Stage-1-evidence-equivalent (AESIC-REQ-129, new) to
this attempt's own supplied evidence. Otherwise, a new, superseding AER is
required (AESIC-REQ-023(b)).

**Model 2 — valid newly supplied Stage 1 evidence always causes
supersession.** On direct comparison, Model 2's own stated behavior
("when the current canonical AER does not carry that exact Stage 1
evidence, AES creates a new immutable AER... even if Stage 2 citation and
outcome fields are otherwise unchanged") is the exact logical complement
of Model 1's own trigger condition. Every scenario in §8/§10 below produces
an identical outcome under either framing. Model 1 is retained as the
operative mechanism because AESIC-REQ-023 already delegates its entire
branch decision to a single named equality procedure (AESIC-REQ-121);
extending that one procedure preserves this existing structural pattern,
whereas stating Model 2 as an independent, second trigger alongside
AESIC-REQ-121 would introduce two decision points where the contract
currently has one, for no additional expressive power.

**Model 3 — explicit refusal.** Rejected. A refusal (raising an error
rather than embedding the evidence) does not satisfy the authorizing
prompt's own §10 required property ("validated Stage 1 evidence
retention") — it discards the call outright rather than retaining
anything. It is also a strictly larger behavioral change than Models 1/2:
every idempotent retry succeeds today (v1.2), regardless of what
`stage_1_result` it supplies; Model 3 would make a subset of these retries
fail where they previously succeeded, a discontinuity neither Model 1 nor
Model 2 introduces (both preserve "the call always succeeds," differing
only in whether it succeeds via no-op or via supersession).

**Selected: Model 1** (§6 below), on the smallest-footprint criterion the
authorizing prompt's §9 itself names, and because it reuses a mechanism
(equality-procedure extension) this contract has already used twice before
for structurally identical reasons (Phase 147L.1's own introduction of
AESIC-REQ-121 to resolve Finding 2/3).

---

## 6. Selected Idempotency Model

**Model 1 is frozen.** AESIC-REQ-121 (repaired) now compares two things:
(1) `citation_text` and `AuthorityEvaluationOutcome` fields (excluding
`evaluated_at`) — unchanged from v1.2; and (2) whether this attempt's own
(already-AESIC-REQ-123-validated, if supplied) `stage_1_result` is
Stage-1-evidence-equivalent (AESIC-REQ-129, new) to the canonical AER's
own `stage_1_outcome_ref`. Both (1) matching and (2) holding classifies
"unchanged" (AESIC-REQ-023(a)); either (1) differing or (2) not holding
classifies "changed" (AESIC-REQ-023(b)).

**Required properties, independently re-verified against the repaired
text:**

- **Immutable AER history** — preserved; this repair never mutates,
  updates, or deletes an AER; every write remains a genuinely new,
  distinct, immutable compound-keyed entry (AESIC-REQ-054/082/119 item 1,
  untouched).
- **At-most-one canonical current-effective pointer** — preserved;
  AESIC-REQ-119 item 2/AESIC-REQ-120 are untouched by this repair; only
  the *frequency* with which the "changed" branch is taken increases (in
  exactly the cases Finding A identified), never the pointer's own
  single-artifact-per-`package_id` invariant.
- **Deterministic idempotency** — preserved and strengthened;
  AESIC-REQ-129's comparison is a total, deterministic function of
  already-in-hand values (§7 below), so the branch decision remains fully
  deterministic given fixed inputs.
- **Stage 2 supersession** — preserved; AESIC-REQ-070/071 (unconditional
  citation-purpose supersession) untouched; this repair only widens one
  of the conditions under which AESIC-REQ-023(b)'s existing supersession
  mechanism is triggered.
- **Validated Stage 1 evidence retention** — now guaranteed: a no-op is
  reachable, by construction, only when the returned AER already carries
  Stage-1-evidence-equivalent content to what this attempt supplied;
  every other case supersedes and the new AER carries this attempt's own
  evidence exactly (AESIC-REQ-057/118, unaffected).
- **Replay observational equivalence** — preserved; a pure replay (no new
  `stage_1_result`, or an unchanged one) still reaches the identical
  no-op classification it always did (§8 below).
- **Compound-key isolation** — preserved; AESIC-REQ-119 item 1's own
  keying is untouched.
- **Concurrent-call safety** — preserved (§8 below).
- **Disclosure-only semantics / non-gating behavior** — preserved; this
  repair changes only which artifact is returned/persisted, never what any
  consumer may do with it (§14, untouched).

**Defined behavior for every scenario the authorizing prompt's §10
names:**

| Scenario | Result under the repaired contract |
|---|---|
| No Stage 1 result originally, none on retry | Both absent → equivalent (AESIC-REQ-129 rule 1) → no-op if citation/outcome also unchanged, exactly as v1.2 already specified |
| Same Stage 1 result on original and retry | Both present, identical content (excluding `evaluated_at`/`evaluation_id`) → equivalent (rule 3) → no-op if citation/outcome also unchanged |
| Stage 1 absent originally, valid Stage 1 supplied on retry | One absent, one present → not equivalent (rule 2) → "changed" → supersession; new AER carries the newly-supplied evidence |
| One valid Stage 1 result originally, a different valid Stage 1 result later | Both present, differing content → not equivalent (rule 3) → "changed" → supersession; new AER carries the later evidence |
| Malformed Stage 1 result on retry | Rejected by AESIC-REQ-123 (`reason=MALFORMED`) before the idempotency comparison is ever reached — no interaction with Finding A's repair |
| Cross-session or mismatched Stage 1 result | Rejected by AESIC-REQ-123 (`SESSION_MISMATCH`/`IDENTITY_MISMATCH`/`TEMPLATE_MISMATCH`) before the idempotency comparison — no interaction |
| Concurrent calls, same Stage 2 outcome, different Stage 1 evidence | Each independently classified "changed" relative to whatever is canonical at read time; both may persist distinct new AERs; AESIC-REQ-120's existing last-write-wins semantics determines which becomes canonical — no new concurrency mechanism |
| Replay after enrichment or supersession | The now-canonical, Stage-1-enriched AER is what a subsequent no-op-classified replay returns; unaffected by this repair's own mechanics beyond the widened comparison |
| Pointer update failure after a new AER is committed | Governed by Finding B's own repair (AESIC-REQ-130/131), independent of this section |

---

## 7. Stage 1 Evidence Identity

Per AESIC-REQ-129 (new): two Stage 1 evidence states are compared, in
order:

1. **Both absent** (no `stage_1_outcome_ref` on the canonical AER, no
   `stage_1_result` supplied) → equivalent.
2. **Exactly one absent** → not equivalent (introducing or removing Stage
   1 evidence is itself a material change).
3. **Both present** → compared field-by-field on `session_id` (trivially
   satisfied, since both derive from AESIC-REQ-123's own session-binding
   check against the same `session`) and every field of the wrapped
   `AuthorityEvaluationOutcome`, **excluding** `evaluated_at` (metadata
   neither `evaluate()` nor this test branches on, mirroring
   AESIC-REQ-121's own pre-existing exclusion) and **excluding**
   `evaluation_id` (guaranteed unique per invocation by AESIC-REQ-098's
   own construction — including it would make every distinct-but-
   substantively-identical Stage 1 invocation "not equivalent," defeating
   the equivalence test's own purpose).

This basis relies on no object identity, no process memory, and no
implementation-specific serialization: every compared field is a plain
value already defined by AEMIC-001 §6 (`AuthorityEvaluationOutcome`) or
AESIC-REQ-122 (`Stage1EvaluationResult.session_id`). The comparison is
therefore deterministic across restart (a resumed caller re-supplying the
same or a different `stage_1_result` produces the identical classification
an uninterrupted execution would) and across independent implementations
(no implementation-specific hashing, ordering, or timing is involved).

---

## 8. Concurrency and Replay Semantics

**Concurrency.** Two concurrent Stage 2 attempts for the same
`package_id` — whichever combination of Stage 1 evidence they supply —
each independently perform AESIC-REQ-121/129's comparison against
whatever is canonical at the moment each reads it, and each independently
decide no-op or write. Two attempts that both decide "write" persist
distinct, collision-free compound-keyed AERs (AESIC-REQ-098's
per-invocation `evaluation_id` uniqueness, unaffected) and race for the
canonical pointer exactly as AESIC-REQ-120 already specifies
(last-atomic-replace-wins, disclosed, non-authority-relevant). This
repair introduces no new concurrency mechanism — it only changes, in the
specific cases Finding A identified, which attempts decide "write" instead
of "no-op."

**Replay.** A Stage 2 replay for an already-canonical `package_id` — one
that supplies the same or no `stage_1_result` as the attempt that made the
current AER canonical — reaches the identical AESIC-REQ-023(a) no-op
classification a replay always reached under v1.2, because
Stage-1-evidence-equivalence (rule 1 or rule 3, unchanged content) holds.
A replay that supplies genuinely different Stage 1 evidence is, correctly,
no longer classified a no-op — this is not a violation of replay
observational equivalence (AESIC-REQ-077), because "replay" in the
AESIC-001 sense means repeating a call with the *same* inputs; a call
supplying materially different `stage_1_result` content is, by definition,
not the same input, and this repair's entire purpose is to make that
difference observable rather than silently absorbed.

---

## 9. Finding B Root Cause

**The two-tier write sequence.** (1) immutable AER commit — exclusive-create
under the compound key `(package_id, evaluation_id)` (AESIC-REQ-119 item
1); (2) canonical pointer write or update — atomic-replace, keyed by
`package_id` alone (AESIC-REQ-119 item 2).

**The crash window.** Between the completion of (1) and the completion of
(2), within a single Stage 2 attempt (first-ever establishment or
supersession alike).

**Durable state after the crash.** The AER from step (1) exists, durable
and immutable, exactly as any other primary-store entry. The canonical
pointer is in whatever state it was in before this attempt began: absent
(first-ever case) or still naming the previous canonical AER (supersession
case).

**Is the committed AER an orphan, candidate, or effective record?** An
**uncommitted candidate** — never an orphan in the sense of being garbage
or unreachable (it remains durably retrievable by its own compound key,
AESIC-REQ-119 item 1), and never automatically the effective/canonical
record merely by existing.

**How restart discovers it.** Not by scanning the primary store for
uncommitted candidates — by the caller retrying the identical
`evaluate_stage_2` call, which re-runs AESIC-REQ-023's own
fresh-resolution-and-comparison procedure against whatever the canonical
pointer currently names (or its absence).

**How AES determines whether the pointer should be completed,
reconstructed, or left unchanged.** AES never determines this for an
existing uncommitted candidate directly — it always re-derives the answer
fresh, from a fresh evaluation, exactly as any ordinary Stage 2 attempt
does. If the fresh result is equivalent to whatever is currently canonical
(or, for the first-ever case, if this is now the first successful
attempt), a pointer write is made; if not, another new compound-keyed AER
is persisted and a pointer write is attempted for that one instead. The
original crash's own uncommitted candidate is never itself revisited,
completed, or reconstructed from.

**How concurrent supersession affects recovery.** No differently than any
other concurrent Stage 2 attempt (§8 above) — the crash-then-retry
sequence is, from the pointer's own perspective, indistinguishable from
any other pair of attempts racing for the same `package_id`'s canonical
pointer.

**How replay remains observationally equivalent.** Once a retry's own
pointer write succeeds, the observable outcome (the canonical AER, its
`citation_text`, its `stage_1_outcome_ref`) is identical to what an
uninterrupted execution of the same call would have produced —
AESIC-REQ-077 is satisfied for this restart point exactly as it already is
for every other row in §11.2's table.

**Whether recovery may mutate AER history.** No — the recovery model
(AESIC-REQ-130) operates entirely on the *pointer's* own write; the
compound-keyed primary store (AESIC-REQ-119 item 1, "no entry... is ever
updated or deleted") is never written to by any recovery/retry operation,
only read from (via AESIC-REQ-121/129's own comparison).

---

## 10. Restart and Recovery Repair

Two new restart-matrix rows are added under AESIC-REQ-076 (§11.2, table-only
additions, mirroring the Phase 147L.3 precedent of adding rows without a
new requirement number), and a new normative rule, AESIC-REQ-130, defines
the complete recovery model (summarized in the table below; the contract's
own §12.1 text is authoritative):

| Property | Specification |
|---|---|
| Detection | On the next `evaluate_stage_2` retry (or diagnostic lookup), by observing the pointer's own absence-or-staleness relative to the freshly-computed result — never by scanning for uncommitted candidates |
| Ownership | AES (the same component that owns both writes) |
| Recovery | Retry the identical call — never automatic reconstruction from the primary store's own ordering (no such ordering is recorded independently of the pointer, mirroring AESIC-REQ-126 item 4's own reasoning for the analogous corruption case) |
| Retry behavior | A retry recomputes fresh (§6.5) and reaches the same AESIC-REQ-023(a)/(b) classification an uninterrupted execution would; case (a) finds an existing, Stage-1-evidence-equivalent canonical AER (no-op); case (b) persists another new compound-keyed AER (fresh `evaluation_id`) and re-attempts the pointer write |
| Pointer-integrity validation | Unaffected — AESIC-REQ-126/127 continue to govern a pointer that IS present but internally inconsistent; this rule governs the disjoint case of a pointer that has not yet been (successfully) written at all |
| Concurrency behavior | Unchanged AESIC-REQ-120 last-write-wins semantics; no new mechanism |
| Stale-candidate handling | An uncommitted candidate is never treated as automatically canonical merely by existing; only a successful pointer write ever makes an AER canonical |
| Logging and diagnostics | AES logs the AER write and the pointer write as two separate, distinguishable events (extending AESIC-REQ-094) |
| User-visible behavior | A crash-then-retry is invisible to the caller beyond an ordinary retry; a detected synchronous pointer-write failure (not a crash) raises `CanonicalPointerUpdateFailedError` (AESIC-REQ-131) rather than returning success or a stale result |
| Observational-equivalence result | Satisfied (AESIC-REQ-077) — once a retry's pointer write succeeds, the outcome is identical to an uninterrupted execution's own outcome |

**Explicit prohibitions, independently re-verified against the repaired
text:** recovery does not delete or mutate immutable AER history (AER
history is never written to by any recovery operation); does not silently
select an unrelated AER (a retry always re-derives its own answer from a
fresh evaluation, never from scanning uncommitted candidates); does not
overwrite a newer valid canonical pointer (AESIC-REQ-120's own
last-write-wins semantics, unchanged, already governs which write is
"newer"); does not rely on ambient process state (AESIC-REQ-017's
statelessness, unaffected); and does not treat every unpointed AER as
automatically canonical (explicitly stated as prohibited, item 4 of
AESIC-REQ-130).

---

## 11. Requirement Changes

**Text-only repairs (identity preserved):** AESIC-REQ-010 (error taxonomy
extended to name `CanonicalPointerUpdateFailedError`), AESIC-REQ-023
(idempotency branch text, extended to reference Stage-1-evidence-equivalence),
AESIC-REQ-057 (clarified — the mandatory-when-supplied guarantee now
explicitly holds across the no-op branch), AESIC-REQ-076 (two new
restart-matrix rows), AESIC-REQ-102 (performance-budget clarification —
the new comparison introduces no additional I/O), AESIC-REQ-121 (equality
procedure extended to include Stage 1 evidence), AESIC-REQ-087's table
(one new row, table-only, mirroring the Phase 147L.1/147L.3 precedent).

**New requirements:** AESIC-REQ-129 (Stage-1-evidence-equivalence
definition), AESIC-REQ-130 (AER-commit/pointer-write restart and recovery
rule), AESIC-REQ-131 (`CanonicalPointerUpdateFailedError` failure
ownership).

Every requirement the authorizing prompt's §14 named for audit was
individually re-checked (AESIC-REQ-019, 023, 053, 054, 055, 056, 057, 075,
076, 077, 078, 079, 080, 081, 082, 083, 084, 085, 086, 098, 102, 103, 104,
118–128): only AESIC-REQ-010, 023, 057, 076, 102, and 121 required a text
change; the remainder were confirmed unaffected in substance — each was
re-read and found either orthogonal to this repair's two mechanisms
(e.g. AESIC-REQ-053/078, which govern the storage *key*, untouched by an
*equality-comparison* or *restart-recovery* repair) or already fully
compatible (e.g. AESIC-REQ-098's own per-invocation uniqueness, which
AESIC-REQ-129 relies on but does not alter). No requirement was deleted.
No requirement's number was reused or reassigned.

---

## 12. Adversarial Analysis

Each scenario the authorizing prompt's §18 names, attempted fresh against
the repaired contract:

1. **Valid Stage 1 evidence silently discarded by idempotent no-op.**
   Cannot occur — AESIC-REQ-129 makes Stage-1-evidence-equivalence a
   precondition of the no-op classification itself; any attempt supplying
   evidence the canonical AER does not already carry is classified
   "changed" and superseded.
2. **Duplicate retry creates unnecessary AER despite identical Stage 1
   evidence.** Cannot occur — identical content (excluding
   `evaluated_at`/`evaluation_id`) classifies equivalent (rule 3), so the
   retry is a genuine no-op, no new AER is written.
3. **Two different Stage 1 results collapse into one AER.** Cannot occur
   — differing content classifies not-equivalent (rule 3), forcing
   supersession; each genuinely distinct Stage 1 evidence value that ever
   becomes canonical does so via its own, distinct AER.
4. **Concurrent enrichment creates conflicting canonical pointers.** Cannot
   occur — the pointer remains a single, atomically-replaced artifact per
   `package_id` (AESIC-REQ-119 item 2/AESIC-REQ-120, unchanged); concurrent
   writers race to replace the same single artifact, never to create two.
5. **Malformed Stage 1 evidence changes idempotency state.** Cannot occur
   — AESIC-REQ-123 validation completes (pass or raise
   `Stage1HandoffInvalidError`) before the idempotency comparison is ever
   reached; a malformed `stage_1_result` never reaches AESIC-REQ-129's
   comparison at all.
6. **Cross-session Stage 1 evidence causes supersession.** Cannot occur —
   AESIC-REQ-123's `SESSION_MISMATCH` check rejects it before the
   idempotency comparison; a cross-session value never reaches
   AESIC-REQ-129 either.
7. **Restart after AER commit loses the committed record.** Cannot occur —
   the primary store's own immutability (AESIC-REQ-119 item 1) guarantees
   the committed AER survives any crash regardless of pointer state
   (AESIC-REQ-130 item 1).
8. **Recovery advances the pointer to a stale candidate.** Cannot occur —
   AESIC-REQ-130 item 4 explicitly forbids inferring canonicality from mere
   existence; a retry always re-derives its own answer from a fresh
   evaluation.
9. **Recovery overwrites a newer pointer.** Cannot occur — the retry path
   uses the same atomic-replace, last-write-wins mechanism (AESIC-REQ-120,
   unchanged) every ordinary Stage 2 write already uses; there is no
   separate "recovery" write path with different semantics.
10. **Recovery mutates immutable AER history.** Cannot occur —
    AESIC-REQ-130 item 4 explicitly states the primary store is never
    written to by any recovery operation, only read from.
11. **Repeated recovery produces different observable outcomes.** Cannot
    occur — AESIC-REQ-130 item 5 ties the retry path directly to
    AESIC-REQ-077's own observational-equivalence guarantee; every retry
    with the same inputs reaches the same classification and, once its
    pointer write succeeds, the same canonical outcome.
12. **Pointer integrity passes while selecting the wrong Stage 1-enriched
    AER.** Cannot occur — AESIC-REQ-126/127's own integrity check
    (unaffected by this repair) verifies the pointer's `record_digest`
    against the AER it names; a pointer that passes this check is, by
    construction, naming the AER it was written to name — "wrong" in the
    sense of "not the caller's intended evidence" is a supersession/
    equivalence question (§6 above), never an integrity question, and the
    two mechanisms remain correctly disjoint.

The contract provides a deterministic result for every scenario above.

---

## 13. Architectural Preservation

Independently re-checked against AESIC-001 v1.3's current text (see
contract §33.8 for the complete, requirement-by-requirement enumeration;
summarized here):

| Invariant | Status |
|---|---|
| AES sole lifecycle orchestrator | Preserved — AESIC-REQ-005/006 untouched |
| Decision Template Resolution ownership | Preserved — §6 entirely untouched |
| Registry lookup-only ownership | Preserved — §7 entirely untouched |
| Evaluator purity and determinism / Registry exclusion | Preserved — `evaluate()` never named as an actor in any repaired/new requirement |
| Stage 1 advisory semantics | Preserved — AESIC-REQ-062–065 unchanged in substance |
| Stage 2 unconditional supersession | Preserved — AESIC-REQ-070/071 byte-for-byte unchanged |
| Immutable AER history | Preserved — this repair never mutates, updates, or deletes an AER |
| Two-tier compound-key storage model | Preserved — AESIC-REQ-119/120 unchanged in their own text |
| Canonical-pointer integrity | Preserved — AESIC-REQ-126/127 entirely untouched; Finding B's own repair governs a disjoint condition |
| Replay observational equivalence | Preserved — AESIC-REQ-075/077 unchanged; new restart-matrix rows describe newly-named restart points only |
| Publication Coordinator publication-only ownership | Preserved — §14 entirely untouched |
| Disclosure-only semantics | Preserved — §14 entirely untouched |
| Non-gating guarantees | Preserved — AESIC-REQ-090/091 untouched |
| Unchanged runtime capability | Preserved — contract text only; §34 (No-Go Boundary Confirmation) confirms |

Falsification attempted (contract §33.8): could AESIC-REQ-129's
equivalence comparison be read as implicitly requiring AES to gain a new
Stage-1-outcome persistence or lookup capability, reopening Finding 1
(Phase 147L) or AESIC-REQ-064/078/080's "exactly one artifact type"
framing? Checked directly: AESIC-REQ-129 compares only fields already in
AES's hands for this one call (the canonical AER's own already-retrieved
`stage_1_outcome_ref`, and this attempt's own in-memory `stage_1_result`
parameter) — no lookup against any Stage-1-specific store, no independent
persistence of any kind. No widening found.

---

## 14. Cross-Contract Compatibility

Independently confirmed by direct citation-checking against each
predecessor contract's own frozen text, not by relying only on earlier
compatibility conclusions:

- **AEM-001 v1.0.** §7 (Registry) untouched by this repair; no new
  citation.
- **AEMIC-001 v1.2.** AESIC-REQ-129's comparison re-uses the same,
  unmodified `AuthorityEvaluationOutcome` shape (AEMIC-001 §6) v1.2's own
  AESIC-REQ-122 already cites — no new field, no reinterpretation.
- **IWC-001 v1.2.** AESIC-REQ-129's `session_id` comparison re-uses the
  same, already-frozen `Session.session_id` field (IWC-001, already
  independently confirmed present and populated at `Session` construction
  by Phase 147L.4's own source inspection,
  `src/pcae/interactive_workflow/models/session.py:77-104`) v1.2's own
  AESIC-REQ-122/123 already cite — no new obligation on Interactive
  Workflow.
- **IWPC-001 v1.4.** AESIC-REQ-120's own IWPC-REQ-144/147 citation is
  unaffected — this repair does not touch AESIC-REQ-120's own text.
- **PEC-001 v1.1.** §14's consumer table entirely untouched — the
  Coordinator still consumes only `citation_text` via reference.
- **CHGR-001 v1.3.** CHGR construction untouched — `authority_basis_claimed`
  still derives only from Stage 2's `citation_text` (AESIC-REQ-058,
  untouched).

**No amendment to any of the six predecessor contracts is required** —
independently reconfirmed, matching AESIC-REQ-113's own claim across all
four revisions (v1.0, v1.1, v1.2, v1.3).

---

## 15. Validation

```
pcae check                        -> passed
pcae health                       -> healthy
pcae doctor task-memory           -> clean
pcae runtime inspect              -> Observed / observe / unavailable (unchanged)
pcae push check                   -> (see finalization commit for final state)
```

```
python -m pytest -m fast_green -n auto -q
                                   -> 4391 passed (matches expected baseline)
python -m pytest tests/test_phase_147g_authority_evaluation.py \
  tests/test_phase_147h_authority_evaluation_independent_verification.py -q
                                   -> 183 passed (matches expected baseline)
```

Confirmed: zero production changes (`src/pcae/**` untouched), zero schema
changes, zero test changes, zero runtime changes, zero implementation
changes, zero predecessor-contract amendments. Only AESIC-001 itself, this
repair document, and ordinary task/phase bookkeeping files changed
throughout this phase.

---

## 16. Overall Verdict

**AESIC-001 v1.3 REPAIRED.**

- Finding A is fully resolved — valid supplied Stage 1 evidence cannot be
  silently discarded by the idempotency no-op branch (AESIC-REQ-121/129,
  AESIC-REQ-023 repaired).
- Idempotency remains fully deterministic (AESIC-REQ-129's own closed,
  ordered comparison rule).
- Concurrent behavior is defined (unchanged AESIC-REQ-120, now governing a
  correctly-widened set of "changed" classifications).
- Finding B is fully represented in the restart matrix (two new rows under
  AESIC-REQ-076, plus AESIC-REQ-130/131's own normative rules).
- Crash recovery is deterministic (retry, never reconstruction).
- Immutable history and pointer integrity remain preserved
  (AESIC-REQ-054/082/119/126/127, entirely untouched by this repair).
- No new contradiction is introduced (§11's requirement-by-requirement
  audit, §13's architectural-preservation table, the falsification
  attempt in §13).
- No predecessor-contract amendment is required (§14).

---

## 17. Recommended Next Phase

**147L.6 — AESIC-001 Idempotency and Restart Repair Independent
Verification.** That phase shall independently verify AESIC-001 v1.3
against the finalized Finding A and Finding B from Phase 147L.4. It shall
independently reconstruct both findings; verify Stage 1 evidence retention
across idempotency, supersession, concurrency, restart, and replay; verify
the post-AER/pre-pointer crash recovery rule; re-read the complete
contract in full; perform fresh adversarial analysis; and make no contract
or implementation change. Only after successful 147L.6 verification should
the project proceed to 147M — Authority Evaluation Integration
Implementation.

**This recommendation is not an authorization.**

---

**End of Phase 147L.5 Contract Repair.**
