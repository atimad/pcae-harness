# Phase 147L.4 — AESIC-001 Final Contract Repair Independent Verification

**Phase ID:** 147L.4
**Mode:** Independent Verification (verification-only — no implementation,
no contract repair, no schema change, no runtime change, no production
source change)
**Baseline:** AESIC-001 v1.2 (`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`)
**Date:** 2026-07-31

---

## 1. Executive Summary

Phase 147L.3 revised AESIC-001 from v1.1 to v1.2 to close the two
Non-Blocking findings Phase 147L.2 raised against the v1.1 repair: the
missing Stage 1→Stage 2 interface channel (§3.1) and the missing
tamper-evidence mechanism for the canonical pointer (§3.2). This phase
independently re-derives both findings from primary sources, independently
re-verifies that v1.2 closes them, and performs a fresh adversarial pass
against the complete repaired contract without reusing 147L.2's or
147L.3's own wording or attack list.

**Result:** Both Phase 147L.2 findings are confirmed resolved. This
verification's own independent adversarial process surfaces **one new
Major, Non-Blocking finding** and **one new Minor, Non-Blocking finding**,
neither reported by Phase 147L.2 or 147L.3, both external to the two
closed findings and to each other:

- **Finding A [Major, Non-Blocking].** The Stage 2 idempotency no-op
  branch (AESIC-REQ-023(a), gated by AESIC-REQ-121's equality procedure)
  compares only `citation_text` and `AuthorityEvaluationOutcome` fields —
  never `stage_1_outcome_ref` or the fact that a `stage_1_result` was
  supplied at all. A legitimately-obtained, fully-validated `stage_1_result`
  supplied to a Stage 2 attempt that turns out to be a same-outcome retry
  is therefore silently discarded: AESIC-REQ-023(a) returns the *existing*
  canonical AER unchanged, which was never validated against, and may
  entirely lack, this attempt's own `stage_1_outcome_ref` content — directly
  contradicting AESIC-REQ-057's "MUST carry... whenever the caller supplies
  AES a valid `stage_1_result` for the same `evaluate_stage_2` call."
- **Finding B [Minor, Non-Blocking].** §11.2's restart matrix, which
  AESIC-REQ-103 requires to name every restart point, has no row for a
  crash between the AER's compound-key commit (AESIC-REQ-119 item 1) and
  the canonical pointer's own write (AESIC-REQ-119 item 2) — a restart
  point the two-tier storage model itself introduces and that is distinct
  in kind from every named row (it is neither a pointer-corruption case,
  covered by AESIC-REQ-126/127, nor any of the ten already-named rows).

Both findings are Non-Blocking: neither reopens Finding §3.1 or §3.2, and
each is resolvable by a narrow, additive future repair. Per §20 of this
phase's own authorizing prompt, a new Major finding means this
verification does **not** clear the "no new Blocking or Major
inconsistency remains" bar for recommending 147M unconditionally — this
report recommends a narrowly scoped repair phase instead, mirroring the
147L.2 → 147L.3 precedent.

**Overall Verdict: AESIC-001 v1.2 VERIFIED WITH NON-BLOCKING FINDINGS.**

---

## 2. Independent Verification Method

AESIC-001 v1.2 was read in full (2,392 lines, all 32 sections) directly
from its own text before consulting Phase 147L.2's or Phase 147L.3's own
conclusions in detail. The two Phase 147L.2 findings were re-derived from
their own primary evidence (the specific requirement text each cites,
re-read independently), not accepted from either report's restatement.
Only after forming an independent judgment of whether v1.2 closes each
finding were Phase 147L.3's own repair narrative
(`docs/verification/PHASE_147L3_AESIC_FINAL_CONTRACT_REPAIR.md`) and
AESIC-001 §29's own account read for comparison. All adversarial
constructions in §5, §7, §14, and §15 below were attempted fresh, without
reusing Phase 147L.2 §3/§9 or Phase 147L.3 §12's own scenario wording.
`docs/verification/PHASE_147L2_AESIC_REPAIR_INDEPENDENT_VERIFICATION.md`
was read in full as the immediate predecessor verification whose two
findings are this phase's baseline.

**Bootstrap confirmation** (§1 of the authorizing prompt):

```
pcae session bootstrap --agent-id claude-local --sync-lock  -> lock rehydrated, healthy, check passed
pcae check                                                   -> passed
pcae health                                                   -> healthy
pcae doctor task-memory                                       -> clean, no inconsistencies
pcae runtime inspect                                           -> Observed / observe / unavailable (unchanged)
pcae push check                                                -> clean tree, 0 unpushed commits, nothing_to_push
```

Latest completed phase: 147L.3 (report: complete). No active governed
phase other than the expected idle placeholder
(`20260731-1100-idle-awaiting-next-governed-phase-post-147l-3`). Repository
clean; branch synchronized with `origin/main` (0 ahead / 0 behind).
`PROJECT_STATUS.md`'s "## Current Phase" section is treated as
authoritative throughout.

---

## 3. Primary-Source Reconstruction

**Finding §3.1, re-derived independently from AESIC-001 v1.1's frozen
requirement text** (not from Phase 147L.2's restatement): `evaluate_stage_1`
returned a bare `AuthorityEvaluationOutcome` (v1.1 AESIC-REQ-007) directly
to its caller and nowhere else. AES held no cross-invocation state
(AESIC-REQ-017). `Session` could not carry a Stage 1 outcome
(AESIC-REQ-060). `evaluate_stage_2`'s own v1.1 signature accepted only
`session` and `package_id` (AESIC-REQ-012). AESIC-REQ-118 (§8.6, Phase
147L.1) nonetheless required the AER to embed Stage 1's *specific,
already-computed* outcome whenever one preceded. No channel existed by
which that specific value could reach the later, separate
`evaluate_stage_2` call. This is independently reconstructed as the same
gap Phase 147L.2 §3.1 reports.

**Finding §3.2, re-derived independently:** AESIC-REQ-119 item 2 (v1.1)
defined the canonical pointer's content as "at minimum: the canonical
`evaluation_id`, `record_id`, and `record_digest`" with no digest of the
pointer's own content and no read-time verification obligation, while the
AER itself carries `record_digest` (AESIC-REQ-055) and is named in §15's
security table as digest-covered against tampering. The pointer, a
newly-introduced, load-bearing, mutable indirection every ordinary
`package_id` lookup reads through, had no analogous mitigation. This is
independently reconstructed as the same gap Phase 147L.2 §3.2 reports.

**Independently derived required properties of a valid repair**, before
reading Phase 147L.3's own repair text: (a) for §3.1, exactly one new,
explicit, same-process transport channel from `evaluate_stage_1`'s return
value into `evaluate_stage_2`, validated against the concurrently-supplied
`session` so it cannot be forged, borrowed, or substituted, without
reopening AESIC-REQ-017/060's closed channels or AESIC-REQ-008's
closed-interface hardening; (b) for §3.2, a digest over the pointer's own
content plus a mandatory cross-check against the AER it names, fail-closed
on mismatch, with recovery left to an operator (mirroring the AER's own
digest-mismatch disposition), at no additional I/O cost beyond what the
idempotency comparison already reads.

Only after independently deriving these two property sets was AESIC-001
v1.2's actual text (§5.2.1, §12.1, §13) compared against them (§4, §6
below) and found to satisfy both — this was independently earned, not
assumed from Phase 147L.3's own "AESIC-001 v1.2 REPAIRED" verdict.

---

## 4. Stage 1 Interface Verification

Independently checked against v1.2's own text, requirement by requirement:

- **`Stage1EvaluationResult`** (AESIC-REQ-122): three fields —
  `outcome`, `evaluation_id`, `session_id`. Authoritative source: AES
  itself, computed once inside `evaluate_stage_1`. Session binding:
  `session_id`, a verbatim copy of `Session.session_id` — independently
  confirmed to be a required, non-empty, frozen field set at `Session`
  construction time (`src/pcae/interactive_workflow/models/session.py:77-104`,
  `@dataclass(frozen=True)`, `session_id: str`, with a `__post_init__`
  check raising if empty) — meaning `session_id` is populated from the
  moment a `Session` object exists, strictly before Stage 1's own
  invocation point ("at or before Confirmation," AESIC-REQ-062), not only
  at the later `build_package` call site AESIC-001 §19's own compatibility
  citation names. This independently *strengthens* the contract's own
  citation (which only demonstrated presence at a later lifecycle point)
  rather than weakening it — no gap found here.
- **Identity binding:** `outcome.claimed_identity`, sourced from the same
  `AuthorityEvaluationOutcome` shape AEMIC-001 §6 already freezes,
  unmodified.
- **Decision Template binding:** `outcome.template_ref`/`template_version`,
  same source.
- **Canonicalization/digest binding:** deliberately absent — `Stage1EvaluationResult`
  carries no digest of its own. Independently assessed as correct, not an
  omission: AESIC-REQ-128 requires it to be a same-process,
  same-call-chain parameter, never serialized or transmitted across a
  process boundary; a digest defends against tampering in transit or at
  rest, neither of which this value is ever exposed to under the
  contract's own transport model. (See §5 for the adversarial attempt to
  falsify this "never serialized" assumption.)
- **Optionality:** `stage_1_result` defaults to `None` on `evaluate_stage_2`
  (AESIC-REQ-007/125); absence is always valid.
- **Validation ownership:** AES, exclusively, via AESIC-REQ-123's four
  ordered checks, before any Registry/Resolution/store work begins
  (AESIC-REQ-124).
- **Exception behavior:** exactly one new exception type,
  `Stage1HandoffInvalidError`, closed four-reason enumeration
  (AESIC-REQ-124).
- **Restart behavior:** the in-memory value is lost on caller-process
  restart; resupplying `None` is always valid (AESIC-REQ-125, §11.2 new
  row).
- **Replay behavior:** a Stage 2 replay that returns an already-canonical
  AER (AESIC-REQ-023(a)) never re-invokes or re-validates
  `stage_1_result` — addressed further in §8/§9 below, where this
  verification's own Finding A originates.
- **Malformed-input behavior:** `Stage1HandoffInvalidError(reason=MALFORMED)`,
  checked first, before session/identity/template checks (AESIC-REQ-123
  check 1).

**Determination: the repaired public interface (§5.2/§5.2.1, AESIC-REQ-007/122/123/124/125/128)
is complete and closed** for the question of *how a Stage 1 result reaches
Stage 2*. No implementer discretion remains among the channels named.
This closes Finding §3.1 on independent re-derivation — see §8 below for a
qualification this verification finds elsewhere in the same neighborhood
(the idempotency interaction), which is not a re-opening of §3.1 itself
(the channel is real and functions exactly as specified whenever it is
consulted) but a new, adjacent gap in *when* the embedded content actually
survives into the returned/canonical AER.

Requirements inspected: AESIC-REQ-007, 008, 010, 012, 017, 057, 060, 064,
076, 080, 098, 102, 118, 122, 123, 124, 125, 128 — all eighteen, cross-read
against each other for contradiction; none found beyond Finding A (§8, an
interaction with AESIC-REQ-023/121, not with any requirement in this list
directly).

---

## 5. Stage 1 Channel Adversarial Attacks

Each attack constructed fresh; disposition determined independently.

| # | Attack | Prevented? | Requirement | Failure/continuation behavior | Ownership complete? |
|---|---|---|---|---|---|
| 1 | Fabricated Stage 1 result accepted by Stage 2 | Yes | AESIC-REQ-123 (all four checks) | `Stage1HandoffInvalidError`, no side effect | Yes — AES, caller-owned retry |
| 2 | Stage 1 result from another Session | Yes | AESIC-REQ-123 check 2 (`SESSION_MISMATCH`) | Refused before any collaborator call | Yes |
| 3 | Stage 1 result from another claimed identity | Yes | AESIC-REQ-123 check 3 (`IDENTITY_MISMATCH`) | Refused | Yes |
| 4 | Stage 1 result from another Decision Template | Yes | AESIC-REQ-123 check 4 (`TEMPLATE_MISMATCH`) | Refused | Yes |
| 5 | Stale Stage 1 result | **Not prevented — by design** | AESIC-REQ-065/123 (staleness is not a validation axis) | Accepted, embedded verbatim | Yes — deliberate, disclosed |
| 6 | Malformed Stage 1 result | Yes | AESIC-REQ-123 check 1 (`MALFORMED`) | Refused first, before any other check | Yes |
| 7 | Valid-looking result with altered embedded outcome | Partially — see below | AESIC-REQ-123 checks 3/4 (compare `outcome.claimed_identity`/`template_ref`/`template_version` against `session`) | A tampered `outcome` whose identity/template fields still happen to match `session` (only its `eligibility`/`reasons` altered) passes all four checks — see finding below | Gap identified, not closed by this requirement set alone |
| 8 | Valid-looking result with mismatched digest | N/A — no digest exists on `Stage1EvaluationResult` by design (§4 above) | AESIC-REQ-128 (same-process transport, never serialized) | Not applicable within the contract's own transport model | Yes, conditional on the never-serialized assumption holding |
| 9 | Arbitrary caller-controlled substitution | Yes | AESIC-REQ-123 (full sequence) | Refused unless it happens to pass all four checks, which requires already controlling a matching `session`/identity/template (§3 above, re-derived from AESIC-REQ-123 directly) | Yes |
| 10 | Ambient-state injection | Yes | AESIC-REQ-017 (statelessness), AESIC-REQ-128 (no ambient-state input channel) | Structurally impossible — no ambient read is a defined input | Yes |
| 11 | Registry-based reconstruction not authorized by contract | Yes | AESIC-REQ-128 row 4 ("no store exists" for `stage_1_result`) | Structurally impossible | Yes |
| 12 | Restart where the Stage 1 channel becomes unavailable | Handled, not an attack | AESIC-REQ-125, §11.2 new row | Caller supplies `None`; valid | Yes |
| 13 | Replay where Stage 1 changes between invocations | **Not prevented — Finding A** | AESIC-REQ-023(a)/121 (equality procedure) | Silently discarded on the "unchanged" branch — see §8/§9 | **Gap — Finding A** |
| 14 | Stage 2 invocation where absence and corruption are indistinguishable | Cannot arise | `None` vs. any object failing check 1 always distinguishable (Python type system + AESIC-REQ-123 structural check) | N/A | Yes |

**New observation from attack #7 (independently constructed, not named by
either prior phase).** AESIC-REQ-123's four checks validate *provenance*
(session/identity/template binding) and *structure*, never the *content*
of `outcome`'s own eligibility fields (`evaluation_result`, `reasons`,
etc.) against anything AES could independently recompute. A caller that
holds a genuine `Stage1EvaluationResult` for the correct session/identity/
template but that has been altered in-memory (or maliciously constructed
with correct binding fields but a fabricated `evaluation_result`) between
receiving it from `evaluate_stage_1` and passing it to `evaluate_stage_2`
would pass all four AESIC-REQ-123 checks and be embedded verbatim as
`stage_1_outcome_ref`.

**Disposition:** independently assessed as **not a defect**, and not
elevated to a finding. `stage_1_outcome_ref` is explicitly advisory-only,
non-authoritative content (AESIC-REQ-070/071: Stage 2 unconditionally
supersedes Stage 1 for every citation purpose; AESIC-REQ-090/091: no AES
output may ever gate or authorize anything). A tampered *embedded copy* of
Stage 1's outcome changes nothing about what is actually cited
(`citation_text` is always Stage 2's own, freshly resolved,
AESIC-REQ-058) or what Stage 2 evaluates (Stage 2 re-resolves and
re-evaluates independently, AESIC-REQ-011/067, never trusting
`stage_1_result` for anything beyond disagreement-visibility). The
contract's own threat model for `stage_1_result` (§15's table, "Stage 1
outcome fabrication/substitution") is explicitly scoped to
provenance-forgery (wrong session/identity/template), matching
AESIC-REQ-123's own four checks exactly — it never claims to defend
against a caller corrupting its own in-memory advisory display data, which
would be a self-inflicted, non-authority-relevant act with no security
consequence (nothing downstream trusts the embedded copy for anything
except disagreement display). No requirement change is warranted.

---

## 6. Stage 1 Absence Semantics

Independently re-verified against AESIC-REQ-062/063/125 and the §11.2
restart-matrix row "Restart between Stage 1 and Stage 2":

- **Stage 1 optionality:** confirmed optional — AESIC-REQ-062/063 require
  Stage 1 to occur "at or before Confirmation" only if the caller invokes
  it; nothing requires invocation.
- **Absence representation:** `stage_1_result=None`, the parameter's own
  default (AESIC-REQ-007).
- **Stage 2 proceeds on absence:** yes, unconditionally (AESIC-REQ-125,
  restating AESIC-REQ-062/063's pre-existing permission).
- **Supersession remains meaningful on absence:** yes — AESIC-REQ-070/071
  (unconditional Stage 2 supersession for citation purposes) does not
  depend on Stage 1 having occurred; it governs the relationship between
  the two stages *when both occur*, and is vacuously unaffected when Stage
  1 did not.
- **Absence vs. malformed confusion:** independently re-tested — `None`
  can never satisfy AESIC-REQ-123 check 1's "well-formed
  `Stage1EvaluationResult`" test, and any non-`None` value that fails
  check 1 is never silently treated as absent (it raises
  `Stage1HandoffInvalidError(reason=MALFORMED)` instead). No confusion
  path found.
- **Restart/replay preserve the same result:** confirmed — a caller that
  loses its in-memory `Stage1EvaluationResult` across a restart simply
  supplies `None`, indistinguishable at the AER level from "Stage 1 never
  invoked" (§11.2's new row, explicitly disclosed as not required to be
  distinguishable).

**Determination:** the repair did not silently make Stage 1 mandatory.
Confirmed independently, no gap found.

---

## 7. Canonical Pointer Integrity Verification

Independently reconstructed from AESIC-001 v1.2 §12.1 (AESIC-REQ-119 item
2, AESIC-REQ-126) and §13 (AESIC-REQ-127):

- **Pointer content:** `{package_id, evaluation_id, record_id,
  record_digest, pointer_digest}` — independently confirmed exhaustive per
  AESIC-REQ-126 item 1's own enumeration.
- **`pointer_digest`:** `compute_record_digest` over the other four
  fields, same function every other durable record in this codebase uses
  (AESIC-REQ-055), AES-owned at write time (AESIC-REQ-126 item 1).
- **Binding to `record_id`/`record_digest`:** both are pointer fields
  themselves, covered by `pointer_digest`'s own recomputation (detects
  corruption of either).
- **Binding to the compound evaluation key:** the pointer's own
  `package_id`/`evaluation_id` fields are the compound key's two halves;
  both are covered by `pointer_digest` and are the values used to retrieve
  the AER the pointer names, "cross-checked against `record_id`"
  (AESIC-REQ-126 item 2(b)) — independently verified this closes a
  three-way consistency check (package_id, evaluation_id, record_id must
  all cohere with the retrieved AER), not merely a two-way one.
- **Validation before use:** mandatory, two ordered steps, before treating
  any pointer as canonical (AESIC-REQ-126 item 2).
- **Mismatch behavior:** `CanonicalPointerCorruptError` (AESIC-REQ-127),
  fail-closed, no canonical result returned.
- **Deterministic reconstruction/recovery:** operator-owned; an
  implementation MAY offer a deterministic rebuild-from-primary-store
  convenience, never automatic (AESIC-REQ-126 item 4) — independently
  assessed as the correct disposition, since automatic selection among
  multiple surviving compound-keyed entries for one `package_id` is not a
  fact derivable from the primary store alone without an ordering record
  the corrupted pointer itself was the sole holder of.
- **Concurrency semantics:** unchanged last-write-wins (AESIC-REQ-120);
  independently confirmed orthogonal to integrity — "which write wins" and
  "is the winning write internally self-consistent" are independent
  questions, and AESIC-REQ-126 answers only the second.
- **Atomicity:** `pointer_digest` rides in the same atomic-replace write
  the pointer already used (AESIC-REQ-119 item 2, AESIC-REQ-086) —
  independently confirmed no new atomicity requirement is introduced.
- **Relationship to immutable AER history:** the primary, compound-keyed
  store (AESIC-REQ-119 item 1) is untouched by any pointer-integrity
  mechanism; a pointer-level fault never touches, and is never resolved by
  mutating, AER history.

**Determination:** the pointer is now tamper-evident for both failure
variants Phase 147L.2 §3.2 constructed (bit-level pointer corruption; a
corrupted `record_id` silently naming a different, valid AER). Corruption
of the pointer can never silently change which AER a consumer treats as
effective — either check catches it, or the pointer is genuinely
self-consistent (§7's own scope boundary — see §15 below for the residual
threat class this deliberately does not cover). Confirmed independently.

---

## 8. Pointer Integrity Adversarial Attacks

| # | Attack | Contract-defined result |
|---|---|---|
| 1 | Pointer selects correct `record_id` but wrong `record_digest` | Detected — AESIC-REQ-126 item 2(b) cross-check against the AER's own self-carried digest fails |
| 2 | Pointer selects wrong `record_id` with a recomputed `pointer_digest` | Detected if the named AER is any AER other than the one whose digest the (correctly recomputed) `pointer_digest` was originally paired with at write time — but see §15 below for the one residual case (a fully self-consistent forgery) this is not claimed to catch, matching AESIC-REQ-055's own explicitly disclosed scope |
| 3 | Pointer rollback selects an older superseded AER | Not integrity-detectable if the pointer is internally self-consistent — governed instead by AESIC-REQ-120's disclosed last-write-wins concurrency semantics, independently confirmed to be the correct governing requirement for this case, not a gap |
| 4 | Pointer points to an AER under another compound key | Detected — retrieval uses the pointer's own `(package_id, evaluation_id)`; a pointer corrupted to name a foreign compound key would fail `pointer_digest` recomputation (item 1 covers `package_id`/`evaluation_id`) unless the corruption also recomputed a matching digest, the same residual case as attack 2 |
| 5 | Pointer points to a missing AER | Not explicitly named as its own AESIC-REQ, but independently derivable as a third detectable case: a compound-key read that fails ("no such entry") at AESIC-REQ-126 item 2(b)'s retrieval step is, by construction, not a pointer that can complete its own mandatory verification — treated as equivalent to a mismatch (no canonical result may be returned), consistent with AESIC-REQ-127's fail-closed framing, though the contract text does not spell out "retrieval failure" as a third explicit trigger alongside its two named digest checks (Minor textual completeness observation, not elevated to a finding — the fail-closed outcome is unambiguous either way) |
| 6 | Pointer content is truncated | Detected — truncation almost always fails structural parsing before digest comparison is even reached, and any surviving truncation that still recomputes a wrong `pointer_digest` is caught by item 2(a) |
| 7 | Pointer digest is absent | Detected — AESIC-REQ-126 item 1 makes `pointer_digest` a mandatory field of the pointer's persisted content; its absence is itself a structural defect the mandatory verification (item 2) cannot complete successfully, fail-closed by the same reasoning as attack 5 |
| 8 | Pointer digest is malformed | Detected — a malformed digest cannot equal a freshly recomputed one |
| 9 | Two concurrent writers create conflicting current-effective pointers | Cannot occur — single atomically-replaced artifact per `package_id`; exactly one atomic replace is last (AESIC-REQ-120) |
| 10 | AER commit succeeds but pointer update fails | **Not addressed by an explicit restart-matrix row — Finding B, §11 below** |
| 11 | Pointer update succeeds but referenced AER is unavailable | Cannot occur under the primary store's own immutability/never-deleted guarantee (AESIC-REQ-119 item 1) combined with the write ordering AESIC-REQ-119 itself specifies (compound-key write, "followed by" the pointer's own write) — the AER necessarily exists before its pointer can ever name it |
| 12 | Replay trusts a corrupted pointer | Cannot occur — AESIC-REQ-126's verification re-runs on every lookup, no cached "already verified" shortcut (AES's own statelessness, AESIC-REQ-017) |
| 13 | Pointer recovery modifies immutable AER history | Forbidden — AESIC-REQ-126 item 4's recovery model reads the primary store, never writes to it |
| 14 | Pointer recovery chooses a different effective outcome than uninterrupted execution | Possible only through explicit operator selection among multiple already-existing, already-valid compound-keyed entries — disclosed as operator-owned, not an automatic contract-level guarantee, and therefore not itself a violation of AESIC-REQ-077's observational-equivalence requirement, which governs automatic resumption, not manual operator intervention after a detected corruption |

---

## 9. Concurrency and Atomicity Verification

Independently verified:

- **Only one current-effective pointer can result:** yes — single
  atomically-replaced artifact per `package_id` (AESIC-REQ-119 item 2,
  AESIC-REQ-120).
- **No committed AER can be silently lost:** yes — the primary,
  compound-keyed store never updates or deletes an entry
  (AESIC-REQ-119 item 1); a pointer fault affects only convenience lookup,
  never the underlying data.
- **A failed pointer update is recoverable:** yes, but only via disclosed,
  operator-directed action once detected (AESIC-REQ-126 item 4) — **and,
  independently identified here, a failed-to-even-attempt pointer update
  (a crash before the write, rather than a corrupted write) has no
  explicit contract-level recovery statement at all — see Finding B, §11.**
- **Retry is observationally equivalent to uninterrupted execution:**
  confirmed for every named restart-matrix row (AESIC-REQ-077); **not
  independently confirmable for the specific crash point Finding B names,
  because that point has no row to check equivalence against** — a
  completeness gap, not a demonstrated inequivalence (§11 below argues the
  natural, unstated behavior likely is equivalent, but the contract does
  not say so).
- **No implementation-specific transaction mechanism is assumed:** confirmed
  — every mechanic named (`O_CREAT|O_EXCL`, atomic-replace) is a portable,
  already-established codebase idiom (AESIC-REQ-086), not tied to any
  particular database or filesystem feature beyond what `storage.py`
  already assumes elsewhere in this codebase.

---

## 10. Replay and Restart Verification

Fresh replay analysis at all ten named points in the authorizing prompt's
own list, independently re-derived from AESIC-001 §11.2's restart matrix
and §9's lifecycle text (not merely re-stating that matrix):

1. **Before Stage 1.** No effect; Stage 1 simply runs whenever next
   invoked (§11.2 row 1).
2. **After Stage 1, before Stage 2.** Any in-memory `Stage1EvaluationResult`
   the caller holds survives only as long as the caller's own process;
   caller may supply it or, after a restart, supply `None` — both valid
   (§11.2's new "Restart between Stage 1 and Stage 2" row, AESIC-REQ-076).
3. **During Stage 1 result validation.** AESIC-REQ-123's four checks are
   evaluated in strict order, first-failure-wins, before any Registry/
   Resolution/store I/O (AESIC-REQ-124) — a crash mid-validation before any
   check completes simply means the whole `evaluate_stage_2` call never
   happened; retry re-runs validation from scratch with the same or a
   different `stage_1_result`, no partial validation state to resume.
4. **Before Stage 2 evaluation (post-validation).** Resolution/Registry
   read fresh every time (§6.5/§7.1); no caching to go stale.
5. **After Stage 2 evaluation, before AER persistence.** No effect — an
   in-memory, not-yet-persisted evaluation result is discarded on crash; a
   retry recomputes (§12.2, AESIC-REQ-080).
6. **After AER persistence, before pointer update.** **This is exactly
   Finding B's restart point** — independently identified as the one
   named in the authorizing prompt's own list that has no corresponding
   row in AESIC-001's own §11.2 table.
7. **After pointer update, before publication.** AER already durable and
   canonical; a retried Coordinator `execute()` uses the already-persisted
   AER's `citation_text` unchanged (§11.2 row "After Publication
   authorization, before Coordinator commit").
8. **After publication.** AER remains the durable, immutable record of
   what was cited; never re-evaluated post-publication (§11.2 row "After
   Coordinator commit").
9. **During repeated publication.** Governed entirely by the Coordinator's
   own idempotency marker, independent of AES (§11.2 row "Duplicate
   publication attempt").
10. **After Registry or Decision Template evolution.** Each Stage 2 attempt
    always re-resolves fresh; a changed Declaration/template produces a
    genuinely new, canonical AER via supersession (§11.2 rows "Registry
    evolution"/"Decision Template evolution").

**Determination:** the repaired contract preserves observational
equivalence at nine of the ten points independently checked. Point 6
(equivalently, adversarial attack #10 in §8 above) is the one point this
verification could not confirm equivalence for, because AESIC-001 v1.2
does not state what happens there — this is Finding B, reported below,
not asserted as a demonstrated inequivalence (the natural retry-based
behavior most likely *is* equivalent; the contract simply never says so,
which is itself the gap AESIC-REQ-103 exists to prevent).

---

## 11. Full Contract Consistency Audit

Re-read AESIC-001 v1.2 in full, not only §5.2.1/§12.1/§13's repaired
sections, checking for:

- **Contradictions between repaired and untouched requirements.** One
  found and reported in full below (Finding A: AESIC-REQ-057 vs.
  AESIC-REQ-023(a)/121). No second contradiction found after checking
  every requirement §29.4 lists as touched against every requirement it
  cross-references (AESIC-REQ-008, 054, 055, 061, 065, 070, 071, 083, 090,
  091, 097, 101, 109, 113 — all independently re-read against the seven
  new requirements; no divergence found beyond Finding A).
- **Duplicate or conflicting definitions.** None found — §3's terminology
  table was checked against every later use of `Stage1EvaluationResult`
  and `pointer_digest`; both are used consistently throughout.
- **Invalid requirement cross-references.** None found — every
  `AESIC-REQ-###` citation within §5.2.1, §12.1, and §13 resolves to a
  requirement that exists and says what it is cited as saying.
- **Undefined terminology.** None found — `Stage1EvaluationResult` and
  `pointer_digest` are both defined in §3 before first normative use.
- **Inconsistent exception taxonomy.** None found — `Stage1HandoffInvalidError`
  and `CanonicalPointerCorruptError` are both correctly folded into
  AESIC-REQ-010's "only the error taxonomy of §13" framing (independently
  re-checked: §13's table now lists both, and no other section introduces
  a third, undisclosed exception type).
- **Lifecycle contradictions.** None found beyond Finding A, which is
  itself a lifecycle-adjacent (idempotency) contradiction — see §12 below
  for why it is classified as such rather than as a pure "persistence"
  finding.
- **Replay contradictions.** Finding B (§10 above, restated §13 below).
- **Persistence contradictions.** None found beyond Finding A (which is,
  more precisely, an idempotency-comparison contradiction touching
  persistence only insofar as it determines whether a write occurs).
- **Failure-ownership gaps.** None found — §13's table was independently
  re-checked to assign exactly one origin/owner/recovery-owner/retry-owner
  to `Stage1HandoffInvalidError` and `CanonicalPointerCorruptError` each;
  no dual ownership found (§14 below).
- **Security omissions.** None found beyond the residual, explicitly
  disclosed forgery limit already present in AESIC-REQ-126 item 3 and
  independently reconfirmed in §15 below (not a new omission — an
  already-disclosed one, scope-checked and found accurately described).
- **Observability gaps.** None found — AESIC-REQ-094/096/097 remain
  satisfiable unchanged by anything this repair touched.
- **Diagrams or examples inconsistent with normative text.** The
  §5.2/§5.2.1 code-shape example was independently checked field-by-field
  against AESIC-REQ-122/123/128's own prose — consistent.
- **Requirement matrix inconsistencies.** §21's matrix was independently
  cross-checked entry-by-entry against §5.2.1/§12.1/§13's actual text for
  all seven new requirements (AESIC-REQ-122–128) — every falsifiability
  anchor accurately describes what the requirement actually says. No
  inconsistency found.
- **Requirement IDs unique and stable.** Confirmed — AESIC-REQ-001 through
  AESIC-REQ-128, sequential, no gaps, no reuse, independently counted
  against §21's own closing tally.

---

## 12. Requirement Verification Matrix

| Requirement | Necessary | Sufficient | Internally consistent | Externally compatible | Implementable | Independently supported | Ambiguous | Contradictory |
|---|---|---|---|---|---|---|---|---|
| AESIC-REQ-007 | Yes | Yes (as a channel-opening change) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-010 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-012 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-057 | Yes | **No, alone** — the "MUST carry... whenever supplied" guarantee is defeated by AESIC-REQ-023(a)'s no-op branch (Finding A) | Yes, internally | Yes | Yes, once Finding A is closed | Yes | **No — contradicts AESIC-REQ-023(a)/121** | See Finding A |
| AESIC-REQ-076 | Yes | Yes for the nine rows it names; **No for the tenth restart point** (crash between AER commit and pointer write, Finding B) | Yes | Yes | Partially — the unstated point has no defined behavior to implement against | Yes for named rows | Yes — one restart point left undefined | No (an omission, not a conflict) |
| AESIC-REQ-098 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-119 | Yes | Yes for storage/keying; the item-2 write ordering it implies is the basis of Finding B | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-122 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-123 | Yes | Yes for provenance validation; does not (and is not claimed to) validate content integrity (§5 attack #7, assessed as not a gap) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-124 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-125 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-126 | Yes | Yes for the two threat variants it names; does not close the residual forgery case (explicitly disclosed, §15) | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-127 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| AESIC-REQ-128 | Yes | Yes | Yes | Yes | Yes | Yes | No | No |

**Untouched requirements materially affected by the repair, independently
identified:**

- **AESIC-REQ-023(a)** (§5.11, unchanged text) — materially affected
  because it is the mechanism through which Finding A arises; its own text
  was not touched by Phase 147L.3 and remains, on its own terms,
  internally correct — the contradiction is with the *new* AESIC-REQ-057
  text, not a defect AESIC-REQ-023(a) introduces unilaterally.
- **AESIC-REQ-121** (§12.1, unchanged text) — same reason; its equality
  procedure was correctly scoped to `citation_text`/`AuthorityEvaluationOutcome`
  fields when written (to resolve Finding 2/3, which never involved
  `stage_1_result`), and was never revisited when AESIC-REQ-057/122/123
  were introduced three phases later.
- **AESIC-REQ-103** (§17, unchanged text) — its own "every restart point
  named in §11.2 SHALL have a defined, safe resumption" guarantee is the
  provision Finding B shows is not fully discharged.

---

## 13. Architectural Preservation

Attempted to falsify each invariant independently, not by re-confirming
Phase 147L.3's own §13/§29.5 table:

| Invariant | Independently confirmed | Evidence |
|---|---|---|
| AES remains sole lifecycle orchestrator | Preserved | AESIC-REQ-005/006 byte-for-byte unchanged; §5.2.1's new mechanics are internal to AES's own already-owned evaluate/persist responsibilities |
| Decision Template Resolution remains AES-owned | Preserved | §6 entirely untouched — zero requirements in §6 appear in §29.4's changed list, independently re-confirmed by re-reading §6 in full |
| Registry remains lookup-only | Preserved | §7 entirely untouched |
| Evaluator remains pure and deterministic | Preserved | `evaluate()` never named as an actor in any repaired/new requirement; AESIC-REQ-123's comparisons consume already-produced `outcome` fields only |
| Evaluator never resolves Registry state | Preserved | Same evidence — no requirement routes Registry access through the evaluator |
| Publication Coordinator remains publication-only | Preserved | §14 entirely untouched |
| Stage 1 remains advisory | Preserved | AESIC-REQ-070/071 byte-for-byte unchanged; `stage_1_result`'s only effect is an embedded, non-authoritative display field (independently confirmed in §5's attack #7 disposition) |
| Stage 2 unconditionally supersedes Stage 1 | Preserved | Same, AESIC-REQ-070/071 untouched |
| AER history remains immutable | Preserved | AESIC-REQ-054/082/119 item 1 untouched; `pointer_digest` is metadata about a different artifact |
| Canonical pointer remains mutable only as current-effective selection state | Preserved | AESIC-REQ-120's last-write-wins model untouched; AESIC-REQ-126 adds detection, not a new mutation path |
| Evaluation remains disclosure-only | Preserved | §14.1/§14.2 entirely untouched |
| Evaluation never authorizes execution/permission/readiness/confirmation/publication | Preserved | AESIC-REQ-090/091 untouched; independently re-verified `stage_1_result`/`CanonicalPointerCorruptError` introduce no new gating path — a raised `Stage1HandoffInvalidError` or `CanonicalPointerCorruptError` *prevents* an AER from being produced/returned, which is refusal-to-disclose, not authorization-of-anything |
| Replay remains observationally equivalent | **Preserved for nine of ten independently-checked restart points; not confirmable for the tenth (Finding B)** | §10 above |
| Runtime capability remains unchanged | Preserved | `pcae runtime inspect`: Observed / observe / unavailable, unchanged throughout this phase's own bootstrap (§2 above); this is contract text only |

**Falsification specifically attempted (fresh, not reusing §29.5's own
attempt):** could AESIC-REQ-126's mandatory read-time verification be read
as granting AES a new authority to *refuse to disclose* an otherwise-valid
AER, functioning as a disguised gating mechanism? Checked: a
`CanonicalPointerCorruptError` is raised only when the pointer's own
content fails internal-consistency checks — it never evaluates the
underlying AER's *substance* (its `ELIGIBLE`/`INELIGIBLE`/`INDETERMINATE`
outcome) to decide whether to disclose it. This is refusal-on-corruption,
identical in kind to a disk-read failure, not a decision made on the
outcome's own merits — disclosure-only semantics (AESIC-REQ-089–091) are
not violated. No widening found.

---

## 14. Cross-Contract Compatibility

Independently re-verified by direct citation-checking, not by trusting
AESIC-001 §29.6's or Phase 147L.3's own compatibility claims:

- **AEM-001 v1.0.** §7 (Registry) untouched by this repair; no new
  citation. Confirmed unaffected.
- **AEMIC-001 v1.2.** `Stage1EvaluationResult.outcome` is independently
  confirmed to be exactly the unmodified `AuthorityEvaluationOutcome`
  type (AEMIC-001 §6) — no field added, renamed, or reinterpreted;
  `Stage1EvaluationResult` itself is a new AESIC-001-owned wrapper, never
  presented as an AEMIC-001 type. Session identity/`session_id` reuse:
  independently confirmed a pre-existing, frozen `Session` field (§4
  above), not a new obligation on AEMIC-001 (which does not define
  `Session` at all — that is IWC-001's domain, checked next).
- **IWC-001 v1.2.** `Session.session_id`: independently confirmed present
  and populated at `Session` construction (§4 above, direct source
  inspection — stronger evidence than AESIC-001 §19's own citation of
  `PublicationHandoff.build_package`). §5.13/§9.2 isolation (Interactive
  Workflow SHALL NOT import AES): untouched — no requirement in this
  repair touches Interactive Workflow's own code or obligations.
- **IWPC-001 v1.4.** Evaluator invocation semantics unaffected — `evaluate()`
  is never called differently by anything this repair adds.
  Readiness-package compatibility: `authority_evaluation_ref` remains
  optional, unaffected (AESIC-REQ-109, untouched). IWPC-REQ-144/147's
  last-write-wins precedent, cited by AESIC-REQ-120, is unaffected by this
  repair (AESIC-REQ-120's own text was not touched by Phase 147L.3).
- **PEC-001 v1.1.** Publication ownership, duplicate-publication behavior:
  §14's consumer table entirely untouched; the Coordinator still consumes
  only `citation_text` via reference, never `stage_1_outcome_ref` or any
  pointer-integrity detail (AESIC-REQ-089/090/091, unaffected).
- **CHGR-001 v1.3.** CHGR citation-only consumption, disclosure-only
  semantics: unaffected — `authority_basis_claimed` still derives only
  from Stage 2's `citation_text` (AESIC-REQ-058, untouched); nothing this
  repair adds is ever cited into CHGR.

**Determination: no predecessor-contract amendment is required.**
Independently reconfirmed, matching AESIC-REQ-113's claim across all three
revisions (v1.0, v1.1, v1.2).

---

## 15. Failure Ownership Verification

Independently re-verified against §13's table for every failure newly
introduced or affected by this repair:

| Failure | Origin | Detection owner | Recovery owner | Retry owner | Logging owner | User-visible owner |
|---|---|---|---|---|---|---|
| Missing Stage 1 result | N/A (`None`, always valid) | N/A | N/A | N/A | N/A | N/A |
| Malformed Stage 1 result | Caller-supplied input | AES (AESIC-REQ-123 check 1) | Caller (corrects or omits) | Caller | AES | AES's caller |
| Stale Stage 1 result | Expected behavior, not a failure | N/A | N/A | N/A | N/A | N/A |
| Session mismatch | Caller-supplied input | AES (check 2) | Caller | Caller | AES | AES's caller |
| Identity mismatch | Caller-supplied input | AES (check 3) | Caller | Caller | AES | AES's caller |
| Decision Template mismatch | Caller-supplied input | AES (check 4) | Caller | Caller | AES | AES's caller |
| Digest mismatch (pointer) | Pointer's own storage | AES (AESIC-REQ-126, at read time) | Operator | N/A — not retryable, corruption-class | AES | Whoever performs the lookup |
| Pointer corruption | Pointer's own storage | AES | Operator | N/A | AES | Whoever performs the lookup |
| Pointer rollback | Concurrency (disclosed), not a failure | N/A | N/A | N/A | N/A | N/A |
| Missing referenced AER | Cannot occur under AESIC-REQ-119's write-ordering guarantee (§8 above, attack 11) | N/A | N/A | N/A | N/A | N/A |
| Concurrent pointer conflict | Concurrency (disclosed last-write-wins), not a failure | N/A | N/A | N/A | N/A | N/A |
| **Partial AER/pointer commit** (crash between the two writes) | AES's own two-step persistence sequence | **No named detection owner — Finding B** | **No named recovery owner — Finding B** | Presumably AES's caller (by analogy with "AER write failure," the nearest named row), but not stated | Presumably AES (by analogy), not stated | Presumably AES's caller, not stated |
| Recovery failure (pointer rebuild fails) | Operator action itself | Operator | Operator | Operator | Not specified beyond AESIC-REQ-126 item 4's own text | Operator |

**No ownership gap or dual authority found** for any row this repair
explicitly names (`Stage1HandoffInvalidError`, `CanonicalPointerCorruptError`
each have exactly one origin/detection/recovery/retry/logging/user-visible
owner, independently re-checked against §13's actual table text). **One
ownership gap found** for the row this repair's own write-ordering
implies but never names as its own failure-ownership entry — the same gap
underlying Finding B, restated here from the failure-ownership angle
rather than the restart-matrix angle.

---

## 16. Independent Threat Analysis

Performed fresh, without reusing Phase 147L.2 §3 or Phase 147L.3 §12's own
wording:

- **Untrusted caller input.** `stage_1_result` is the only new untrusted
  per-call input this repair adds. AESIC-REQ-123's four-check validation
  is independently assessed as adequate for the provenance threat it
  targets; §5's attack #7 identifies the one thing it does not target
  (content-integrity of an already-provenance-valid object) and finds that
  omission harmless given the field's advisory-only, non-authoritative
  role.
- **Cross-session substitution.** Closed — AESIC-REQ-123 check 2.
- **Historical-outcome manipulation.** Bounded to the same non-authoritative
  scope as above — Stage 2's own re-evaluation is never influenced by
  `stage_1_result`'s content (only its presence/absence and, when present,
  its provenance-validity), so no manipulation of it can change what is
  actually cited.
- **Digest confusion.** Independently attempted to construct a scenario
  where a consumer treats the pointer's own `record_digest` copy as
  authoritative over the AER's self-carried one, or vice versa in a way
  that matters. AESIC-REQ-083 unambiguously assigns the AER's own digest
  computation to AES exclusively; the pointer's copy exists only to be
  cross-checked against it (AESIC-REQ-126 item 2(b)), never substituted
  for it. No confusion path found.
- **Current-pointer rollback.** Addressed in §7/§8 above (attack 3) —
  governed by disclosed concurrency semantics, not a defect.
- **Key collision.** `evaluation_id` uniqueness (AESIC-REQ-098) remains the
  load-bearing guarantee for compound-key collision-freedom; unaffected by
  this repair; independently re-confirmed no new key-collision surface is
  introduced by `Stage1EvaluationResult` (it is never itself a storage
  key).
- **Stale Registry state.** Unaffected — Resolution/Registry re-resolve
  fresh every call (§6.5/§7.1), unchanged.
- **Stale Decision Template state.** Same.
- **Crash recovery.** This is where Finding B originates — see §11 above.
- **Concurrent supersession.** Addressed §9 above — cannot produce more
  than one current-effective pointer.
- **Denial of service through malformed references.** A caller repeatedly
  supplying malformed `stage_1_result` values only ever costs AES the
  four cheap, in-memory AESIC-REQ-123 checks (no Registry/store I/O occurs
  before the refusal, AESIC-REQ-124) — independently assessed as bounded,
  no amplification vector found.
- **Authority confusion caused by conflicting Stage 1 and Stage 2
  outcomes.** Structurally prevented — AESIC-REQ-070/071's unconditional
  supersession and AESIC-REQ-090/091's non-gating prohibition jointly
  ensure a Stage 1/Stage 2 disagreement can only ever be *displayed*
  (embedded in the AER, never acted on) — independently re-confirmed no
  code path this contract describes could let Stage 1's outcome override
  or block Stage 2's.

**New findings from this section:** none beyond Finding A and Finding B,
already derived above and restated in §17.

---

## 17. Findings

### Finding A — [Major, Non-Blocking] Idempotency no-op can silently discard a validated `stage_1_result`

**Requirements in tension:** AESIC-REQ-057 (§8.6, repaired Phase 147L.3)
vs. AESIC-REQ-023(a) (§5.11, unchanged since v1.0) and AESIC-REQ-121
(§12.1, unchanged since v1.1).

**Statement.** AESIC-REQ-057 requires: "The AER MUST carry a
`stage_1_outcome_ref` field whenever the caller supplies AES a valid
`stage_1_result` for the same `evaluate_stage_2` call." AESIC-REQ-121's
equality procedure — which decides whether a Stage 2 attempt is classified
"unchanged" (AESIC-REQ-023(a)) or "changed" (AESIC-REQ-023(b)) — compares
only the freshly-resolved `citation_text` and the freshly-computed
`AuthorityEvaluationOutcome`'s fields (excluding `evaluated_at`) against
the current canonical AER's corresponding fields. It never compares
whether a `stage_1_result` was supplied to this attempt, nor the content
of `stage_1_outcome_ref` at all. When the comparison finds "unchanged,"
AESIC-REQ-023(a) requires AES to "return that already-persisted AER
unchanged — no new AER SHALL be written."

**Concrete failure scenario (constructed fresh).**

1. Caller invokes `evaluate_stage_2(session=s, package_id=p)` with
   `stage_1_result=None` (Stage 1 was never invoked, or its result was
   discarded). AES writes AER `A1` — `citation_text=C`, outcome fields
   `O`, no `stage_1_outcome_ref` — and it becomes canonical for `p`.
2. Later, the same caller invokes `evaluate_stage_1(session=s)`, receives
   a genuine `Stage1EvaluationResult` `R`, and retains it.
3. The caller invokes `evaluate_stage_2(session=s, package_id=p,
   stage_1_result=R)`. `R` passes all four AESIC-REQ-123 checks (it
   genuinely belongs to `s`). AES freshly re-resolves and re-evaluates,
   obtaining the identical `citation_text=C` and outcome fields `O`
   (nothing changed in the Registry or Decision Template between steps 1
   and 3).
4. AESIC-REQ-121's comparison classifies this "unchanged" (the only fields
   it compares — `C` and `O` — are identical to `A1`'s). AESIC-REQ-023(a)
   therefore requires AES to "return that already-persisted AER unchanged
   — no new AER SHALL be written" — i.e., return `A1`, which has no
   `stage_1_outcome_ref`.
5. But step 3's own call *did* supply AES a valid `stage_1_result` (`R`,
   which passed every AESIC-REQ-123 check) "for the same `evaluate_stage_2`
   call." AESIC-REQ-057 requires the AER this call produces to carry
   `stage_1_outcome_ref` in exactly this circumstance. The AER actually
   returned (`A1`) does not.

**Why this is not Finding §3.1 recurring.** Finding §3.1 was about whether
a Stage 1 result could ever reach `evaluate_stage_2` at all — closed by
AESIC-REQ-122/123/128. This finding accepts that the value *does* reach
AES, passes validation, and is genuinely available to embed — the gap is
that the idempotency short-circuit can still discard it before it is ever
written anywhere, a mechanism Phase 147L.2 and Phase 147L.3 did not examine
because `AESIC-REQ-023(a)`/`121` predate `stage_1_result`'s own existence
by two contract revisions and were never revisited against it.

**Severity and disposition.** **Major, Non-Blocking.** It does not affect
Finding §3.1's or §3.2's own resolution, does not affect the two-tier
storage model's supersession/concurrency correctness (§9 above, fully
independently reconfirmed), and does not affect any other requirement's
satisfiability. It is narrowly resolvable in a future repair by one of:
(a) extending AESIC-REQ-121's compared-field set to include whether
`stage_1_outcome_ref` would be present/different, so a supplied,
newly-valid `stage_1_result` that the canonical AER lacks (or whose
embedded content differs) causes a "changed" classification even when
`citation_text`/outcome fields are themselves unchanged; or (b) explicitly
carving out an exception in AESIC-REQ-057's own text disclosing that the
mandatory-when-supplied guarantee applies only to the AER actually written
by *some* Stage 2 attempt for that `package_id`, never retroactively to
one returned unchanged by a later idempotent retry — disclosing, not
hiding, the same silent-discard behavior this finding identifies. Candidate
(a) is more consistent with AESIC-REQ-057's own stated disagreement-
visibility purpose; candidate (b) is the smaller textual change. Neither
is selected here — this phase makes no contract change (§18 below).

### Finding B — [Minor, Non-Blocking] No restart-matrix row for a crash between the AER's compound-key commit and the canonical pointer's write

**Requirements in tension:** AESIC-REQ-103 (§17, "every restart point named
in §11.2 SHALL have a defined, safe resumption... no future implementation
SHALL introduce a restart point without an entry in that matrix") vs.
AESIC-REQ-119's own two-step write-ordering ("a first compound-keyed
write, followed by the pointer index's own first, exclusive-create
write") — a two-step sequence that structurally creates exactly one new
restart point (between the two writes) that §11.2's table, independently
re-read in full, does not name as its own row.

**Statement.** AESIC-REQ-119's persistence model is inherently two
sequential writes: the AER's own compound-keyed, exclusive-create write
(item 1), then the canonical pointer's own atomic-replace write (item 2).
A crash between them leaves a durably-persisted AER with no pointer
advance to make it canonical (first-ever write for a `package_id`), or
with the pointer still naming the *previous* canonical AER (a supersession
attempt). This is distinct from every row §11.2 currently names: it is not
"pointer corrupted" (AESIC-REQ-126/127's concern is a syntactically-present
but wrong pointer, not an absent-or-stale-but-otherwise-valid one), and it
is not any of the ten pre-existing rows (none of which describes a crash
*inside* AES's own two-step Stage 2 write itself, as opposed to before or
after it).

**Independently assessed likely behavior (not asserted by the contract
itself).** A retry of the same `evaluate_stage_2` call would, per
AESIC-REQ-023, recompute fresh and compare against whatever the pointer
currently names (the prior canonical AER, if any) — finding "changed"
again (since the new content still differs from the old canonical, or no
canonical exists yet) — and would write a *new* compound-keyed AER (fresh
`evaluation_id` per AESIC-REQ-098) plus attempt the pointer write again.
The AER orphaned by the original crash remains durably retrievable by its
own compound key (AESIC-REQ-119 item 1's "no entry... is ever... deleted"),
never referenced by any pointer, but never lost either. This is plausibly
observationally equivalent to uninterrupted execution — but §11.2's table
does not say so, and AESIC-REQ-103 requires it to.

**Severity and disposition.** **Minor, Non-Blocking.** No data loss, no
corruption, no consumer-visible incorrect result — the pointer, when it
does eventually get written (by this retry or a later one), is internally
consistent and passes AESIC-REQ-126's own verification. The gap is a
completeness gap in §11.2's own table, not a correctness defect in the
mechanism the table would describe. Resolvable by adding one restart-matrix
row (mirroring the three Phase 147L.3 already added for the interface
channel) stating the retry behavior this verification independently
derived as likely, making it a contractual guarantee rather than an
unstated inference.

---

## 18. Overall Verdict

**AESIC-001 v1.2 VERIFIED WITH NON-BLOCKING FINDINGS.**

- Both Phase 147L.2 findings (§3.1, §3.2) are demonstrably resolved,
  independently re-derived and re-confirmed in §4–§7 above, not merely
  accepted from Phase 147L.3's own account.
- The complete Stage 2 interface is implementable (§4, §12) — every
  input's source, derivation, and validator is named, with no remaining
  implementer discretion among the channels the original authorizing
  prompt closed.
- Pointer integrity and recovery are deterministic for every corruption
  variant this and the prior verification constructed (§7, §8), with the
  one explicitly-disclosed, unchanged residual limitation named in §16
  (a fully self-consistent forgery — out of scope for this digest scheme,
  exactly as it always was for the AER's own digest).
- Concurrency remains coherent (§9); replay remains coherent for nine of
  ten independently-checked restart points, with the tenth being Finding
  B, a completeness gap rather than a demonstrated inequivalence.
- Architecture remains preserved (§13) — all fourteen invariants named in
  this phase's own authorizing prompt independently confirmed unbroken.
- No predecessor-contract amendment is required (§14), independently
  reconfirmed against all six governing predecessors' own frozen text.
- **Two new, independently-derived, Non-Blocking findings remain
  unresolved** (§17): Finding A (Major — the idempotency/`stage_1_outcome_ref`
  interaction) and Finding B (Minor — the missing restart-matrix row for
  the AER-commit/pointer-write crash point). Neither reopens Finding §3.1
  or §3.2. Neither undermines any other requirement's satisfiability.
  Both are resolvable by a narrow, additive future repair, consistent with
  every finding this same project has resolved through the 147L → 147L.1
  → 147L.2 → 147L.3 sequence.

This verdict is independent of, and was formed before fully consulting,
Phase 147L.3's own §16 self-assessment ("AESIC-001 v1.2 REPAIRED... no new
contradiction is introduced"). This verification agrees no new
contradiction was introduced *into the seven requirements Phase 147L.3
itself wrote or repaired, considered in isolation* (§12 above finds all
seven internally consistent on their own terms), but finds that the
repair, by construction, interacts with an *adjacent, unmodified*
requirement pair (AESIC-REQ-023(a)/121) in a way neither Phase 147L.2 nor
Phase 147L.3 examined — because that interaction did not exist to examine
before AESIC-REQ-122/123 introduced `stage_1_result` as a new per-call
input two phases after AESIC-REQ-023/121 were last touched. This mirrors
exactly the structure of Phase 147L.2's own finding against Phase 147L.1
(a new mechanism interacting badly with an adjacent, correctly-untouched
requirement) — this verification considers that structural parallel
material enough to report as a finding rather than defer.

---

## 19. Recommended Next Phase

Per this phase's own authorizing prompt §20: a Major finding (Finding A)
remains, so this report does **not** recommend proceeding directly to
147M. Consistent with the 147L.2 → 147L.3 precedent, this report
recommends:

**147L.5 — AESIC-001 Idempotency/Stage-1-Embedding and Restart-Matrix
Completeness Repair.** That phase should be narrowly scoped to exactly
Finding A and Finding B above: (a) resolve the AESIC-REQ-057 vs.
AESIC-REQ-023(a)/121 contradiction, most likely by extending
AESIC-REQ-121's equality procedure to account for `stage_1_outcome_ref`
presence/content, or by an explicit, disclosed carve-out in AESIC-REQ-057's
own text — either way, following this project's own established practice
of selecting the candidate that best preserves the guarantee's original
stated purpose over one that merely relabels the gap; and (b) add one new
restart-matrix row to §11.2 naming the crash-between-AER-commit-and-
pointer-write point and its (already independently derived, in §17 above)
retry-based resolution. It should remain a contract-repair-only phase —
no implementation, no schema, no runtime change — mirroring Phase 147L.1's
and Phase 147L.3's own scope discipline. A subsequent 147L.6 independent
verification of that repair, mirroring this same
verification-then-repair-then-re-verification discipline, would then be
the natural gate before 147M.

**This recommendation is not an authorization.**

---

**End of Phase 147L.4 Independent Verification.**
