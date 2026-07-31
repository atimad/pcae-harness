# Phase 147L.3 — AESIC-001 Final Contract Repair

**Phase ID:** 147L.3
**Mode:** Contract Repair (no implementation, no schema change, no
runtime change, no production source change)
**Baseline:** AESIC-001 v1.1
(`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`)
**Result:** AESIC-001 v1.2
**Date:** 2026-07-31

---

## 1. Executive Summary

Phase 147L.2 independently verified that AESIC-001 v1.1 (Phase 147L.1's
repair) fully resolved Phase 147L's two Major findings, but its own
adversarial process surfaced two new, Non-Blocking findings against
requirements the v1.1 repair correctly left untouched:

- **§3.1 [Major, Non-Blocking].** `stage_1_outcome_ref`'s embedded-copy
  shape (AESIC-REQ-118) has no defined channel by which the specific
  Stage 1 outcome a caller received from `evaluate_stage_1` can ever reach
  the later, separate `evaluate_stage_2` call that is supposed to embed
  it — `evaluate_stage_2`'s frozen signature (AESIC-REQ-007/012) accepts
  no such input, `Session` may not carry it (AESIC-REQ-060), and AES may
  not hold it across calls (AESIC-REQ-017).
- **§3.2 [Minor, Non-Blocking].** The canonical pointer index
  (AESIC-REQ-119 item 2) has no defined tamper-evidence mechanism, unlike
  the AER itself — a corrupted or substituted pointer could silently
  redirect an ordinary consumer to the wrong AER.

This phase performs a strictly bounded repair addressing exactly these
two findings, converting AESIC-001 from v1.1 to v1.2. Finding §3.1 is
closed by introducing `Stage1EvaluationResult` — the new return type of
`evaluate_stage_1` and the type of a new, optional `stage_1_result`
parameter on `evaluate_stage_2` — through which a caller hands back,
verbatim, the exact value AES already gave it, validated by AES against
the concurrently-supplied `session` before being embedded. Finding §3.2 is
closed by adding a `pointer_digest` field to the canonical pointer and a
mandatory read-time verification obligation cross-checking it against the
referenced AER's own self-carried digest.

**Overall Verdict: AESIC-001 v1.2 REPAIRED.**

---

## 2. Scope

Per the authorizing prompt's explicit scope boundary, this repair
addresses only:

- the Stage 1 embedded-outcome interface-channel gap (§3.1)
- the canonical pointer tamper-evidence gap (§3.2)

It does not redesign AES, broaden the public API beyond what these two
findings require, change the two-stage lifecycle, change supersession
semantics, change the compound-key AER model, introduce implementation
details, or amend any predecessor contract. Every existing architectural
decision AESIC-001 v1.1 already froze is preserved (§13 below).

---

## 3. Primary-Source Reconstruction

Before drafting any repair, both findings were re-read directly from
their primary source — Phase 147L.2's own independent verification report
(`docs/verification/PHASE_147L2_AESIC_REPAIR_INDEPENDENT_VERIFICATION.md`
§3.1, §3.2) — and the specific AESIC-001 v1.1 requirements each finding
names were re-read directly from the frozen contract text, not merely
from Phase 147L.2's own restatement of them:

- **AESIC-REQ-118** (§8.6): requires the AER, "whenever a Stage 1
  evaluation... preceded," to embed a byte-for-byte copy of Stage 1's
  outcome, `evaluation_id`, and `evaluated_at`.
- **AESIC-REQ-007** (§5.2): freezes `evaluate_stage_1(*, session) ->
  AuthorityEvaluationOutcome` and `evaluate_stage_2(*, session, package_id)
  -> AuthorityEvaluationRecord` — no parameter through which the value
  AESIC-REQ-118 needs could travel.
- **AESIC-REQ-012** (§5.4): "AES SHALL accept no other input" beyond
  `registry`/`aer_store` (construction) and `session`/`package_id` (Stage
  2 call) — closes the parameter channel explicitly.
- **AESIC-REQ-060** (§8.9): "No AER, AER reference, Stage 1 outcome, or
  Stage 2 outcome SHALL ever be written back onto `Session`" — closes the
  `Session`-carried channel explicitly.
- **AESIC-REQ-017** (§5.8): "AES SHALL be stateless between invocations...
  no cross-invocation mutable state" — closes the AES-internal-retention
  channel explicitly.
- **AESIC-REQ-119 item 2** (§12.1): defines the canonical pointer's
  content as "at minimum: the canonical `evaluation_id`, `record_id`, and
  `record_digest`" with no digest of the pointer's own content and no
  read-time verification obligation.
- **AESIC-REQ-055** (§8.4): the existing digest precedent this repair
  extends to the pointer, already used identically for every other
  durable record family in this codebase.

**Independent confirmation of the gap.** Re-deriving §3.1 from these
primary texts alone (without re-reading Phase 147L.2's own disposition
first): `evaluate_stage_1` returns an `AuthorityEvaluationOutcome`
directly to its caller and nowhere else (AESIC-REQ-007); AES itself never
retains it (AESIC-REQ-017); `Session` may not carry it (AESIC-REQ-060);
and `evaluate_stage_2`'s own signature has no slot for it (AESIC-REQ-007/012).
For AESIC-REQ-118 to ever be satisfiable by a real caller, one of these
four requirements had to change. The authorizing prompt's own architectural
preservation demands (§11: AES sole orchestrator, Registry ownership,
evaluator purity, Stage 1 advisory semantics, non-gating guarantees, zero
execution capability) foreclose touching AESIC-REQ-017's statelessness or
AESIC-REQ-060's non-write-back rule without a materially larger change than
the finding warrants — leaving exactly one minimal-footprint option: add a
new, optional parameter to `evaluate_stage_2` (repairing AESIC-REQ-007/012),
which is also the disposition Phase 147L.2 §3.1's own candidate (a)
already identified.

Re-deriving §3.2 from these primary texts alone: AESIC-REQ-119 item 2's
pointer content has no digest of its own, and no requirement in §12 or
§13 obligates any read-time check of that content against anything else.
AESIC-REQ-055's own digest pattern already exists in this codebase for
exactly this class of problem (detect corruption of a persisted artifact's
content) — applying the same pattern to the pointer, plus a cross-check
against the AER it references, closes both failure variants Phase 147L.2
§3.2 constructed (bit-level pointer corruption, and a corrupted
`record_id` silently naming a different, still-valid AER).

---

## 4. Finding §3.1 Root Cause

**Where `stage_1_outcome_ref`'s content is created.** Inside AES, during
`evaluate_stage_1(session=s)` — AES resolves the Decision Template,
calls the unmodified `evaluate()`, and returns the resulting
`AuthorityEvaluationOutcome` to its caller (AESIC-REQ-011, §5.3).

**Who owns it.** AES computes it; the caller (§9.2 — the same
caller-side layer that already orchestrates the
interactive-workflow → publication-handoff → publication-execution
sequence, e.g. `interactive_workflow/application/{session_service,publication_service}.py`)
receives and, per AESIC-REQ-063/AESIC-REQ-064, may hold it only in its
own memory, never write it anywhere durable or onto `Session`.

**Where it resides before Stage 2.** Exactly one place: the caller's own
process memory, for exactly as long as that process runs and that caller
chooses to retain it. It is not durable, not in AES, not on `Session`, and
not in any store.

**How AES received it, before this repair.** It didn't — this was
precisely the gap. `evaluate_stage_2`'s v1.1 signature accepted no
parameter through which the caller could hand it back.

**How `evaluate_stage_2` receives or derives it, after this repair.** The
caller passes it back explicitly as `stage_1_result:
Optional[Stage1EvaluationResult]` (AESIC-REQ-007/122, §5.2.1) — the exact
object `evaluate_stage_1` returned, unmodified, never re-derived or
reconstructed by AES.

**What happens when Stage 1 did not occur in the current process.**
`stage_1_result` is `None` (AESIC-REQ-125) — not an error, and
structurally indistinguishable, from AES's own point of view, from "Stage
1 occurred but the caller chose not to supply its result." Both produce
an AER with `stage_1_outcome_ref` absent.

**What happens after restart.** Any in-memory `Stage1EvaluationResult` a
caller was holding is lost with the process (§11.2's existing "After
Stage 1, before Confirmation" row, unaffected by this repair) — the
caller simply supplies `stage_1_result=None` on resumption, exactly the
same as if Stage 1 had never run.

**What happens during replay.** A Stage 2 replay for an already-canonical
`package_id` (AESIC-REQ-023(a)) never re-invokes `evaluate_stage_1` and
never re-validates a `stage_1_result` — it returns the already-persisted,
canonical AER unchanged, `stage_1_outcome_ref` (if any) already fixed
inside that immutable artifact from the original Stage 2 attempt.

**Whether caller-supplied arbitrary Stage 1 material is permitted.**
No — AESIC-REQ-123's mandatory four-check sequence (structural validity,
session binding via `Session.session_id`, identity binding, decision-template
binding) refuses, via `Stage1HandoffInvalidError` (AESIC-REQ-124), any
`stage_1_result` that does not genuinely correspond to the concurrently-supplied
`session`. A caller cannot fabricate, borrow from another session, or
otherwise substitute Stage 1 material and have it silently accepted.

---

## 5. Finding §3.1 Repair

See AESIC-001 §5.2 (AESIC-REQ-007, repaired), §5.2.1 (AESIC-REQ-122–125,
128, new), §5.4 (AESIC-REQ-012, repaired), §5.7 (error-ownership addition),
§8.6 (AESIC-REQ-057, clarified), §9.1 (retention/absence note, new), and
§16 (AESIC-REQ-098, clarified) for the complete normative text. Summary:

- **`Stage1EvaluationResult`** (AESIC-REQ-122): a new, AESIC-001-owned,
  immutable value type carrying exactly `outcome`
  (the unmodified `AuthorityEvaluationOutcome`, AEMIC-001 §6, already
  carrying `evaluated_at` verbatim), `evaluation_id` (this Stage 1
  invocation's own, previously computed by AES but never actually
  surfaced to any caller through any channel — closed as a necessary
  byproduct), and `session_id` (verbatim copy of `session.session_id`,
  the binding field).
- **`evaluate_stage_1`'s return type** changes from bare
  `AuthorityEvaluationOutcome` to `Stage1EvaluationResult` (AESIC-REQ-007,
  repaired) — additive, not narrowing: every field the v1.1 return value
  carried is still present, at `.outcome`.
- **`evaluate_stage_2` gains one new, optional parameter**,
  `stage_1_result: Optional[Stage1EvaluationResult] = None` (AESIC-REQ-007/012,
  repaired) — every existing caller that never supplies it is unaffected
  (defaults to `None`, AESIC-REQ-125).
- **Mandatory validation** (AESIC-REQ-123) when non-`None`: structural
  validity, then session/identity/template binding, each checked against
  the concurrently-supplied `session`, refusing via
  `Stage1HandoffInvalidError` (AESIC-REQ-124, closed four-reason
  enumeration) on the first failing check, with zero side effects before
  or after the refusal.
- **Complete Stage 2 invocation contract** (AESIC-REQ-128): a table naming
  every input, its source, its derivation, and its validator — closing
  every implementer-discretion channel the authorizing prompt's §5
  explicitly named (extra ungoverned argument, arbitrary file load,
  ambient state, Registry-mediated resolution, incomplete-`Session`
  reconstruction).

---

## 6. Stage 2 Interface Model

Reproduced from AESIC-001 §5.2.1 (AESIC-REQ-128) — the authoritative
version is the contract's own table; this section restates it for
readability:

| Input | Direct? | Derived? | Governed-state load? | Validator |
|---|---|---|---|---|
| `session` | Yes | identity/template derived from it (AESIC-REQ-008) | No | AES, structurally |
| `package_id` | Yes | No | No | Keying logic (§12.1) |
| `registry`/`aer_store` | No (construction-time) | No | No | N/A |
| `stage_1_result` (optional) | Yes | No | No — no store exists | AES, via AESIC-REQ-123 |
| Decision Template | No | No | Yes, fresh every call | Resolution (§6.4) |
| `EligibleAuthorityDeclaration` | No | No | Yes, fresh every call | Registry (§7.5) |

Exactly one ownership and transport model is frozen: `stage_1_result` is
a same-process, same-call-chain, caller-retained, AES-validated parameter
— never a durable artifact, never a hidden channel, never resolved
through the Registry, never reconstructed from `Session`.

---

## 7. Stage 1 Absence and Invalidity Semantics

- **Absent** (`stage_1_result=None`, AESIC-REQ-125): always valid, never an
  error, `stage_1_outcome_ref` absent from the resulting AER. This is the
  behavior of every caller that predates this repair, unchanged.
- **Malformed** (structurally invalid non-`None` value, AESIC-REQ-123
  check 1): refused, `Stage1HandoffInvalidError(reason=MALFORMED)`.
- **Cross-session** (`stage_1_result.session_id != session.session_id`,
  check 2): refused, `reason=SESSION_MISMATCH`.
- **Cross-identity** (`stage_1_result.outcome.claimed_identity !=
  session.owner_identity`, check 3): refused, `reason=IDENTITY_MISMATCH`.
- **Cross-template** (`stage_1_result.outcome.template_ref`/`template_version`
  mismatch, check 4): refused, `reason=TEMPLATE_MISMATCH`.
- **Stale but otherwise valid** (old `outcome.evaluated_at`, all four
  checks pass): **accepted**, embedded verbatim — staleness is a
  disclosed, expected property of Stage 1 (AESIC-REQ-065, unchanged), not
  a validation failure. Provenance and freshness are deliberately
  independent axes.

`None` and an invalid non-`None` value are always structurally
distinguishable at the API level (Python's own type system distinguishes
`None` from any object failing AESIC-REQ-123's checks) — Phase 147L.2's
own adversarial scenario "Stage 2 cannot distinguish absent from corrupted
Stage 1" cannot arise under this design.

---

## 8. Finding §3.2 Root Cause

**What the pointer identifies.** The currently-canonical compound-keyed
AER for a given `package_id` — at minimum its `evaluation_id`, `record_id`,
and `record_digest` (AESIC-REQ-119 item 2, v1.1).

**Whether it is itself persistent state.** Yes — a small, separately
persisted, mutable artifact, atomically replaced on every canonical
update (AESIC-REQ-119 item 2, unchanged by this repair).

**How it binds to the selected AER.** By value only, in v1.1: the
pointer's own `record_id`/`record_digest` fields name the canonical AER,
with no mechanism verifying that naming is itself intact.

**What corruption or substitution attacks remain possible (pre-repair).**
Two, independently constructed by Phase 147L.2 §3.2: (a) the pointer's
`record_digest` field alone is corrupted, no longer matching the AER it
still correctly names by `record_id`; (b) the pointer's `record_id` field
is corrupted to name a *different*, still-valid, but superseded (or
otherwise wrong) AER for the same `package_id` — this second variant
produces no digest mismatch at all, because the wrongly-named AER's own
self-carried digest still matches itself.

**How replay detects mismatch.** Before this repair: not at all, for
variant (b) — nothing re-verifies the pointer's own claim against
anything independent of the pointer.

**Who owns validation.** Before this repair: no one — no requirement
assigns pointer-content validation to any component.

**Whether the pointer may be rebuilt deterministically.** Partially: the
primary store retains every AER ever produced for a `package_id`
indefinitely (AESIC-REQ-119 item 1, unaffected), so the *data* needed to
rebuild a pointer always survives a pointer-level corruption. But *which*
surviving entry is the correct canonical one is not, in general,
mechanically re-derivable from the primary store alone without additional
ordering metadata the corrupted pointer itself was the only record of —
so full automatic reconstruction is not asserted as a completeness
guarantee; detection and disclosed, operator-directed recovery is.

---

## 9. Finding §3.2 Repair

See AESIC-001 §12.1 (AESIC-REQ-119 item 2, repaired; AESIC-REQ-126, new)
and §13 (failure-ownership row, new, AESIC-REQ-127) for the complete
normative text. Summary:

- **Pointer content** gains one field: `pointer_digest`, computed via the
  same `compute_record_digest` function every other durable record in
  this codebase already uses (AESIC-REQ-055), over the pointer's own
  other four fields (`package_id`, `evaluation_id`, `record_id`,
  `record_digest`). AES owns computing and attaching it at every pointer
  write (mirrors AESIC-REQ-083's digest-ownership discipline).
- **Mandatory read-time verification** (AESIC-REQ-126 item 2), performed
  before any consumer may treat a pointer as canonical: (a) recompute
  `pointer_digest` over the pointer's own other fields and compare —
  catches bit-level pointer corruption (closes variant (a) above); (b)
  retrieve the AER the pointer names and compare *that AER's own
  self-carried `record_digest`* against the pointer's copy of it — catches
  a corrupted `record_id`/`record_digest` pair naming a different, valid
  AER (closes variant (b) above, the more severe case, because a
  different valid AER's own digest will not equal what an untouched
  pointer would have recorded for the AER it originally, correctly,
  named).
- **Fail-closed on mismatch:** either check failing raises
  `CanonicalPointerCorruptError` (AESIC-REQ-127); no consumer is permitted
  to treat the mismatched content as canonical.
- **Recovery is operator-owned** (AESIC-REQ-126 item 4), mirroring the
  existing "Digest mismatch" row's own disposition (§13) — not an
  automatic AES-internal repair, since automatic selection among multiple
  surviving compound-keyed entries is not a fact AES can determine
  unassisted. An implementation MAY offer an operator-invoked,
  deterministic rebuild-from-primary-store operation as a convenience;
  none is mandated.

---

## 10. Pointer Integrity and Recovery Model

- **Canonical pointer content:** `{package_id, evaluation_id, record_id,
  record_digest, pointer_digest}`.
- **Integrity field:** `pointer_digest`, `compute_record_digest` over the
  other four fields (AESIC-REQ-126 item 1).
- **Validation before use:** mandatory, two-step, at every canonical
  `package_id` lookup (AESIC-REQ-126 item 2).
- **Behavior on mismatch:** `CanonicalPointerCorruptError` (AESIC-REQ-127),
  fail-closed — no canonical result returned.
- **Repair/recovery ownership:** operator-owned; AES MAY offer a
  convenience rebuild operation, never automatic (AESIC-REQ-126 item 4).
- **Replay behavior:** a replayed lookup performs the identical
  verification every time — no cached "already verified" shortcut is
  introduced, consistent with AES's own statelessness (AESIC-REQ-017,
  unaffected).
- **Concurrency behavior:** unchanged from v1.1's last-write-wins model
  (AESIC-REQ-120) — `pointer_digest` is computed fresh by whichever
  atomic-replace write completes last, so it is always internally
  consistent with the content it accompanies at write time; concurrency
  affects *which* write wins, never whether the winning write's own digest
  is self-consistent.
- **Atomicity:** unchanged — the pointer's write already uses the
  temp-file + fsync + `os.replace` idiom (AESIC-REQ-119 item 2,
  AESIC-REQ-086); adding `pointer_digest` as one more field in that same
  atomic write introduces no new atomicity requirement.
- **Relationship to immutable AER history:** the primary, compound-keyed
  store (AESIC-REQ-119 item 1) is entirely unaffected — every AER,
  superseded or canonical, remains durable and independently retrievable
  regardless of the pointer's own state, so a corrupted pointer never
  loses data, only temporarily loses convenient canonical lookup for that
  `package_id`.

---

## 11. Requirement Changes

**Text-only repairs (identity preserved):** AESIC-REQ-007, AESIC-REQ-010,
AESIC-REQ-012, AESIC-REQ-057, AESIC-REQ-076 (three new restart-matrix
rows), AESIC-REQ-098 (clarifying note), AESIC-REQ-102, AESIC-REQ-119
(item 2 gains `pointer_digest`).

**New requirements:** AESIC-REQ-122, AESIC-REQ-123, AESIC-REQ-124,
AESIC-REQ-125, AESIC-REQ-126, AESIC-REQ-127, AESIC-REQ-128 (contract §21's
Requirement/Test Matrix records all seven with falsifiability anchors).

**Table-only additions under an existing, unrenumbered requirement**
(mirrors the Phase 147L.1 precedent of adding restart-matrix rows without
a new requirement number): two new rows in §13's Failure Ownership matrix
(under AESIC-REQ-087: `Stage1HandoffInvalidError`, `CanonicalPointerCorruptError`)
and two new rows in §15's security mitigation table (under AESIC-REQ-092:
Stage 1 fabrication/substitution, canonical pointer tampering).

Every AESIC-REQ audited against the authorizing prompt's §9 list
(AESIC-REQ-007, 012, 017, 019, 023, 053, 056, 057, 060, 064, 078, 080, 081,
098, 102, 118, 119, 120, 121) was individually re-checked: only
AESIC-REQ-007, 012, 057, 098, 102, and 119 required a text change; the
remainder (017, 019, 023, 053, 056, 060, 064, 078, 080, 081, 118, 120,
121) were confirmed unaffected in substance — each was re-read and found
to already be compatible with, or entirely orthogonal to, this repair's
two new mechanisms. No requirement was deleted. No requirement's number
was reused or reassigned.

---

## 12. Adversarial Analysis

Each scenario the authorizing prompt's §13 names, attempted fresh against
the repaired contract:

1. **Caller substitutes a fabricated Stage 1 outcome.** Refused —
   AESIC-REQ-123 check 2/3/4 requires the supplied `stage_1_result`'s
   `session_id`/`claimed_identity`/`template_ref`/`template_version` to
   match the concurrently-supplied `session`'s own values; a fabricated
   outcome constructed without a genuine, matching `evaluate_stage_1`
   call would need to forge all four simultaneously, and even a
   successful forgery of the *content* fields still could not forge
   `session_id` matching an unrelated `session` object's own value
   without already controlling that `session` object itself (in which
   case the "substitution" is not meaningfully distinct from a
   legitimately-obtained result for that same session).
2. **Stage 1 outcome belongs to another Session.** Refused —
   AESIC-REQ-123 check 2 (`SESSION_MISMATCH`), the check purpose-built for
   this exact scenario using `Session.session_id`, a field distinct from
   identity/template and therefore not collapsible into checks 3/4.
3. **Stage 1 outcome belongs to another identity.** Refused —
   AESIC-REQ-123 check 3 (`IDENTITY_MISMATCH`).
4. **Stage 1 outcome belongs to another Decision Template.** Refused —
   AESIC-REQ-123 check 4 (`TEMPLATE_MISMATCH`).
5. **Stage 1 content is stale.** **Accepted**, embedded verbatim — see §7
   above; staleness is not a validation axis (AESIC-REQ-065, unchanged).
6. **Stage 1 content is malformed.** Refused — AESIC-REQ-123 check 1
   (`MALFORMED`).
7. **Restart loses the Stage 1 channel.** Handled, not an error — caller
   supplies `stage_1_result=None` on resumption (AESIC-REQ-125, §11.2 new
   row).
8. **Stage 2 cannot distinguish absent from corrupted Stage 1.** Cannot
   arise — `None` and a structurally-invalid non-`None` object are always
   distinguishable at the API level (§7 above).
9. **Canonical pointer selects an AER with the wrong digest.** Detected —
   AESIC-REQ-126 item 2 step (b) compares the pointer's copy of
   `record_digest` against the referenced AER's own self-carried digest;
   any mismatch raises `CanonicalPointerCorruptError`.
10. **Pointer rollback selects an older superseded AER.** If the pointer's
    content is internally consistent (its `pointer_digest` matches, and
    its `record_digest` matches the AER it names), this is not corruption
    detectable by AESIC-REQ-126 alone — it is a question of *which write
    won* under concurrency, governed by AESIC-REQ-120's disclosed
    last-write-wins semantics, unchanged by this repair; if instead the
    rollback was produced by an out-of-band edit of the pointer file
    (not a legitimate concurrent write), AESIC-REQ-126 item 2 step (a)
    (pointer_digest recomputation) detects it whenever that edit did not
    also correctly recompute `pointer_digest` — the residual case of a
    fully-consistent forged pointer is explicitly out of this mechanism's
    threat model (§10 above item 3, mirroring AESIC-REQ-055's own scope).
11. **Pointer corruption survives replay.** Does not survive undetected —
    every canonical-`package_id` lookup re-performs AESIC-REQ-126's
    read-time verification; there is no cached "already verified"
    shortcut (AES's own statelessness, AESIC-REQ-017, unaffected).
12. **Concurrent supersession produces multiple current-effective
    pointers.** Cannot occur by construction — the pointer is a single,
    atomically-replaced artifact per `package_id` (AESIC-REQ-119 item 2);
    concurrent writers race to replace the same single artifact, and
    exactly one atomic replace is the last to complete (AESIC-REQ-120,
    unchanged) — there is never more than one pointer file per
    `package_id` to disagree with itself.
13. **Pointer repair mutates immutable AER history.** Forbidden and
    unnecessary — AESIC-REQ-126 item 4's own recovery model operates
    entirely on the pointer artifact; the compound-keyed primary store
    (AESIC-REQ-119 item 1, "no entry... is ever updated or deleted") is
    never written to by any pointer-recovery operation, only read from.

The contract provides a deterministic result for every scenario above.

---

## 13. Architectural Preservation

Independently re-checked against AESIC-001 v1.2's current text (see
contract §29.5 for the complete, requirement-by-requirement enumeration;
summarized here):

| Invariant | Status |
|---|---|
| AES sole lifecycle orchestrator | Preserved — AESIC-REQ-005/006 (§5.1) untouched |
| Decision Template Resolution ownership | Preserved — §6 entirely untouched |
| Registry ownership | Preserved — §7 entirely untouched |
| Evaluator purity/determinism/Registry exclusion | Preserved — `evaluate()` never named as an actor in any repaired/new requirement |
| Publication Coordinator publication-only ownership | Preserved — §14 entirely untouched |
| Disclosure-only semantics | Preserved — §14 entirely untouched |
| Non-gating guarantees | Preserved — AESIC-REQ-090/091 untouched |
| Stage 1 advisory semantics | Preserved — AESIC-REQ-062–065 unchanged in substance |
| Stage 2 unconditional supersession | Preserved — AESIC-REQ-070/071 byte-for-byte unchanged |
| Immutable AER history | Preserved — AESIC-REQ-054/082/119 item 1 unchanged in substance; `pointer_digest` is metadata about the pointer, not the AER |
| Two-tier compound-key model | Preserved — item 1 untouched; item 2 gains one field and one read-time check |
| Replay observational equivalence | Preserved — AESIC-REQ-075/077 unchanged; new restart-matrix rows describe newly-named restart points only |
| Zero execution capability | Preserved — contract text only; AESIC-001 §30 (Phase 147L.3 No-Go Boundary Confirmation) confirms |

Falsification attempted (contract §29.5): could AESIC-REQ-123's
validation logic be read as implicitly requiring AES to gain a new
Stage-1-outcome persistence capability, reopening Phase 147L's original
Finding 1 or AESIC-REQ-064/078/080's "exactly one artifact type" framing?
Checked directly: all four checks compare fields already in AES's hands
for this one call (the supplied `stage_1_result`, the concurrently-supplied
`session`) — no lookup against any store, no Stage-1 persistence of any
kind. No widening found.

---

## 14. Cross-Contract Compatibility

Reconfirmed by direct citation-checking against each predecessor
contract's own frozen text, not by trusting this repair's own claims:

| Contract | New citation this repair introduces | Independently reconfirmed |
|---|---|---|
| AEM-001 v1.0 | None | Untouched — §7 not touched by this repair |
| AEMIC-001 v1.2 | `AuthorityEvaluationOutcome`'s own shape (AEMIC-REQ-021), already cited unmodified — `Stage1EvaluationResult.outcome` is exactly this type, never a modification of it | Unmodified — `Stage1EvaluationResult` is a new AESIC-001-owned wrapper type, not an AEMIC-001 type; AEMIC-001 §6 is not amended |
| IWC-001 v1.2 | `Session.session_id` (new citation, AESIC-REQ-122) | Already a frozen, already-populated field — IWC-001 §26.1 independently confirms `PublicationHandoff.build_package` already receives the full `Session` object with this field populated, for an unrelated purpose (Coordinator record construction). This repair adds a new *reader* of an existing field, not a new field, method, or obligation on IWC-001 |
| IWPC-001 v1.4 | None new (AESIC-REQ-120's existing IWPC-REQ-144/147 citation is unaffected) | Unmodified — this repair does not touch AESIC-REQ-120's own text |
| PEC-001 v1.1 | None | Untouched — §14's consumer table unaffected |
| CHGR-001 v1.3 | None | Untouched — no repair requirement touches CHGR construction |

**No amendment to any of the six predecessor contracts is required** —
independently reconfirmed, matching AESIC-REQ-113's own claim (unaffected
in substance by this repair, per AESIC-001 §29.6) and Phase 147L.1's/147L.2's
own prior compatibility assessments, now re-confirmed unchanged across a
third revision.

---

## 15. Validation

```
pcae check                        -> passed
pcae health                       -> healthy
pcae doctor task-memory           -> clean
pcae runtime inspect              -> Observed / observe / unavailable (unchanged)
pcae push check                   -> clean / nothing_to_push (prior to this phase's own commit)
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
changes. Only AESIC-001 itself, this verification document, and ordinary
task/phase bookkeeping files changed throughout this phase, confirmed by
`git status --short` at finalization.

---

## 16. Overall Verdict

**AESIC-001 v1.2 REPAIRED.**

- The Stage 1 interface channel is complete and unambiguous
  (AESIC-REQ-122/123/128) — §5/§6/§7 above.
- The Stage 1 channel preserves closed-interface hardening —
  AESIC-REQ-008 is untouched; no bare identity/template string parameter
  is introduced; `stage_1_result` carries only an already-computed,
  AES-validated outcome object (§13 above).
- Absent and invalid Stage 1 semantics are defined and always
  distinguishable (AESIC-REQ-125, §7 above).
- The canonical pointer is tamper-evident (AESIC-REQ-126/127) — §9/§10
  above.
- Replay and concurrency semantics remain coherent — §10, §12 (items
  10–12) above.
- No new contradiction is introduced — §11's requirement-by-requirement
  audit, §13's architectural-preservation table.
- All architectural invariants remain preserved — §13 above.
- No predecessor-contract amendment is required — §14 above.

---

## 17. Recommended Next Phase

**147L.4 — AESIC-001 Final Contract Repair Independent Verification.**
That phase shall independently verify AESIC-001 v1.2 against the two
findings from Phase 147L.2 (§3.1, §3.2 of that report), re-read the
complete repaired contract in full, and perform fresh interface, replay,
persistence, pointer-integrity, concurrency, and cross-contract attacks.
It shall remain verification-only and make no contract or implementation
change. Only after successful 147L.4 verification should the project
proceed to 147M — Authority Evaluation Integration Implementation.

**This recommendation is not an authorization.**

---

**End of Phase 147L.3 Contract Repair.**
