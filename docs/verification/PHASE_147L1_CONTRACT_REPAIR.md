# Phase 147L.1 — AESIC-001 Contract Repair

**Phase ID:** 147L.1
**Mode:** Contract Repair (bounded — no implementation, no schema change,
no runtime change, no production source change)
**Baseline:** AESIC-001 v1.0 (`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`)
**Result:** AESIC-001 v1.1 (same file, in-place minor revision)
**Date:** 2026-07-31

---

## Authorization

Phases 147G–147L are complete. Phase 147L independently verified AESIC-001
v1.0 and reached the verdict **AESIC-001 VERIFIED WITH NON-BLOCKING
FINDINGS**: two Major, internally-inconsistent findings (Finding 1, Finding
2), one Minor finding (Finding 3), and one Informational finding
(Finding 4). This phase is authorized, per the governing prompt reproduced
above the Authorization heading of this task, to perform a strictly
bounded contract repair of AESIC-001 resolving Findings 1 and 2 (with
Findings 3 and 4 resolved only insofar as they are inseparable byproducts
of repairing 1 and 2). No implementation, schema, or runtime change is
authorized or was made.

### Bootstrap

```
pcae session bootstrap --agent-id claude-local --sync-lock
  -> healthy; agent lock held by claude-local; latest completed phase 147L;
     readiness "blocked" only because the post-147L idle placeholder task
     was still active, not because of any repository defect
pcae check              -> passed
pcae health              -> healthy; all required files present; policy valid; git clean
pcae doctor task-memory  -> clean, no inconsistencies
pcae runtime inspect     -> Runtime state Observed; Execution capability unavailable;
                            Registry status empty; Plugin count 0; Governance posture
                            non-executing (unchanged from 147L)
pcae push check          -> nothing_to_push, health healthy, check passed
```

Confirmed: repository clean; 0 unpushed commits; no other active governed
phase; runtime unchanged (Observed / observe / unavailable); latest
completed phase 147L, matching `PROJECT_STATUS.md`'s own "## Current
Phase" section, treated as authoritative background.

---

## 1. Scope

This repair is narrowly scoped to the two Major findings Phase 147L
identified by direct textual analysis of AESIC-001 against itself:

1. **Finding 1** (§8.6 vs. §9.1/§12.2) — `stage_1_outcome_ref`
   (AESIC-REQ-057) is defined to make "both outcomes retrievable," while
   AESIC-REQ-064/080 unconditionally guarantee Stage 1's outcome is never
   persisted anywhere a later reader could retrieve it from.
2. **Finding 2** (§5.11/§11.2 vs. §12.1) — Stage 2's idempotency mechanism
   (AESIC-REQ-019, an exclusive-create, one-record-per-`package_id` store)
   structurally cannot accommodate §11.2's own restart-matrix rows
   requiring a changed-input retry to produce a new, disclosed record
   under the same key.

Finding 3 (Minor — undefined "inputs unchanged" equality procedure) and
Finding 4 (Informational — `evaluation_id`/`stage_1_outcome_ref`
relationship unstated) are resolved as unavoidable byproducts: Finding 2's
own repair cannot state an unambiguous supersession-vs-no-op decision
procedure without defining the equality check that makes the decision
(closing Finding 3), and Finding 1's own repair cannot define the embedded
copy's content without stating whether it carries its own `evaluation_id`
(closing Finding 4). Neither is independently motivated scope expansion.

No architectural redesign was performed. No requirement was renumbered,
reassigned, or reused. No feature was added beyond what eliminating the
two contradictions strictly required.

---

## 2. Findings (as received from Phase 147L)

Reproduced verbatim in substance from
`docs/verification/PHASE_147L_AUTHORITY_EVALUATION_INTEGRATION_CONTRACT_INDEPENDENT_VERIFICATION.md`
§14:

### Finding 1 — [Major] `stage_1_outcome_ref` cannot deliver "both outcomes retrievable"

AESIC-REQ-057 requires the AER to carry `stage_1_outcome_ref` "so that a
disagreement between the two is structurally visible (both outcomes
retrievable, never one silently discarded)." AESIC-REQ-064/080
independently and unconditionally guarantee every Stage 1 outcome remains
transient and is never persisted anywhere. A "reference" required to make
a value "retrievable," paired with an unconditional guarantee that the
referenced value is never durably stored anywhere a later reader could
retrieve it from, is a direct internal contradiction: as literally
specified, `stage_1_outcome_ref` cannot be dereferenced to anything.

### Finding 2 — [Major] Stage 2 idempotency's "supersede" branch is unsatisfiable

AESIC-REQ-023 requires a second Stage 2 attempt with changed inputs to be
"refused or superseded." AESIC-REQ-019 requires the AER write to use an
`O_CREAT | O_EXCL` exclusive-create pattern. AESIC-REQ-053/078 key the AER
by `package_id` alone. §11.2's own restart-matrix rows ("Registry
evolution," "Decision Template evolution") require a changed-input retry
to produce "a genuinely different, freshly-computed outcome" as a new,
disclosed record. An exclusive-create store keyed by `package_id` alone
can only fail (EEXIST) or return the existing record on a second attempt
— it cannot write a second, distinct record under the same key without
either violating immutability (AESIC-REQ-054/082) or requiring a
different key that AESIC-REQ-053/078 do not define.

### Finding 3 — [Minor] Undefined "inputs unchanged" equality procedure

AESIC-REQ-023(a)/081 require detecting whether repeated inputs are
"unchanged" but no section defines the comparison procedure, and
AESIC-REQ-102's performance budget omits the AER-store read this
comparison requires.

### Finding 4 — [Informational] `evaluation_id`/`stage_1_outcome_ref` relationship unstated

`evaluation_id` (AESIC-REQ-098) is well-defined as distinct from
`package_id`/`record_id`, but its relationship to `stage_1_outcome_ref`
(AESIC-REQ-057) — is `stage_1_outcome_ref` itself an `evaluation_id`, or a
distinct value? — was never stated.

---

## 3. Root Cause Analysis

**Finding 1's root cause:** AESIC-001 v1.0's own naming discipline used
the `_ref` suffix uniformly for every reference-shaped field in the
contract (`authority_evaluation_ref`, `declaration_ref`). Every other
`_ref` field in v1.0 genuinely is a pointer to separately-durable state.
`stage_1_outcome_ref` was drafted by the same naming convention without
noticing that, unlike every other `_ref` field, the thing it would need
to point to (a persisted Stage 1 outcome) is exactly the thing a different,
unconditional requirement (AESIC-REQ-064/080) forbids from ever existing.
The contradiction is therefore not a reasoning error about *what* §8.6
wants (structural disagreement-visibility between Stage 1 and Stage 2 is a
sound, independently-motivated goal, confirmed sound by Phase 147L §2's
independent reconstruction) but a naming/shape error about *how* to
deliver it: a dereferenceable pointer is the wrong mechanism when the
referent is contractually forbidden to be durable.

**Finding 2's root cause:** AESIC-REQ-019's `O_CREAT | O_EXCL` pattern was
directly borrowed from `PublicationRecordStore.commit_publication`
(`storage.py:8-16`) — a precedent that is correct for Publication, where
duplicate-publication prevention is the *entire point* (a `package_id` may
publish at most once, ever). Stage 2 evaluation is a different problem
with superficially similar shape: it also wants "detect a duplicate
attempt for the same `package_id`," but unlike Publication, a Stage 2
retry *can* legitimately need to produce a new outcome (Registry/template
evolution). Borrowing Publication's own single-key exclusive-create
pattern silently imported Publication's own "at most once, ever" semantics
into a component whose own restart matrix (§11.2, drafted independently
and, per Phase 147L §2's reconstruction, correctly) already required a
different, richer semantics — "idempotent for unchanged inputs, but able
to produce a new record for changed inputs." The two halves of AESIC-001
v1.0 (§5.9's borrowed persistence mechanism, §11.2's own restart-matrix
requirement) were each independently reasonable but were never checked
against each other at freeze time.

---

## 4. Repair Strategy

**Finding 1:** Redefine `stage_1_outcome_ref`'s content, not its name or
its mandatory-when-present cardinality. It becomes an inline, embedded,
byte-for-byte copy of Stage 1's own outcome (plus its own `evaluation_id`
and timestamp), written directly into the AER's own document body — never
a pointer to anything durable outside the AER. AESIC-REQ-064/080 are
clarified (not weakened) to state explicitly that "never persisted" has
always meant "never persisted as its own, independently-addressable
artifact," a reading fully consistent with both requirements' original
text and with Phase 147L's own Finding 1 disposition, which named exactly
this repair as the most direct resolution (§14.1 of the 147L report).

**Finding 2:** Introduce a two-tier storage model — a compound
`(package_id, evaluation_id)` key for the actual, immutable, write-once
AER store (collision-free by construction, since AESIC-REQ-098 already
guarantees per-invocation `evaluation_id` uniqueness), plus a separate,
small, atomically-updated `package_id`-keyed canonical pointer index for
ordinary lookup. AESIC-REQ-023 is repaired to state the complete decision
procedure (recompute, compare via a new equality procedure, then either
no-op or persist-and-advance-pointer). This is exactly the repair
Phase 147L's own Finding 2 disposition (§14.2/§8 of the 147L report)
identified as the resolution. The equality procedure this decision
requires (AESIC-REQ-121) closes Finding 3 as a byproduct; the embedded
copy's `evaluation_id` clause (part of AESIC-REQ-118) closes Finding 4 as
a byproduct.

Both repairs are additive and in-place: no requirement was deleted, no
requirement number was reused, and every requirement not touched by these
two repairs is unchanged, byte-for-byte, from v1.0.

---

## 5. Requirement Changes

| Requirement | Change type | Reason |
|---|---|---|
| AESIC-REQ-019 (§5.9) | Text repaired | Compound-key exclusive-create, not `package_id`-alone (Finding 2) |
| AESIC-REQ-023 (§5.11) | Text repaired | States full recompute→compare→(no-op\|supersede) decision procedure (Finding 2) |
| AESIC-REQ-053 (§8.2) | Text repaired | Two-tier keying (storage key vs. canonical lookup key) (Finding 2) |
| AESIC-REQ-056 (§8.5) | Text repaired | Content-shape cross-reference to repaired §8.6 (Finding 1) |
| AESIC-REQ-057 (§8.6) | Text repaired | Mandatory/optional cardinality unchanged; retrieval mechanism redefined (Finding 1) |
| AESIC-REQ-064 (§9.1) | Text clarified | "Never persisted" scoped to "as its own artifact" (Finding 1) |
| AESIC-REQ-078 (§12.1) | Text repaired | Storage/lookup key distinction stated (Finding 2) |
| AESIC-REQ-080 (§12.2) | Text clarified | Same scoping as AESIC-REQ-064 (Finding 1) |
| AESIC-REQ-081 (§12.3) | Text repaired | References the new equality procedure (Finding 2/3) |
| AESIC-REQ-098 (§16) | Text extended | States the `evaluation_id`/`stage_1_outcome_ref` relationship (Finding 4) |
| AESIC-REQ-102 (§17) | Text repaired | Performance budget includes the AER-store comparison read (Finding 3) |
| §11.2 restart-matrix rows ("Registry evolution", "Decision Template evolution") | Cross-reference added | Cites the now-satisfiable mechanism (Finding 2) |
| **AESIC-REQ-118** (§8.6) | **New** | Defines the embedded-copy shape and content (Finding 1, 4) |
| **AESIC-REQ-119** (§12.1) | **New** | Defines the two-tier storage model (Finding 2) |
| **AESIC-REQ-120** (§12.1) | **New** | Defines canonical-pointer concurrency semantics (Finding 2) |
| **AESIC-REQ-121** (§12.1) | **New** | Defines the equality procedure (Finding 2, 3) |

**Total:** 11 existing requirements repaired/clarified in place (identity
preserved), 2 restart-matrix rows given an added cross-reference (no
normative change), 4 new requirements added (AESIC-REQ-118–121). 106 of
117 v1.0 requirements are untouched, byte-for-byte. Requirement count:
117 → 121.

---

## 6. Compatibility Assessment

This repair cites no provision of AEM-001, IWC-001, PEC-001, or CHGR-001
beyond what v1.0 already cited. It re-cites two already-frozen provisions
without altering their meaning:

- **AEMIC-001** (`evaluate()`'s purity/determinism, AEMIC-REQ-074/075/076)
  — cited identically to v1.0's own citation; the repair never asks
  `evaluate()` to change, be called differently, or accept a new
  parameter. The equality procedure (AESIC-REQ-121) compares
  `evaluate()`'s already-produced output field-by-field; it does not
  re-derive or reinterpret what `evaluate()` computes.
- **IWPC-001** (IWPC-REQ-144/147's "not authority-relevant,
  last-write-wins" pre-commit-point precedent) — already cited by Phase
  147L §2.10 to justify Stage 2's own existence; this repair additionally
  cites the same provision (AESIC-REQ-120) to justify the canonical
  pointer's own concurrency semantics, an extension of the same already-
  accepted principle to a new, structurally analogous situation (both are
  "before the one true commit point" state), not a new claim about
  IWPC-001 itself.

**Zero amendments to AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or
CHGR-001 are required** — independently re-confirmed by this repair, the
same "zero" AESIC-REQ-113 already claimed at v1.0. This repair's own edits
are entirely internal to AESIC-001's own text: one optional AER field's
content definition (§8.6), AES's own internal persistence mechanics
(§12.1), and one performance-budget line item (§17). None of these
surfaces is visible to, or governed by, any of the six predecessor
contracts.

---

## 7. Architectural Preservation

Every invariant the governing prompt (§6) named is confirmed preserved,
each independently checked against the repaired text, not merely asserted:

| Invariant | Status | Basis |
|---|---|---|
| Authority Evaluation Service ownership | **Unchanged** | AESIC-REQ-005/006 (§5.1) untouched; repair is internal to AES's own persistence mechanics (§12.1), never its ownership boundary |
| Registry ownership | **Unchanged** | §7 (AESIC-REQ-040–050) — zero requirements in this section touched |
| Evaluator purity | **Unchanged** | `evaluate()` is never mentioned by any repaired or new requirement; AESIC-REQ-121's equality check operates on `evaluate()`'s own already-produced output only |
| Disclosure-only semantics | **Unchanged** | §14 (AESIC-REQ-089–091) untouched; every consumer already consumed the AER only by reference (AESIC-REQ-061, unchanged) — the canonical pointer's read-indirection (AESIC-REQ-119 item 2) is transparent to every named consumer |
| Replay architecture | **Unchanged in framing, satisfiable in mechanism** | AESIC-REQ-075/077 untouched; only two restart-matrix rows gained a citation to the mechanism that makes their own pre-existing text achievable |
| Persistence architecture | **Unchanged in artifact-type count** | AESIC-REQ-078's "exactly one artifact type" preserved — the canonical pointer index is storage-location infrastructure, not a second governed artifact type; it carries no `AuthorityEvaluationOutcome`, no `citation_text`, and is never referenced by Readiness/Publication/CHGR |
| Authority Evaluation Record architecture | **Unchanged except one optional field's content, one keying clause** | AESIC-REQ-051/052/054/055/058/059/060/061 (identity, immutability, digest, CHGR relationship, Readiness relationship, Session relationship, reference-only consumption) all untouched |
| Lifecycle architecture | **Unchanged** | §9 (AESIC-REQ-062–073) — zero requirements touched |
| Stage 2 supersession principle | **Unchanged in intent, now mechanically achievable** | AESIC-REQ-070/071 (unconditional citation-purpose supersession) untouched; this repair only makes AESIC-REQ-023(b)'s own pre-existing supersession claim satisfiable |

No invariant was weakened. No invariant required a new exception. No
component gained a new responsibility beyond AES's own already-owned
persistence mechanics (§5.3 item 4, §12, unchanged in scope, only in
internal mechanism).

---

## 8. Final Verification

Self-check performed before declaring this repair complete, mirroring
Phase 147L's own adversarial-verification discipline:

1. **Does Finding 1 recur?** Re-reading repaired AESIC-REQ-057/118 against
   AESIC-REQ-064/080 (repaired): "both outcomes retrievable" is now
   satisfied by a copy embedded in an artifact that *does* durably exist
   (the AER); "never persisted" is now explicitly scoped to "as its own
   artifact," a scope the embedded copy never violates (it has no
   `record_id`, no `record_digest`, no store entry of its own). No
   contradiction found.
2. **Does Finding 2 recur?** Re-reading repaired AESIC-REQ-019/023/053/078
   together: the exclusive-create guard now operates on a compound key
   guaranteed collision-free by AESIC-REQ-098; the "refused or superseded"
   branch is now backed by a storage model (AESIC-REQ-119) that can
   actually write a second, distinct, immutable record without violating
   AESIC-REQ-054/082. No contradiction found.
3. **Does the repair introduce a new contradiction?** Checked AESIC-REQ-119
   (two-tier model) against AESIC-REQ-078's "exactly one artifact type"
   — resolved explicitly in §12.1's own text (the pointer is not a second
   *type* in AESIC-REQ-078's sense). Checked AESIC-REQ-120 (last-write-wins
   pointer) against AESIC-REQ-104's "idempotency guarantees SHALL hold
   under concurrent duplicate Stage 2 attempts" — consistent: idempotency
   for *unchanged*-input concurrent attempts still holds (both compute the
   same content, both find themselves "unchanged" relative to whichever AER
   the pointer resolves to, neither writes a fresh AER), and the disclosed
   last-write-wins semantics applies only to which of several
   already-durable, already-correct AERs is *canonical* — not to whether
   any data is lost or corrupted. No new contradiction found.
4. **Does the repair touch anything outside its declared scope?** Cross-
   checked the full requirement change list (§5 above) against the
   No-Go Boundary (§6 of the governing prompt, restated at AESIC-001 §26):
   every change is textual, inside AESIC-001 itself, and traces directly
   to Finding 1 or Finding 2. No unrelated requirement was touched.

No implementation, schema, or runtime change was made — confirmed by
`git status --short` at finalization (documentation and bookkeeping files
only).

---

## 9. Verdict

**AESIC-001 v1.1 REPAIRED.**

Both Major findings (Finding 1, Finding 2) are fully resolved. Architectural
intent is preserved (§7). Zero new ambiguities were introduced (§8). Zero
cross-contract amendments are required (§6). The Minor and Informational
findings (3, 4) are resolved as byproducts, not left open and not
independently expanded beyond what Findings 1–2's own repair required.

---

## 10. Recommended Next Phase

**147L.2 — AESIC-001 Contract Repair Independent Verification.** This
phase shall independently verify that the repairs introduced in AESIC-001
v1.1 (this document; `docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`
§25) resolve the two Major findings identified in Phase 147L without
altering the architecture or introducing new inconsistencies. It shall
remain verification-only and make no implementation changes. Only after
successful independent verification should the project proceed to
147M — Authority Evaluation Integration Implementation.

**This recommendation is not an authorization.**

---

**End of Phase 147L.1 Contract Repair.**
