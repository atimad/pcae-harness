# PEC-001 v1.0 — Publication Execution Contract

## Contract identity and status

**Contract:** PEC-001
**Version:** 1.1
**Status:** FROZEN
**Frozen by:** Phase 144B — Publication Execution Contract Freeze
**Revised by:** Phase 144E — Publication Execution Contract Revision (§20
below; additively describes how the Coordinator consumes IWC-001 v1.2's
widened Publication Readiness Package to close the provenance-boundary
gap Phase 144D's F-1/JC-2 independently demonstrated; no semantic
narrowing of any existing provision)
**Architecture basis:** Phase 144A — Publication Execution Ownership
Architecture, GLP-001 §6.1 Stage 1 — Architecture
(`docs/PHASE_144A_PUBLICATION_EXECUTION_OWNERSHIP_ARCHITECTURE.md`)
**Governed subject:** **Publication Execution** — the previously-unassigned
architectural gap named by IWC-001 §18.4 (`IWC-REQ-171`) and CHGR-001 §20.5:
which concrete component realizes CHGR-001 §20's "System, atomically and
immediately following Confirmation, performing no discretionary act" row
for Publication, what triggers it, and under what authorization,
determinism, failure, and ownership discipline it operates.

PEC-001 v1.0 is the sole normative authority governing the **Publication
Coordinator**, the **Publication Authorization Event**, and **Publication
Execution** as newly-named concepts. It does not redefine, narrow, or
supersede IWC-001 or CHGR-001; it fills exactly the gap those two contracts
each independently and deliberately left open (IWC-001 §18.4, CHGR-001
§20.5), per their own stated precondition that the responsibility may be
assigned only "once the Publication Handoff is itself separately
architected and authorized" (IWC-001 §18.4) — the architecture Phase 144A
performed. Every IWC-001 and CHGR-001 section this contract cites is cited
to demonstrate compatibility with an already-frozen provision, never to
amend it. This contract does not touch TAMC-001, TAMPC-001, the Canonical
Phase Finalization Architecture (Phase 134), the Canonical Lifecycle State
Authority Architecture (Phase 135), or the Governance Lifecycle Pattern
Architecture/Contract (Phase 137V, GLP-001) — all four are independently
reconfirmed unrelated or already-compatible in §13 below.

Phase 144A's Architecture stage is the approved design basis for every
section below. This contract independently re-derives every requirement
directly from `docs/PHASE_144A_PUBLICATION_EXECUTION_OWNERSHIP_ARCHITECTURE.md`,
treated as evidence of architectural intent, never as contractual
authority; from direct re-reading of `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`
(IWC-001 v1.1) and `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
(CHGR-001 v1.0), each treated as independent normative authority this
contract must remain compatible with; and from
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` (TAMC-001)
and `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(TAMPC-001), read directly for §13's compatibility analysis rather than
assumed from 144A's own summary of them. Where Phase 144A left a design
question open for this contract to resolve, this contract resolves it
explicitly and discloses the resolution as a ratification, not a silent
default (see §6 below, ratifying 144A §5's Model 2 recommendation).

This is contract text only. It does not implement `PublicationCoordinator`
or any other class, does not implement any CLI command, does not implement
any CHGR-writing machinery, does not create any CHGR, does not modify
`src/pcae/interactive_workflow/**`, does not modify any Typed Authority
Model or PCAE phase-lifecycle machinery, and does not perform, or
constitute evidence of, any act of Publication. It preserves every
provision of IWC-001, CHGR-001, TAMC-001, and TAMPC-001, unchanged. Runtime
remains Observed / observe / unavailable throughout every operation this
contract governs.

## 0. Normative Language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative, with the meanings given in
GLP-001 §0, which this contract adopts unchanged.

This contract does not itself perform, and is not evidence of, any act of
publishing, authorizing, or executing Publication. No provision below
authorizes a future implementation phase to begin merely by this
contract's own freeze; §9 and the Non-Goals below state this explicitly.

Every mandatory obligation below is stated in §17 as a single, atomic,
independently identified `PEC-REQ-###` requirement. Sections 1–16 state the
normative rules in narrative form; §17 is the authoritative, falsifiable
enumeration of those rules. Where narrative prose in §1–§16 and a
requirement in §17 differ in force, §17 is normative.

---

## 1. Purpose

**Publication Execution** is the previously-unassigned act of realizing
CHGR-001 §8's atomic Publication act in concrete software: given a
`Confirmed` Decision Session's `PublicationReadinessPackage` (IWC-001
§11.4) and an explicit, separately-obtained authorization, performing the
write, canonical-identity assignment (CHGR-001 §9), and provenance/
integrity capture (CHGR-001 §10) that constitute a CHGR's creation.

This contract exists to convert Phase 144A's evidence-derived architecture
into binding, falsifiable `SHALL`/`SHALL NOT` obligations, per GLP-001
§6.1 Stage 2's own definition, applied here to the ownership gap IWC-001
§18.4 and CHGR-001 §20.5 each left open — mirroring exactly how Phase 143B
converted Phase 143A into CHGR-001.

Publication Execution, as this contract defines it, is formally distinct
from every adjacent artifact class or subsystem this repository already
governs:

- It is distinct from **Publication itself** (CHGR-001 §8), which is the
  already-frozen definition of *what* the act does; this contract assigns
  *who performs it*, *what triggers it*, and *under what determinism and
  failure discipline*, without redefining CHGR-001 §8's own text.
- It is distinct from the **Publication Handoff** (IWC-001 §2, §11.4),
  which is the already-frozen boundary at which a `Confirmed` session's
  responsibility ends; this contract governs only what happens on the far
  side of that boundary.
- It is distinct from **PCAE phase/task completion lifecycle** (Phase
  134/135/137V, `pcae phase complete`), an independently confirmed
  unrelated domain (144A §2.5, IWC-001 §11.1, CHGR-001 §19).
- It is distinct from the **Typed Authority Model / CLTR migration
  "publication"** (TAMC-001, TAMPC-001), an independently confirmed,
  structurally disjoint artifact family (144A §2.5, IWC-001 §19.1,
  CHGR-001 §19.1).
- It is distinct from **backend-output-adoption lifecycle**
  (`src/pcae/lifecycle.py`, Phase 80A), an independently confirmed
  unrelated domain (144A §2.5).

## 2. Definitions

**PEC-REQ-001.** **Publication Coordinator** — the single, named component
that performs Publication Execution: given one already-built,
already-validated `PublicationReadinessPackage` and one valid Publication
Authorization Event, performs exactly CHGR-001 §8's atomic act.

**PEC-REQ-002.** **Publication Readiness** — the technical fact, computed
solely from a `PublicationReadinessPackage`'s own content, that the
package is complete and internally consistent (`is_ready() == True` per
144A §5). Readiness is a property of data, never of authority.

**PEC-REQ-003.** **Publication Authorization** — the governance fact that
a human or human-designated act has explicitly permitted the Publication
Coordinator to act now, on a specific, identified `PublicationReadinessPackage`.
Authorization is a discrete event, never a persistent state, and is
distinct from, and never inferable from, Readiness.

**PEC-REQ-004.** **Publication Authorization Event** — the concrete,
auditable occurrence that constitutes Publication Authorization: an
explicit human-operated invocation of a dedicated CLI command, per §6
below.

**PEC-REQ-005.** **Publication Execution** — the Publication Coordinator's
single act of consuming one `PublicationReadinessPackage` and one
Publication Authorization Event to perform CHGR-001 §8's atomic write,
identity assignment, and provenance/integrity capture.

**PEC-REQ-006.** **CHGR Boundary** — the point at which Publication
Execution's atomic write brings a CHGR into existence under CHGR-001
§13.1's lifecycle model; the last architectural act this contract governs
and the first act CHGR-001's own record-lifecycle discipline governs.

**PEC-REQ-007.** **Replay** — a second or subsequent invocation of the
Publication Coordinator naming a `package_id` or `session_id` that has
already been consumed by a completed Publication Execution.

**PEC-REQ-008.** **Idempotency check** — the Publication Coordinator's
single-entry-point verification, prior to any write, that the named
`package_id`/`session_id` has not already been published.

## 3. Core Invariants

The following nine properties are frozen as mandatory, non-negotiable, and
immutable for every Publication Coordinator implementation, regardless of
invocation surface or future extension. None is invented by this contract;
each is independently re-derived from Phase 144A's architecture and from
IWC-001's and CHGR-001's own core invariants, restated here at the
Publication Execution layer.

**PEC-REQ-009.** Readiness is never Authorization. A complete, internally
consistent `PublicationReadinessPackage` establishes only Readiness (§2
above; 144A §5).

**PEC-REQ-010.** The Publication Coordinator SHALL NEVER infer
Authorization from Readiness, from a session reaching `Confirmed`, or from
any other fact the Coordinator can observe on its own.

**PEC-REQ-011.** No automatic publication SHALL occur. Reaching `Confirmed`
is necessary but never sufficient to publish (144A §5).

**PEC-REQ-012.** No publish-when-ready behavior SHALL exist anywhere in the
Coordinator's design; a complete package SHALL remain unpublished
indefinitely absent a Publication Authorization Event.

**PEC-REQ-013.** One-owner-per-responsibility SHALL hold: the Publication
Coordinator is the sole owner of Publication Execution, duplicating no
existing owner and ceding no part of its responsibility to another
component.

**PEC-REQ-014.** Authority neutrality SHALL hold: the Coordinator inherits
no ambient authority from any calling component; it acts only on an
explicit Publication Authorization Event it independently verifies.

**PEC-REQ-015.** Fail-closed behavior SHALL hold: absence, ambiguity, or
invalidity of either the package or the authorization event SHALL result
in no publication, never a best-effort or benefit-of-the-doubt default.

**PEC-REQ-016.** Deterministic sequencing SHALL hold: given the same valid
package and the same valid authorization event, Publication Execution
SHALL produce the same CHGR-001 §8 write outcome every time, with no
discretionary step.

**PEC-REQ-017.** Immutable publication evidence SHALL hold: once
Publication Execution completes, the written CHGR is subject only to
CHGR-001 §13's own supersession/suspension/revocation discipline, never to
the Coordinator's own subsequent action.

---

## 4. Publication Coordinator Contract

**PEC-REQ-018.** The Publication Coordinator SHALL be a component external
to `src/pcae/interactive_workflow/**`, preserving IWC-001 §1's frozen rule
that a Decision Session never itself constitutes Publication and preserving
Phase 143O's AST-enforced import boundary.

**PEC-REQ-019.** The Publication Coordinator SHALL be external to the PCAE
phase/task lifecycle tree (`finalization_transaction.py`, agent-lock
machinery), preserving the Phase 134/135 "unrelated domain" classification.

**PEC-REQ-020.** The Publication Coordinator SHALL be external to
`src/pcae/cltr/**` and any other Typed Authority Model / CLTR machinery,
preserving TAMC-001's and TAMPC-001's independently confirmed disjointness
from CHGR (IWC-001 §19.1, CHGR-001 §19.1).

**PEC-REQ-021.** The Publication Coordinator's sole responsibility SHALL be:
given one already-built, already-validated `PublicationReadinessPackage`
and one valid Publication Authorization Event, to perform CHGR-001 §8's
atomic write, canonical identity assignment (CHGR-001 §9), and provenance/
integrity capture (CHGR-001 §10) in the same atomic operation.

**PEC-REQ-022.** The Publication Coordinator SHALL own no responsibility
beyond §21 above. In particular, it SHALL NOT determine transition
legality, evidence sufficiency, clarification completeness, Preview Digest
correctness, or Confirmation validity — all already owned inside
`interactive_workflow/**` and already re-verified by `PublicationHandoff`'s
own cross-reference checks before a package is ever built.

**PEC-REQ-023.** The Publication Coordinator SHALL NOT decide when or
whether to trigger itself (§6 below governs invocation exclusively).

**PEC-REQ-024.** The Publication Coordinator SHALL NOT perform any PCAE
phase/task lifecycle action, including `pcae phase complete`, agent-lock
acquisition or release, or phase-completion notification delivery.

**PEC-REQ-025.** The Publication Coordinator SHALL NOT perform any Typed
Authority Model or CLTR action.

**PEC-REQ-026.** The Publication Coordinator SHALL NOT perform supersession,
suspension, or revocation of an already-published CHGR; CHGR-001 §13
reserves that act exclusively to an eligible Human Authority acting under
the record's own governing template.

**PEC-REQ-027.** The Publication Coordinator's package placement, as a new
sibling package to `interactive_workflow` (e.g. `src/pcae/governance/publication/`),
is ratified as architectural naming; a future implementation phase MAY
rename the package without requiring a further contract revision, provided
`PEC-REQ-018`–`PEC-REQ-020`'s placement boundaries are preserved in
substance.

---

## 5. Authority Contract

**PEC-REQ-028.** This contract freezes as its governing principle:
**Publication Readiness is never Publication Authorization.**

**PEC-REQ-029.** A `Confirmed` session and a complete
`PublicationReadinessPackage` SHALL establish only technical readiness, per
§3 above.

**PEC-REQ-030.** Publication SHALL require a separate, explicit
Authorization Event, distinct from and subsequent to Confirmation.

**PEC-REQ-031.** The Publication Coordinator SHALL NEVER infer
Authorization from any fact it can observe about the package or the
session that produced it.

**PEC-REQ-032.** No agent, including one producing a future implementation
of this contract, SHALL treat this contract, or any implementation of it,
as self-authorizing that agent to mint, confirm, or publish a CHGR on a
human's behalf — restating CHGR-001 §17's frozen prohibition unchanged, one
layer earlier, at the Coordinator's own invocation boundary.

**PEC-REQ-033.** Publication Authorization, once consumed by a completed
Publication Execution, SHALL NOT be reusable for a second act (§7's replay
rejection); it is one-shot, mirroring CHGR-001 §7/§8's identical treatment
of Confirmation and Publication.

---

## 6. Authorization Event Contract

**PEC-REQ-034.** The Publication Authorization Event SHALL originate from
an explicit, human-operated invocation of a dedicated CLI command (e.g.,
`pcae governance-record publish <package-id>`), ratifying Phase 144A §5's
Model 2 as the minimum viable authority boundary.

**PEC-REQ-035.** Autonomous, self-triggering invocation of the Publication
Coordinator (144A §5 Model 1 — the Coordinator watching for sessions
reaching `Confirmed` and publishing without further human action) is
excluded outright. No implementation of this contract SHALL introduce it.

**PEC-REQ-036.** The CLI layer invoking the Coordinator SHALL be a thin
invocation surface only; it SHALL delegate to the Publication Coordinator
class rather than embed Publication Execution logic inline (ratifying 144A
§3 Option D1's retained insight).

**PEC-REQ-037.** The human act of running the authorizing command SHALL
constitute the Authorization Event; it is distinct from, and never
substitutes for, the Confirmation act that produced the underlying
session's `Confirmed` state (IWC-001 §10).

**PEC-REQ-038.** Required evidence for a Publication Authorization Event
SHALL include, at minimum: the identity of the operator who invoked the
command, the timestamp of invocation, and the exact `package_id` (or
equivalent unique reference) named.

**PEC-REQ-039.** Timing: a Publication Authorization Event SHALL be
evaluated only against a `PublicationReadinessPackage` that is, at
evaluation time, complete per `is_ready() == True`; an event naming an
incomplete package SHALL be refused.

**PEC-REQ-040.** Invariant: a Publication Authorization Event SHALL name
exactly one `PublicationReadinessPackage`; it SHALL NOT authorize a class,
batch, or future set of packages.

**PEC-REQ-041.** Idempotency: a Publication Authorization Event naming a
`package_id`/`session_id` that has already been consumed by a completed
Publication Execution SHALL be refused as a Replay (§2 above), never
silently accepted as a no-op success.

**PEC-REQ-042.** Replay handling: the Publication Coordinator SHALL reject
a Replay at its single entry point, before any write is attempted, per
§8's idempotency check.

**PEC-REQ-043.** Auditability: every Publication Authorization Event,
whether accepted or refused, SHALL be retained as part of the resulting
CHGR's provenance (if accepted) or as an independently retrievable refusal
record (if refused); no Authorization Event SHALL be evaluated and
discarded without a trace.

**PEC-REQ-044.** The Publication Authorization Event SHALL be external to
Interactive Workflow: no component under `src/pcae/interactive_workflow/**`
SHALL originate, evaluate, or record it.

**PEC-REQ-045.** The Publication Authorization Event SHALL NEVER be
synthesized by software; only an explicit act by a human operator, or a
human-designated delegated-authorization-token mechanism (144A §5 Model 3,
reserved as a future hardening layer, not adopted by this contract) SHALL
constitute it.

**PEC-REQ-046.** This contract adopts Model 2 (CLI-operator invocation) as
sufficient for v1.0; Model 3 (a separate, typed, CHGR-scoped authorization
artifact, independently verifiable and independently revocable) is named
as a permitted future hardening extension per §14, not a requirement of
this contract.

---

## 7. Publication Execution Contract

**PEC-REQ-047.** Publication Execution SHALL be deterministic: given the
same valid `PublicationReadinessPackage` and the same valid Authorization
Event, the write outcome SHALL be the same every time.

**PEC-REQ-048.** Input validation: the Coordinator SHALL validate, before
any write, that the package it received is the exact, unmodified output of
`PublicationHandoff.build_package`/`serialize`, per
`interactive_workflow/serialization/publication_handoff_schema.py`'s
already-frozen shape.

**PEC-REQ-049.** Precondition: the Coordinator SHALL refuse to act on any
package for which `is_ready() == True` does not hold.

**PEC-REQ-050.** Precondition: the Coordinator SHALL refuse to act absent
a valid Publication Authorization Event per §6.

**PEC-REQ-051.** Execution ordering: the idempotency/replay check (§8)
SHALL be performed first, before package validation; package validation
SHALL be performed before the atomic write; the atomic write SHALL be
performed before completion reporting.

**PEC-REQ-052.** Failure handling: any precondition failure (missing
authorization, invalid package, replay) SHALL terminate the attempt with no
partial effect and no CHGR created.

**PEC-REQ-053.** Rollback behavior: because Publication (CHGR-001 §8) is a
single atomic operation, rollback SHALL be binary — either the atomic write
completed (canonical identity assigned, record immutable) or it did not
happen at all; no intermediate or partially-written state SHALL be
observable to any caller or to storage.

**PEC-REQ-054.** Atomicity: canonical identity assignment (CHGR-001 §9) and
provenance/integrity capture (CHGR-001 §10) SHALL occur within the same
atomic operation as the write itself, per CHGR-001 §8's unmodified text.

**PEC-REQ-055.** Completion conditions: Publication Execution SHALL be
considered complete only once the CHGR exists in canonical storage with its
identity assigned and its provenance/integrity evidence captured; a partial
write SHALL NOT be reported as complete.

**PEC-REQ-056.** The Coordinator SHALL report completion (or failure)
deterministically and SHALL NOT leave a caller unable to determine, from
the Coordinator's own output, whether the CHGR was created.

**PEC-REQ-057.** The Coordinator SHALL perform no discretionary step, per
CHGR-001 §8's "no discretionary step" requirement restated unchanged at
this layer.

---

## 8. Publication Readiness Package Contract

**PEC-REQ-058.** The Publication Coordinator's sole input SHALL be a
`PublicationReadinessPackage` (or its serialized form), unmodified from
`interactive_workflow`'s own frozen shape (IWC-001 §11.4, 143O).

**PEC-REQ-059.** Required fields, unchanged from the existing
`PublicationHandoff.build_package` output: the bound template reference,
captured decision content, exact Preview and Preview Digest, and
Confirmation evidence.

**PEC-REQ-060.** The package SHALL remain immutable from the moment
`PublicationHandoff.build_package` produces it through Publication
Execution; the Coordinator SHALL NOT mutate any field of the package it
receives.

**PEC-REQ-061.** The package SHALL remain authority-neutral: it SHALL
carry no authority token, no field asserting Publication Authorization,
and no field the Coordinator could mistake for an Authorization Event.

**PEC-REQ-062.** The package SHALL remain publication-neutral: it SHALL
carry no publication-state field and no field indicating whether
Publication has already occurred.

**PEC-REQ-063.** Prohibited fields: the package SHALL NEVER contain an
authority token, a publication decision, a CHGR identifier, or execution
state — restating IWC-001 §11.4's and 144A §3's existing "no
publication-state field, no publication-result field, no CHGR identifier
field, and no authority-token field" guarantee unchanged.

**PEC-REQ-064.** The Coordinator SHALL treat any package found to carry a
prohibited field (§63 above) as invalid and SHALL refuse to act on it,
per the fail-closed invariant (§3 above).

**PEC-REQ-065.** The package's shape SHALL remain the sole responsibility
of `interactive_workflow/**`'s own serialization module; the Coordinator
SHALL NOT define, extend, or reinterpret the package's schema.

---

## 9. CHGR Boundary Contract

**PEC-REQ-066.** The Publication Coordinator MAY create a CHGR, atomically,
per §7 above.

**PEC-REQ-067.** The Publication Coordinator SHALL NOT authorize
publication; authorization is established exclusively by a Publication
Authorization Event per §6, evaluated and verified before the Coordinator
acts, never granted by the Coordinator itself.

**PEC-REQ-068.** The Publication Coordinator SHALL NOT determine Publication
Readiness; readiness is established exclusively by
`PublicationHandoff.validate_completeness`/`is_ready()`, already owned
inside `interactive_workflow/**`.

**PEC-REQ-069.** The Publication Coordinator SHALL NOT modify Interactive
Workflow state, code, or data in any way.

**PEC-REQ-070.** The Publication Coordinator SHALL NOT alter Confirmation;
Confirmation is complete, and its evidence frozen, before a package is ever
built (IWC-001 §10).

**PEC-REQ-071.** The Publication Coordinator SHALL NOT mutate evidence;
all evidence the CHGR carries is exactly the evidence the package already
carries, unmodified (§8 above).

**PEC-REQ-072.** CHGR ownership, once created, remains exactly as CHGR-001
§13 and §20 already assign it: supersession, suspension, and revocation
remain owned solely by an eligible Human Authority under the record's own
template, never by the Publication Coordinator.

---

## 10. Responsibility Matrix

**PEC-REQ-073.** The following ownership table SHALL govern; no
responsibility SHALL be duplicated across two rows, and no row SHALL be
left without an owner.

| Responsibility | Owner |
|---|---|
| Decision presentation, evidence assembly, Preview rendering, Confirmation | Interactive Workflow (IWC-001 §5, §6, §10) — unchanged by this contract |
| `PublicationReadinessPackage` construction and completeness validation | Interactive Workflow / `PublicationHandoff` (IWC-001 §11.4) — unchanged |
| Publication Authorization Event origination and evidence | Human operator, via the CLI invocation surface (§6 above) |
| Publication Authorization Event verification (validity, non-replay) | Publication Coordinator, at its single entry point (§6, §8 above) |
| Publication Execution (atomic write, identity assignment, provenance/integrity capture) | Publication Coordinator (§4, §7 above) |
| CHGR record lifecycle after creation (supersession, suspension, revocation) | Eligible Human Authority, under the record's own template (CHGR-001 §13, §20) |
| PCAE phase/task lifecycle bookkeeping | PCAE phase-lifecycle machinery (Phase 134/135/137V) — unrelated domain, untouched |
| Human operator | Originates the Authorization Event (§6); holds no other Publication Execution responsibility |

**PEC-REQ-074.** No responsibility listed in §73's table SHALL be
reassigned, duplicated, or informally exercised by a component other than
the row's named owner.

---

## 11. Failure Semantics

**PEC-REQ-075.** Fail-closed behavior SHALL govern every failure scenario
below: ambiguity or a verification gap SHALL result in refusal to publish,
never a best-effort or benefit-of-the-doubt default.

**PEC-REQ-076.** **Missing authorization** — the Coordinator SHALL refuse
to act and SHALL create no CHGR; the refusal SHALL be reported
deterministically (§7 above).

**PEC-REQ-077.** **Invalid package** — a package failing `is_ready()`, or
found to carry a prohibited field (§8 above), SHALL cause refusal with no
partial write.

**PEC-REQ-078.** **Replay attempt** — an Authorization Event or a package
reference naming an already-published `package_id`/`session_id` SHALL be
refused at the Coordinator's single entry point (§6, §8 above).

**PEC-REQ-079.** **Stale authorization** — an Authorization Event naming a
package that has since become invalid (e.g., its underlying session was
superseded or its template amended in a way `is_ready()` no longer
satisfies) SHALL be refused; the Coordinator SHALL re-verify readiness at
execution time, not merely trust a prior check.

**PEC-REQ-080.** **Duplicate publication** — two concurrent or sequential
attempts naming the same `package_id` SHALL result in exactly one CHGR
created; the second attempt SHALL be refused as a Replay (§78 above), never
silently accepted as a second, redundant success.

**PEC-REQ-081.** **Partial failure** — any failure occurring after the
atomic write begins but before it completes SHALL leave no CHGR in
canonical storage; the write SHALL be all-or-nothing (§7's atomicity
requirement).

**PEC-REQ-082.** **Storage failure** — a failure to persist the CHGR SHALL
be reported as a failed Publication Execution; the Coordinator SHALL NOT
report success while storage has not durably completed the write.

**PEC-REQ-083.** Every failure scenario above SHALL terminate
deterministically: the same failing input, retried unchanged, SHALL
produce the same refusal outcome every time.

**PEC-REQ-084.** No failure scenario listed above, and no failure scenario
this contract does not anticipate, SHALL, through any recovery, retry, or
fallback mechanism, accidentally create a CHGR without a valid Publication
Authorization Event and a valid, ready package.

---

## 12. Security Contract

This contract freezes protections, drawn from Phase 144A's risk analysis
(144A §8) and from CHGR-001 §17's/§18's already-frozen threat posture,
against the following threats. For every scenario below, the default
response to any detected ambiguity or verification gap is to refuse
Publication Execution, fail-closed.

**PEC-REQ-085.** **Authority neutrality** — the Coordinator SHALL derive no
authority from its own existence, its placement in the codebase, or its
having been invoked; authority derives solely from a verified Publication
Authorization Event (§5, §6 above).

**PEC-REQ-086.** **Least privilege** — the Coordinator SHALL depend on
nothing beyond the `PublicationReadinessPackage` boundary and the CHGR-001
§8/§9/§10 write surface (§4's dependency boundary; restating 144A §7
unchanged).

**PEC-REQ-087.** **Replay protection** — restating §78 above: every
Authorization Event and every package reference SHALL be checked for
replay at the Coordinator's single entry point before any write.

**PEC-REQ-088.** **Authorization integrity** — the Coordinator SHALL verify
that a presented Authorization Event was genuinely produced by the
required human-operated invocation surface (§6 above), never accepted from
a caller's own unverified assertion.

**PEC-REQ-089.** **Immutable evidence** — once a CHGR is created, its
substantive fields SHALL never be edited in place by the Coordinator or by
any component this contract governs, per CHGR-001 §13.3 restated unchanged.

**PEC-REQ-090.** **Deterministic execution** — restating §47 above: the
Coordinator's behavior SHALL be fully determined by its two inputs, with no
discretionary step.

**PEC-REQ-091.** **Explicit ownership** — restating §10's responsibility
matrix: no responsibility this contract assigns SHALL be exercised by an
unnamed or informally-assigned component.

**PEC-REQ-092.** **No implicit authority transfer** — invoking the
Coordinator's CLI surface SHALL NOT itself constitute, on the operator's
behalf, any authority beyond the single Publication Authorization Event
that specific invocation produces; it SHALL NOT be treated as a standing
grant for future invocations.

---

## 13. Compatibility Contract

This contract demonstrates compatibility with, and does not redefine,
narrow, or supersede:

**PEC-REQ-093.** **IWC-001** — no section is renumbered, reworded, or
contradicted. §1 (session never publishes), §2/§11.4 (Publication Handoff
boundary), §11.1 (five non-substitutable state classes), §18/§18.4
(Publication Handoff ownership, now resolved by this contract exactly as
§18.4 anticipated — "a future, separately governed contract revision"),
and §19/§21.18 (`IWC-REQ-171`, now retired from "unassigned" by this
contract's §4 and §6) are all read as currently frozen and satisfied, not
amended.

**PEC-REQ-094.** **CHGR-001** — no section is renumbered, reworded, or
contradicted. §8/§9/§10 (the atomic write/identity/provenance requirements
this contract's Coordinator satisfies without altering their text), §13
(record lifecycle, untouched beyond creation), §17 (Runtime Consumption
Contract's self-authorization prohibition, restated unchanged at §5/§32
above), §19.1 (Typed Authority Model separation, reconfirmed at §96
below), and §20/§20.5 (Governance Responsibility Contract's Publication
row and its "not yet assigned" deferral, now resolved by this contract
exactly as §20.5 anticipated) are all read as currently frozen and
satisfied.

**PEC-REQ-095.** **Phase 144A** — this contract's Publication Coordinator,
Authority Contract, and Authorization Event Contract are the direct
freezing of 144A's Option C recommendation (§3) and §5's Model 2
recommendation; no architectural conclusion 144A reached is contradicted.

**PEC-REQ-096.** **TAMC-001 / TAMPC-001** — untouched; independently
reconfirmed structurally disjoint per IWC-001 §19.1 and CHGR-001 §19.1;
TAMC-REQ-009's prohibition on TAMC-001 authorizing publication in any sense
is unaffected by this contract, which grants the Typed Authority Model
family no role in Publication Authorization.

**PEC-REQ-097.** **Canonical Phase Finalization Architecture / Canonical
Lifecycle State Authority Architecture / Governance Lifecycle Pattern
Architecture (Phase 134/135/137V, GLP-001)** — untouched; confirmed
unrelated domain (§4 above); this contract's own Stage 2 Contract Freeze
status is itself an instance of GLP-001 §6.1's pattern, not a modification
of it.

**PEC-REQ-098.** **Existing implementation (143K–143P, Interactive
Workflow)** — zero files under `src/pcae/interactive_workflow/**` are
authorized to change by this contract; 143P's certification remains fully
valid and unaffected.

---

## 14. Extensibility Contract

**PEC-REQ-099.** Future implementations MAY extend diagnostics, metrics,
and observability around the Publication Coordinator, provided no such
extension alters ownership, authorization, or the publication boundary
this contract freezes.

**PEC-REQ-100.** Future implementations SHALL NOT redefine ownership: the
Publication Coordinator remains the sole owner of Publication Execution
(§4, §73) unless and until a future, separately governed contract revision
supersedes this one.

**PEC-REQ-101.** Future implementations SHALL NOT redefine authorization:
the readiness/authorization distinction (§3, §5) and the CLI-operator
invocation model (§6) remain frozen unless and until a future, separately
governed contract revision amends them.

**PEC-REQ-102.** Future implementations SHALL NOT redefine the publication
boundary: §9's CHGR Boundary Contract remains frozen in the same terms.

**PEC-REQ-103.** Model 3 (a separate, typed, CHGR-scoped delegated
authorization artifact, per 144A §5) is named as a permitted future
hardening layer; adopting it requires a governed contract revision to this
contract, not an informal extension by an implementing phase.

**PEC-REQ-104.** Multi-party or quorum-based Publication Authorization
(analogous to IWC-001 §17's reserved L5 multi-party Confirmation extension
point) is explicitly deferred; this contract's single-operator
Authorization Event model is the case such an extension would extend, not
replace, and building it now is out of scope for this contract.

---

## 15. Audit Contract

**PEC-REQ-105.** A future verifier SHALL be able to determine, from the
Publication Coordinator's own retained records alone: which
`PublicationReadinessPackage` was consumed; which Publication Authorization
Event authorized the act, including operator identity and timestamp;
whether the attempt succeeded or was refused, and for what reason if
refused; and the resulting CHGR's canonical identifier, where creation
succeeded.

**PEC-REQ-106.** Every refused Publication Execution attempt SHALL be
independently retrievable, not merely logged and discarded (restating §43
above at the audit layer).

**PEC-REQ-107.** The audit trail the Coordinator retains SHALL be
structurally separate from Session Audit Evidence (IWC-001 §13.1) and from
CHGR provenance (CHGR-001 §10); it documents the Coordinator's own act, not
a restatement of either.

---

## 16. Amendment Contract

**PEC-REQ-108.** PEC-001 MAY evolve only through governed superseding
contracts, each independently re-derived and independently verified,
mirroring CHGR-001 §22's and IWC-001 §20's identical amendment discipline.

**PEC-REQ-109.** No requirement in §17 below SHALL be altered by an
implementing phase's own discretion; any apparent gap or ambiguity
discovered during implementation is evidence of a defect requiring a
governed contract revision, never license to informally resolve it in
code.

**PEC-REQ-110.** Backward compatibility with PEC-001 v1.0 SHALL be
maintained by any superseding revision unless the revision explicitly and
narrowly states otherwise, mirroring CHGR-REQ-193's identical discipline.

---

## 17. Requirement Set

The requirements above (`PEC-REQ-001` through `PEC-REQ-110`) are the
complete, authoritative, falsifiable enumeration of this contract's
obligations. They are organized into the sixteen subsections above
(§2–§16), sequential, with no gaps and no reuse.

---

## 18. Adversarial Validation

Nine adversarial scenarios were run against the requirement set above;
every scenario resolved to an existing, citable mitigation.

| # | Scenario | Mitigating requirement(s) |
|---|---|---|
| A1 | Coordinator publishes automatically on `Confirmed` | PEC-REQ-009–012, 035 |
| A2 | Coordinator infers authorization from a "ready" package | PEC-REQ-009, 010, 028–031 |
| A3 | Replay: same package published twice | PEC-REQ-007, 008, 041, 042, 078, 080, 087 |
| A4 | Coordinator placed inside `interactive_workflow/**` | PEC-REQ-018, 093 |
| A5 | Coordinator scope creep (adds validation/notification logic) | PEC-REQ-022–026, 073, 100 |
| A6 | Package tampered to carry an authority token or CHGR ID | PEC-REQ-061–064 |
| A7 | Partial write leaves an inconsistent CHGR | PEC-REQ-053, 054, 081, 082 |
| A8 | CLI invocation treated as a standing authorization grant | PEC-REQ-092 |
| A9 | Coordinator supersedes/revokes an existing CHGR itself | PEC-REQ-026, 067, 072 |

No scenario surfaced a genuine gap requiring a new requirement beyond this
contract's draft text; each was mitigated by requirements already derived
directly from §1–§16's narrative obligations.

---

## 19. Success Criteria

A future implementation of this contract is successful only if:

1. A `PublicationCoordinator`-shaped component exists, external to
   `interactive_workflow/**`, `cltr/**`, and the PCAE phase-lifecycle tree.
2. It cannot be reached, and performs no write, absent a verified
   Publication Authorization Event (§6).
3. It rejects Replay at its single entry point (§8, §78).
4. Its write is atomic: identity assignment and provenance/integrity
   capture occur within the same operation as the write itself (§7).
5. No responsibility in §10's matrix is duplicated or left unowned.
6. Runtime posture remains `Observed`/`observe`/`unavailable` until a
   separately governed phase explicitly authorizes a capability change.
7. 143P's Interactive Workflow certification remains valid and unaffected.
8. Every failure scenario in §11 terminates deterministically with no
   partial CHGR created.

---

## Non-Goals

This contract does not:

- implement `PublicationCoordinator` or any other class;
- implement any CLI command, flag, or exit-code behavior;
- implement any CHGR-writing machinery under
  `src/pcae/schema_resources/chgr/**`;
- create any CHGR;
- modify `src/pcae/interactive_workflow/**`;
- modify any Typed Authority Model or CLTR machinery;
- modify any PCAE phase/task lifecycle machinery;
- introduce any runtime capability change;
- constitute, or provide evidence of, any Publication Authorization Event;
- authorize any future implementation phase to begin merely by this
  contract's own freeze.

---

## 20. Phase 144E contract revision — consuming the widened Publication Readiness Package

**Version:** 1.1
**Predecessor:** PEC-001 v1.0 (Phase 144B)
**Revised by:** Phase 144E — Publication Execution Contract Revision

### 20.1 Reason

Phase 144D independently classified Finding F-1/JC-2 as Blocking for full
CHGR-001 §10 conformance and Non-Blocking against this contract's own
literal §17 text, because PEC-REQ-054 already required "provenance/
integrity capture (CHGR-001 §10) ... in the same atomic operation," and
PEC-REQ-059 already described the Coordinator's required input as
including "captured decision content" and "exact Preview" — language this
contract's own §8 never itself narrowed to identifiers/digests only; the
narrowing originated one layer earlier, in IWC-001 §11.4's implementation
(Phase 143O), independently re-derived and closed by IWC-001 §26 (this
same governed phase). This section closes the corresponding half of the
gap on this contract's side: it describes, without altering any existing
PEC-REQ-001–110 requirement, how a Publication Coordinator implementation
consumes IWC-001 v1.2's widened Package to actually satisfy PEC-REQ-054's
already-existing CHGR-001 §10 obligation, which no implementation could
previously satisfy through no fault of this contract's own text.

### 20.2 Changed requirements

**PEC-REQ-111.** The Publication Coordinator's sole input package (§8)
now carries, per IWC-001 v1.2 IWC-REQ-185, verbatim content in addition
to its existing reference fields. PEC-REQ-054's provenance/integrity
capture obligation (restating CHGR-001 §10 unchanged) SHALL be read as
satisfiable using this widened package alone, without requiring the
Coordinator to independently fetch, re-derive, reconstruct, or infer any
field CHGR-001 §10 requires.

**PEC-REQ-112.** A Publication Coordinator implementation SHALL carry
every verbatim field IWC-REQ-185 adds through, unmodified, into the CHGR
record's provenance capture (CHGR-001 §10), populating
`human_governance_record`'s `decision_subject`, `template_ref`,
`selected_option_id`, `decision_maker_identity_evidence`, `rationale`,
and `conditions` fields, and the sibling `human_confirmation_evidence`/
`governance_record_provenance` artifacts' `confirmation_statement`,
`options_presented`, and preview-content fields, directly and only from
the widened Package's own verbatim content — never from an independently
fetched, computed, or re-derived value.

**PEC-REQ-113.** The Coordinator SHALL continue to depend on nothing
beyond the Publication Readiness Package boundary and the CHGR-001
§8/§9/§10 write surface (restating PEC-REQ-086 unchanged). This revision
widens the Package's content, not the Coordinator's dependency boundary:
PEC-REQ-018–020's placement rules and the existing AST-enforced
import-boundary discipline (Phase 143O, Phase 144C's
`_FORBIDDEN_IMPORT_ROOTS` test) remain unchanged and unweakened. A
Publication Coordinator implementation SHALL NOT import
`pcae.interactive_workflow.session`, `.preview`, `.confirmation`,
`.orchestration`, `.evidence`, `.clarification`, `.state_machine`,
`.audit`, or `pcae.cltr` to obtain any field this section names; every
such field SHALL arrive exclusively through the Package.

**PEC-REQ-114.** §8's "unmodified from interactive_workflow's own frozen
shape" language (PEC-REQ-058) now refers to the IWC-001 v1.2-widened
shape. No other provision of this contract that names the Package's
prior shape is thereby contradicted: none named a closed field list this
contract itself owns — PEC-REQ-065 already assigned shape ownership to
`interactive_workflow/**` exclusively, and continues to do so unchanged.

**PEC-REQ-115.** `authority_basis_claimed` (CHGR-001 §10, §11) is a claim
citing the bound Decision Template's own `eligible_authority` field
(CHGR-REQ-096). Where the widened Package's verbatim `template_ref`
content resolves, deterministically and without discretion, to that
template's own `eligible_authority` text, the Coordinator MAY construct
`authority_basis_claimed` solely from that already-verbatim citation,
never from an independent judgment of whether the claim is actually
valid — restating PEC-REQ-057's "no discretionary step" and
CHGR-REQ-097's authority-gap-disclosure rule unchanged, one layer later.
The Coordinator SHALL NOT itself evaluate, weight, or resolve eligibility;
that determination remains, as it always has, outside Publication
Execution entirely (CHGR-001 §11).

**PEC-REQ-116.** This widening does not authorize the Coordinator to
validate, weight, or resolve any conflict among the Package's verbatim
fields. PEC-REQ-048's existing validation obligation — confirming the
package is the exact, unmodified output of
`PublicationHandoff.build_package`/`serialize` — extends unchanged to the
widened shape; a Package failing that check remains invalid per
PEC-REQ-064 and refused per PEC-REQ-077, exactly as before this revision.

**PEC-REQ-117.** No requirement in §17 (PEC-REQ-001 through PEC-REQ-110)
is narrowed, superseded, or reworded by this revision. PEC-REQ-111
through PEC-REQ-116 are additive; §19's Success Criteria and §18's
Adversarial Validation table remain fully satisfied by an implementation
that additionally satisfies PEC-REQ-111–116.

### 20.3 Regression review

Independently reconfirmed unchanged: Definitions (§2), Core Invariants
(§3), the Publication Coordinator Contract (§4, including PEC-REQ-018–020's
placement/dependency boundaries, restated unweakened by PEC-REQ-113
above), the Authority Contract (§5), the Authorization Event Contract
(§6), the Publication Execution Contract (§7, including atomicity,
determinism, and failure-handling — this revision changes only which
verbatim values the already-atomic write carries, never the ordering,
atomicity, or determinism discipline itself), the Publication Readiness
Package Contract's structural rules (§8 — immutability PEC-REQ-060,
authority-neutrality PEC-REQ-061, publication-neutrality PEC-REQ-062, and
the prohibited-fields list PEC-REQ-063 all extend, unweakened, to every
newly-added field: none of IWC-REQ-185's additions is an authority token,
a publication decision, a CHGR identifier, or execution state), the CHGR
Boundary Contract (§9), the Responsibility Matrix (§10, unaffected — no
row is reassigned; `interactive_workflow`/`PublicationHandoff` still owns
Package construction and completeness, the Coordinator still owns only
verification and atomic write), Failure Semantics (§11), the Security
Contract (§12, strengthened in the Coordinator's actual capability to
satisfy PEC-REQ-089's immutable-evidence and PEC-REQ-085's
authority-neutrality provisions against complete data, not weakened by
any new attack surface — the widened fields are copied, never computed,
from a boundary already inside the Package's existing authority-neutral,
tamper-checked shape), the Compatibility Contract (§13), the
Extensibility Contract (§14), the Audit Contract (§15), and the Amendment
Contract (§16).

### 20.4 Compatibility review

Independently confirmed compatible with IWC-001 v1.2 (this same phase's
companion revision, §26 there), CHGR-001 (unmodified; this revision moves
an existing implementation strictly closer to CHGR-001 §10 conformance,
never redefining any CHGR-001 section), TAMC-001/TAMPC-001 (unmodified,
independently reconfirmed structurally disjoint — no field this revision
names is a Typed Authority Model record type or identifier namespace
member), and the Canonical Phase Finalization / Canonical Lifecycle State
Authority / Governance Lifecycle Pattern family (Phase 134/135/137V,
GLP-001 — unrelated domain, unaffected).

### 20.5 Migration strategy

Phase 144C's implementation (`src/pcae/governance/publication/**`) is
unmodified by this revision (Forbidden Files for this phase); it remains
exactly as Phase 144D verified it: PEC-001 v1.0-conformant, and
CHGR-001 §10-incomplete (F-1, unrepaired). Migrating the 144C
implementation to satisfy PEC-REQ-111–116 requires, in a future,
separately governed implementation phase (144F or equivalent, not
authorized here):

1. An IWC-001-side change (widening `PublicationReadinessPackage`,
   `Preview`, and `PublicationHandoff.build_package` per IWC-001 §26.3) —
   an implementation update, not merely documentation, since new fields
   must be added to existing frozen dataclasses.
2. A PEC-001-side change (updating
   `src/pcae/governance/publication/record.py`'s `build_publication_record`
   to populate the CHGR-001 §10 fields this section names from the
   widened Package, and removing or narrowing `_KNOWN_LIMITATIONS`
   accordingly) — an implementation update to the Coordinator's record
   construction, not to its ownership, authorization, or execution-ordering
   logic, all of which PEC-REQ-111–116 leave untouched.

No CLI, storage, or runtime change is required by either step; both are
pure-function content changes to already-existing, already-atomic write
paths. Until that future phase runs, no CHGR schema-validated against
`human_governance_record.schema.json` can be produced by
`PublicationCoordinator`, exactly as Phase 144D found.

### 20.6 Backward-compatibility impact

None beyond the additive widening itself. Every PEC-001 v1.0 requirement
remains textually and positionally unchanged. A hypothetical future
implementation satisfying only PEC-REQ-001–110 (the pre-revision text)
without also satisfying PEC-REQ-111–117 would remain PEC-001-literal-
compliant but would not close F-1 — exactly Phase 144C's own status
today, unaffected by this revision. No implementation of
`PublicationCoordinator`, any CLI command, any CHGR-writing machinery, or
any new capability is authorized, performed, or implied by this revision.
`src/pcae/governance/publication/**` and `src/pcae/interactive_workflow/**`
are unmodified (verified: zero files under either path appear in this
phase's diff). Runtime remains State: Observed, Maximum Capability:
observe, Execution Availability: unavailable, unchanged before and after
this revision.

## 21. Post-revision next phase

The expected next phase is **144F — Provenance Boundary Implementation**,
which would implement both this section's and IWC-001 §26's obligations
against the actual `interactive_workflow` and `governance/publication`
source. This recommendation does not authorize 144F.
