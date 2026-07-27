# Phase 145H.1 — Post-Consumption Readiness Uniqueness Contract Clarification

**Status:** Complete (architecture/contract-clarification phase only; no
production code modified; no runtime-capability change; no repair
performed).
**Mode:** Governed contract-clarification phase, per this phase's own
governing prompt, independently re-deriving Blocking Finding H-1's
contractual cause from primary text rather than trusting Phase 145H's own
conclusions, then freezing exactly one normative post-consumption
readiness behavior.
**Governing authority (consulted, this phase's own basis):** IWC-001
v1.2, IWPC-001 v1.3 (revised in place by this phase to v1.4), PEC-001
v1.1, CHGR-001 v1.0, PROJECT_STATUS.md, `docs/PHASE_145H_INTERACTIVE_WORKFLOW_CHAPTER_INDEPENDENT_CERTIFICATION.md`.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Repair authority exercised:** None. This phase is architecture and
contract-clarification only, per its own governing prompt's explicit
No-Go list. Blocking Finding H-1 remains open.

---

## 1. Independent re-derivation of H-1's contractual cause

Before consulting Phase 145H's own conclusions as anything but leads, this
phase independently re-read IWC-001 v1.2, IWPC-001 v1.3 (full text, not
summary), PEC-001 v1.1, and CHGR-001 v1.0, and independently re-derived the
uniqueness boundary those four contracts jointly impose:

- **IWC-REQ-019** (IWC-001 §10.1/§7): Confirmation is a distinct,
  non-repeatable act; a session yields at most one confirmed Human
  Decision.
- **IWC-REQ-024** (IWC-001 §4.9): a session identifier, once terminal, is
  never reused for a new interaction.
- **CHGR-001 §2 / CHGR-REQ-001**: a CHGR is, by definition, the
  representation of "one" Human Governance Act — singular.
- **IWPC-REQ-024** (IWPC-001 v1.3, unrevised): readiness construction is
  "idempotent by key, keyed on `session_id`," described without any
  stated post-consumption exception.
- **IWPC-REQ-082/107** (IWPC-001 v1.3, unrevised): "one **pending**
  package per session" — textually scoped to the pending state, an
  ambiguity independently reconfirmed genuine (§2 below).
- **PEC-REQ-007/041/080** (PEC-001 v1.1): the one airtight replay guard
  that exists is correctly scoped to `package_id`, not `session_id` —
  PEC-001 was never asked, and is not equipped, to reason about
  session-level uniqueness.

This independently reproduces Phase 145H's own §6.1/§6.5 conclusion: the
weight of contractual evidence forecloses a second, independently
publishable package for an already-published session, but no contract
text says so explicitly. **The primary root cause is a genuine
implementation defect** (`FilesystemPendingReadinessStore.
find_by_session_id`'s own docstring-disclosed "never return a `consumed/`
record" design, independently confirmed at
`src/pcae/interactive_workflow/persistence/filesystem_pending_readiness_store.py:505-518`,
which Phase 145G.1 wired into real construction power via
`PublicationApplicationService.ensure_readiness_package`/
`persist_readiness_package`, confirmed at
`src/pcae/interactive_workflow/application/publication_service.py:122-124,
158-185`, without re-checking that wiring against IWPC-REQ-024's
unqualified text). **A secondary, real contract-drafting gap independently
exists** in IWPC-REQ-082/107's pending-scoped language, which is what this
phase closes.

## 2. Contract-gap classification

Classified as: **missing normative requirement** (no `IWPC-REQ-###`
anywhere stated the required post-consumption behavior) and **missing
cross-contract uniqueness statement** (CHGR-001 §2 states the required
conclusion one layer downstream of where the gap actually lived — the
CLI/transport readiness-construction boundary IWPC-001 alone owns). Not
classified as: incomplete replay semantics (PEC-001's `package_id`-scoped
guard is correct and sufficient once the session-level gap is closed one
layer earlier — §6 below), incomplete persistence semantics (atomic-write
and disposition-move mechanics are independently correct; only the
idempotency-*lookup scope* was wrong), ambiguous terminology (every term
in play is already precisely defined), or incomplete recovery semantics
beyond the narrow, already-disclosed IWPC-REQ-154 window (restated
unchanged, §7 below).

**Primary defect vs. secondary gap, distinguished:** the implementation
defect would remain a defect under even the strictest reading of the
pre-clarification text (IWPC-REQ-024's *unqualified* half already argued
against the observed behavior); the contract's own ambiguity is why the
defect survived five independent-verification passes (145G.1 through
145G.3V) unchallenged, not why the defect exists. Closing the ambiguity,
as IWPC-001 v1.4 now does, removes the excuse for recurrence; it does not
itself repair the code.

## 3. Alternatives analysis

Three candidate post-consumption behaviors were evaluated on independent
primary-text analysis (full reasoning: IWPC-001 v1.4 §35.3):

- **Option A — return the original, consumed package's identity
  unchanged.** Preserves IWPC-REQ-024's existing idempotency guarantee
  exactly; requires no new transport shape, since `readiness`'s own
  frozen output contract (IWPC-REQ-023) already names `"consumed"` as a
  designed disposition value the implementation simply never reached.
- **Option B — reject with a new domain error.** Would narrow an existing
  unqualified guarantee (IWPC-REQ-024), requiring a major version bump
  per IWPC-REQ-191, not the additive clarification this gap warrants;
  discards operationally useful information for no contractual reason.
- **Option C — a distinct "publication-completed" result shape.** Would
  duplicate a schema IWPC-REQ-023/054 already assign to `readiness`,
  inventing a new caller-visible branch with no architectural
  justification.

**Selected: Option A**, independently confirming — not merely deferring
to — the governing prompt's own stated preference. Full analysis: IWPC-001
v1.4 §35.3.

## 4. The uniqueness invariant (frozen)

`session_id` is confirmed as the sole readiness uniqueness key, sufficient
without a new identifier (per IWC-REQ-019/024, a session yields at most
one Confirmation, hence at most one Human Governance Act). The complete
invariant, IWPC-REQ-197, freezes: one readiness identity per confirmed
decision; one successful authoritative publication per Human Governance
Act; one authoritative CHGR per Human Governance Act; one successful
publication result for a given readiness identity; and no new readiness
package after authoritative publication of the same confirmed decision —
explicitly preventing the exact `A → publish A → B → publish B → two
CHGRs` sequence 145H demonstrated. Full text: IWPC-001 v1.4 §35.4.

## 5. Post-consumption readiness behavior (the repair)

IWPC-REQ-024, IWPC-REQ-082, and IWPC-REQ-107 are corrected in place
(additive drafting-gap repair, mirroring the Phase 145C precedent at
IWPC-001 §32 — no narrowing, no renumbering) to extend the existing
idempotent-by-`session_id` construction guarantee across a package's
**entire lifecycle**, not merely its pending state. Two new requirements
freeze the mechanism: **IWPC-REQ-198** requires the session-keyed lookup
to search both the pending and `consumed/` locations; **IWPC-REQ-199**
requires `readiness`, invoked post-consumption, to return the existing
package's identity/metadata (including `disposition: "consumed"` and
`record_id` where available) unchanged, never constructing a new package.
**IWPC-REQ-200** confirms no new `error_type`, exit code, or transport
shape is required — the fix reaches an output value (`"consumed"`) the
contract already defined. Full text: IWPC-001 v1.4 §35.5.

## 6. Publication replay — upstream invariant

PEC-001's `package_id`-scoped replay guard (PEC-REQ-007/041/080,
IWPC-REQ-032/113) is confirmed sufficient and is left unrevised. It is
sufficient **if and only if** exactly one `package_id` is ever minted per
session for the session's entire lifetime — which IWPC-REQ-197 now
guarantees. This is stated explicitly as **IWPC-REQ-201**, the upstream
invariant PEC-001's own text always implicitly assumed without ever being
required to state it, because the session-level question was never
PEC-001's to answer (PEC-001 §1: "does not redefine ... IWC-001"). No
PEC-001 revision was made; §9 below documents why existing text is
sufficient.

## 7. Failed and partial publication

**IWPC-REQ-202** restates IWPC-REQ-089 unchanged: a failed `publish`
leaves the package `pending`; no new behavior. **IWPC-REQ-203** restates
IWPC-REQ-154 unchanged and classifies the narrow interruption window
between PEC-001's successful commit and the store's disposition move as a
disclosed, pre-existing, Non-Blocking eventual-consistency gap — not H-1,
and not reintroduced by this revision, because a `publish` retry in that
window is still caught by PEC-001's own replay check regardless of what
`readiness` currently reports. This phase does not close that window
(closing it would require a cross-store transaction beyond this phase's
additive, contract-only scope, and beyond its own No-Go list).

## 8. Backward compatibility and historical inconsistency

**IWPC-REQ-204**: a repository already carrying more than one readiness
record for a single `session_id` (produced by the pre-145H.1 defective
implementation) is a historical inconsistency that a future
implementation's session-keyed lookup MUST fail closed on
(`persistence_corrupt`, no new error type), never silently resolve by
selecting one record. This phase repairs no existing duplicate record and
authorizes no migration tooling. **IWPC-REQ-205**: a repository with
exactly one record per session (the common case) requires no migration —
this is a lookup-scope correction, not a persisted-format change; no field
is added to or removed from any persisted schema.

## 9. Cross-contract review

- **IWC-001** — existing text sufficient, no revision. IWC-REQ-019/024
  already establish "at most one Human Governance Act per session"; IWC-001
  has no jurisdiction over the Pending-Readiness Store, a concept IWPC-001
  itself introduces (IWPC-001 §3: "not an IWC-001 or PEC-001 concept").
- **PEC-001** — existing text sufficient, no revision. §6 above states the
  upstream invariant explicitly; the session-level uniqueness question was
  always exclusively IWPC-001's to answer.
- **CHGR-001** — existing text sufficient, no revision. §2's "one Human
  Governance Act" language already states the required invariant at the
  definitional level; CHGR-001 has no operational hook into the
  pre-publication layer where H-1 actually occurred (CHGR-001 §1: "does
  not govern the Interactive Decision Session layer itself").

No contract other than IWPC-001 required revision; each of the above is
documented with its own reasoning rather than asserted.

## 10. Normative readiness behavior matrix

The complete matrix (IWPC-REQ-206) is reproduced in IWPC-001 v1.4 §35.9,
covering: no package exists; matching pending package exists; matching
consumed package exists (new — the H-1 case, now closed); prior failed
publication; the IWPC-REQ-154 interruption window; wrong/missing
identity; session not yet confirmed; session terminal before confirmation;
multiple matching historical records (fail closed); and corrupted
records (fail closed). No row introduces a new `error_type` or exit code.

## 11. Security restatement

IWPC-REQ-207 confirms this revision introduces no new bypass, force flag,
or automatic behavior: `readiness` remains read/idempotent-construction
only; `publish` remains the sole authorizing act; identity enforcement
continues to run before every idempotent/cache-hit branch, including the
newly-reachable consumed-package branch, independently confirmed already
covered by `ensure_readiness_package`'s existing
identity-check-before-cache-check ordering
(`publication_service.py:158-185`). A changed `package_id` cannot produce
a duplicate CHGR because IWPC-REQ-197 now guarantees no second `package_id`
is ever minted for the same session — the mechanism, not merely a
restated goal.

## 12. Traceability

Every requirement added or amended (IWPC-REQ-197 through IWPC-REQ-209,
plus the in-place corrections to IWPC-REQ-024/082/107) traces to H-1
directly; no unrelated cleanup was performed. Full matrix: IWPC-001 v1.4
§35.12. Expected future implementation owner: a narrowly scoped repair
phase against `FilesystemPendingReadinessStore.find_by_session_id`,
`PublicationApplicationService.ensure_readiness_package`/
`persist_readiness_package`, and `decision_session.py`'s `readiness`
handler. Expected verification evidence: a repaired-behavior test
exercising the exact "readiness → publish → readiness again" sequence
145H's own live adversarial testing used to find H-1, plus the
historical-multiple-record fail-closed case.

## 13. Contract consistency verification

Independently checked before finalization: requirement numbering (new
identifiers begin at IWPC-REQ-197, sequential, no gaps, no reuse — the
three in-place corrections keep their original numbers per the 145C
precedent); version references (contract header updated 1.3 → 1.4 with an
explicit revision-history entry, mirroring §32–34's own format exactly);
cross-references (every `IWPC-REQ-###`/`IWC-REQ-###`/`PEC-REQ-###`/
`CHGR-REQ-###` citation in the new §35 resolves to text that exists at the
cited contract/section); terminology consistency (no new synonym for
"pending"/"consumed"/"session_id"/"package_id" introduced); state-table
and behavior-matrix consistency (the new §35.9 matrix does not contradict
the existing §20 Idempotency Contract table — it restates `readiness`'s
own row with its previously-unstated full scope, not a different rule);
error-table consistency (§19.1's closed 24-member taxonomy is unchanged —
zero new members); no accidental authorization of implementation work (the
No-Go list at §14 below is explicit); no contradiction with
identity-bound-resumption requirements (§34's ordering discipline is
independently reconfirmed unweakened, §11 above).

## 14. No-Go Confirmation

No production code was modified. No file under `src/` was modified. No
file under `tests/` was modified. `docs/contracts/
INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md` is the only
contract file modified (IWPC-001 → v1.4); IWC-001, PEC-001, and CHGR-001
were read only, not modified — each independently confirmed to require no
revision (§9). No `PublicationApplicationService`, no
`PublicationCoordinator`, and no persistence adapter was touched. No
migration tooling was created. No new runtime capability was created; no
identity was inferred; no automatic publication, automatic authorization,
force flag, or bypass flag was added. No historical duplicate record was
repaired. H-1 is **not** closed and is **not** certified by this phase —
it remains open, pending a future, separately governed implementation
phase. This phase does not begin, and does not authorize, 145H.2, 145H.3,
145H.4, 145I, Phase 146, or any production repair.

## 15. Governance validation

- `pcae check` — passed.
- `pcae health` — healthy.
- `pcae doctor task-memory check` — clean.
- `pcae runtime inspect --json` — Observed / observe / unavailable,
  confirmed unchanged before and after this phase.
- Contract cross-reference/requirement-numbering validation — performed
  manually per §13 above (no automated contract-linter exists in this
  repository beyond the existing `bootstrap_todo_consistency`-style
  documentation-consistency tests, which are PROJECT_STATUS.md/TODO.md
  scoped, not contract-text scoped).

## 16. Exit criteria — self-assessment

1. H-1 independently re-derived from primary contracts and current
   behavior — §1. ✅
2. Contract-drafting gap precisely classified — §2. ✅
3. Exactly one post-consumption readiness behavior selected — §3, §5. ✅
4. Readiness uniqueness key explicit and operationally enforceable —
   §4 (IWPC-REQ-197, `session_id`). ✅
5. One-Human-Governance-Act uniqueness invariant explicit — §4. ✅
6. Readiness replay before and after publication fully specified — §5,
   §10. ✅
7. Publication replay cannot be bypassed by changing `package_id` — §6
   (IWPC-REQ-197 + IWPC-REQ-201). ✅
8. Failed and partial publication recovery semantics specified — §7. ✅
9. Consumed readiness discoverability semantics specified — §5
   (IWPC-REQ-198/199). ✅
10. Historical inconsistent states fail closed — §8 (IWPC-REQ-204). ✅
11. Identity-enforcement ordering preserved — §11. ✅
12. IWPC-001 revised additively to v1.4 — done. ✅
13. Cross-contract revision minimal and justified — §9 (none required,
    each documented). ✅
14. Contract cross-reference checks pass — §13, §15. ✅
15. No production code changes — §14. ✅
16. Runtime remains Observed/observe/unavailable — §15. ✅
17. H-1 remains open pending implementation and verification — §14. ✅
18. This canonical report is complete and consistent. ✅

## 17. Recommendation (not authorized by this report)

**145H.2 — Post-Consumption Readiness Uniqueness Implementation Repair**,
against `FilesystemPendingReadinessStore.find_by_session_id`,
`PublicationApplicationService.ensure_readiness_package`/
`persist_readiness_package`, and the `readiness` CLI handler, per
IWPC-001 v1.4 §35's now-frozen normative requirements. This report does
not authorize 145H.2, 145H.3, 145H.4, 145I, Phase 146, or any production
repair.
