# Phase 143J — Canonical Human Governance Record Interactive Decision Workflow Implementation Planning

## 0. Status and scope

**Phase:** 143J
**Type:** Implementation planning (GLP-001 §6.1 Stage 3 discipline, applied
here to the Interactive Workflow layer exactly as Phase 143D applied it to
the CHGR schema/artifact foundation layer)
**Governed subject:** The Interactive Decision Session subsystem frozen by
`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.1) and
constrained above by `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
(CHGR-001 v1.0).
**Predecessor evidence:** Phase 143A, 143C, 143D, 143E, 143F, 143F.1, 143G,
143H, 143I, 143I.1, 143I.2 (Track 143 in full), plus
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` (TAMC-001),
`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(TAMPC-001), `src/pcae/lifecycle.py` / Phase 135 (lifecycle architecture),
and `src/pcae/core/canonical_artifact_promotion.py` / Phase 114A (canonical
artifact architecture). Every one of these is treated as evidence of what
already exists and what has already been decided, never as license to
re-decide it here.

**This phase produces planning text only.** It implements no session, no
schema, no CLI, no storage, no persistence, no confirmation mechanism, no
publication code, no runtime enforcement, and no authority resolution. It
modifies no contract. Runtime remains State: Observed, Maximum Capability:
observe, Execution Availability: unavailable, unchanged before and after
this phase, exactly as every predecessor phase in Track 143 has confirmed.

### 0.1 Confirmation of governing inputs

Before planning began, this phase confirmed:

1. A governed PCAE session was bootstrapped (`pcae session bootstrap
   --agent-id claude-local`); backend lock rehydrated; health/check
   passed.
2. The repository was clean (`git status --porcelain` empty) before this
   phase's task contract was created.
3. No other governed phase was active — the only active task was the idle
   placeholder `20260724-0214-idle-awaiting-next-governed-phase-after-143i-2`,
   which this phase's task contract creation completed and superseded.
4. IWC-001 v1.1 and CHGR-001 v1.0 were read directly and completely
   (not summarized from a prior phase's own account of them); the eleven
   Track 143 phase reports, TAMC-001, TAMPC-001, the lifecycle
   architecture, the canonical artifact architecture, and
   `PROJECT_STATUS.md` were read as evidence of prior decisions and
   current repository state (§0.2 below records what each established).
   No previous implementation decomposition (including 143D's, for the
   sibling CHGR schema/artifact subsystem) is assumed complete or
   directly transferable; 143D is used here as a *disciplined precedent
   for planning method*, not as a source of pre-answered questions about
   the Interactive Workflow subsystem specifically.

### 0.2 What is settled entering this phase, and what is not

**Settled (frozen, not reopened by this plan):**

- IWC-001 v1.1's ten-state model (§4.4, IWC-REQ-040–042), fully repaired
  and independently re-verified as internally coherent (143I.1, 143I.2).
- The Decision Session vs. CHGR distinction (IWC §1, §7, §11; CHGR §1),
  the five-state-class separation (IWC §11.1, IWC-REQ-113–120), and the
  Publication Handoff boundary as a *named but unimplemented* boundary
  (IWC §2, §11.4, §18.4).
- The AI/human responsibility boundary (IWC §5–§6), the Decision
  Existence semantics (IWC §7, IWC-REQ-070–077), and the Confirmation
  exact-digest-binding discipline (IWC §10) — independently confirmed at
  143I as "the single most safety-critical property" in the contract.
- The wholly-separate-artifact-family boundary against the Typed
  Authority Model (IWC §19.1, IWC-REQ-174–176) and the non-adoption of
  `canonical_artifact_promotion.py`/`ArtifactState` as anything more than
  non-binding precedent (IWC §19).
- Two disclosed, unrepaired Observations carried forward from 143I: OBS-1
  (smart-resume re-affirmation — explicitly left as future implementation
  discretion) and OBS-2 (a disclosure-only regression in the
  Explanation/Persuasion boundary heading, not a substantive gap). This
  plan treats both as inputs to specific planning decisions below (§8.2,
  §11.2) rather than as defects requiring contract repair — repairing
  them is out of this phase's scope by the Governing Inputs and
  Explicit No-Go sections above.

**Not settled — precisely what this phase exists to decide:**

- How the ten-state model, the AI/human boundary, and the Confirmation
  binding become buildable software: which modules, in what order, with
  what test discipline, and what remains explicitly deferred beyond this
  plan's own first-increment recommendation.

---

## 1. Planning Principles Restated as Design Constraints

Every planning decision below is checked against these ten invariants
before being finalized; none is treated as negotiable for implementation
convenience:

| # | Principle | Binding source | Planning consequence |
|---|---|---|---|
| 1 | Human-exclusive authority | IWC §6, IWC-REQ-063 | No component may expose a code path that selects an option, supplies rationale, or confirms without an explicit, externally-supplied human input value |
| 2 | Explicit confirmation | IWC §10, IWC-REQ-098–112 | Confirmation Engine is planned as its own component, never folded into session-transition logic generically |
| 3 | Preview Digest binding | IWC §10.2–§10.4 | Digest recomputation is planned as mandatory, synchronous, and blocking immediately before any state write that would enter `Confirmed` |
| 4 | Decision Existence semantics | IWC §7 | No planned component's data model may expose a field or query that reports "decision made" before `Confirmed` |
| 5 | Lifecycle independence | IWC §11.5, IWC-REQ-113–114 | No planned component imports, calls, or is called by `src/pcae/lifecycle.py`, `phase_reports.py`, or any PCAE phase/task lifecycle module |
| 6 | Authority neutrality | IWC §11.2, CHGR §11 | No planned component computes or exposes an "is this decision authoritative" boolean; that judgment belongs to a future, separately authorized Publication/consumption layer |
| 7 | Runtime neutrality | IWC §19.1, IWC-REQ-179 | No planned component is reachable from any `pcae runtime inspect`-visible capability path |
| 8 | Transport independence | IWC §16, IWC-REQ-155–161 | Every planned component's interface is specified in terms of stages/states/data, never CLI flags, HTTP verbs, or widget behavior |
| 9 | Deterministic behavior | IWC §8.1, §10.1, IWC-REQ-079, 098 | Every planned component that produces output from state is specified as a pure function of that state plus explicitly-cited external inputs |
| 10 | Fail-closed execution | IWC §12, §15, IWC-REQ-153 | Every planned error path defaults to refusing advancement, never to a best-effort continuation |

No component decomposed in §3 below is permitted to weaken any of these
ten; where a design choice in §9–§16 appears to create tension with one,
that tension is resolved in favor of the invariant, and the resolution is
disclosed as a judgment call (see §9.2, §11.2, §17.3).

---

## 2. Implementation Boundary

### 2.1 Inside the Interactive Workflow subsystem

| Responsibility | Inside? | Basis |
|---|---|---|
| Decision Session lifecycle (create, transition, terminate) | Yes | IWC §4 |
| Session state persistence (read/write of session records) | Yes | IWC §4.10, §12, §14 |
| Transition enforcement (ten-state table) | Yes | IWC §4.4 |
| Confirmation workflow (Preview, digest, capture) | Yes | IWC §10 |
| Preview Digest generation and verification | Yes | IWC §2, §10.2 |
| Evidence assembly coordination (calling existing evidence sources, assembling per template declarations) | Yes | IWC §8 |
| Clarification orchestration (routing Explanation/Clarification, blocking Recommendation/Persuasion) | Yes | IWC §9 |
| Cancellation, expiry, abandonment handling | Yes | IWC §4.7–§4.9, §12 |
| Publication Handoff *boundary description and data contract* | Yes — description and interface only | IWC §2, §11.4, §18.4 |
| Session Audit Evidence retention (seven boundaries) | Yes | IWC §13 |
| Transport adapters (CLI first; interface for others) | Yes | IWC §16 |
| Session persistence *abstraction* (interface, not storage technology) | Yes | IWC §4.10 |
| **Publication itself** (writing a CHGR, assigning `chgr-<uuid4>`, atomic canonical storage) | **No** | CHGR §8, IWC §2 — explicitly out of scope, "described but unimplemented" |
| **Publication Handoff execution** (the actual call from a Confirmed session into Publication) | **No — interface only, no callee exists** | IWC §18.4 — ownership explicitly unassigned |
| Decision Template *authoring or governance* | No — templates are consumed, not authored, by this subsystem | CHGR §6 (already governed) |
| CHGR schema definitions | No | Already frozen (143E), owned by `src/pcae/schema_resources/chgr/` |
| Authority resolution / eligibility checking beyond "is this the identity bound at session creation" | No | IWC §11.2, CHGR §11 — a future, separately authorized layer |
| Cryptographic signing | No | IWC §17 extension point, not built here |
| External identity-provider integration | No | IWC §17 extension point |
| Multi-participant / quorum workflows | No | IWC §17, IWC-REQ-167 — explicitly deferred |
| Legacy import | No | CHGR §14 — a separate, already-deferred concern; no interaction with sessions |

### 2.2 Boundary tests applied

A responsibility is placed inside the subsystem only if all three hold:
(a) IWC-001 names it as part of the Decision Session layer; (b) it can be
implemented without writing a CHGR or assigning `chgr-<uuid4>`; (c) it
does not require an authority model, identity provider, or runtime
capability that does not already exist. Publication Handoff passes (a)
only partially — IWC-001 names the boundary but assigns no owner (§18.4)
— so this plan treats *describing the interface* as inside scope and
*building the callee* as outside scope, mirroring 143D's identical
"plan the boundary, do not build across it" treatment of CHGR Publication
before 143E existed.

---

## 3. Architectural Decomposition

Eighteen candidate components were evaluated (per the governing prompt's
own list). Each is independently justified below rather than adopted
by default; two are merged, one is deferred entirely, and none is added
beyond the governing prompt's list.

| Candidate component | Decision | Reason |
|---|---|---|
| Session Coordinator | **Adopt** | Needed as the single entry point owning session identity (§4.1), ownership binding (§4.2), and template/subject binding (§4.3); no other planned component is positioned to own creation |
| State Machine | **Adopt** | The ten-state table (§4.4) is a distinct, independently testable concern from *what* triggers a transition; keeping it separate lets the transition table be exhaustively unit-tested against IWC-REQ-040–049 in isolation |
| Transition Validator | **Merge into State Machine** | IWC-001 draws no line between "the table" and "code that checks a proposed transition against the table" — splitting them would create two components with one shared piece of state (the table itself) and no independent responsibility for the Validator beyond enforcing what the State Machine already owns; merging avoids a coordination surface with no contractual basis |
| Confirmation Engine | **Adopt** | IWC §10 is the contract's own most safety-critical section (143I); it owns Preview Digest recomputation, stale-preview rejection, and the non-defaultable confirming-action check — distinct enough from Preview generation (a pure rendering function) to warrant its own component boundary, so a defect in "did we check the digest" is never conflated with a defect in "did we render the preview correctly" |
| Preview Builder | **Adopt, as a pure function, not a stateful component** | IWC §10.1, IWC-REQ-098 requires Preview to be "a pure function of captured content"; planning it as a stateless function (not an object with lifecycle) is the only design that can satisfy IWC-REQ-079's determinism requirement without also requiring its own persistence or test-isolation discipline |
| Preview Digest Generator | **Merge into Preview Builder** | IWC §2, §10.2 define Preview Digest as "a content digest of the exact Preview" — it is a deterministic transform *of* the Preview Builder's own output, not an independent responsibility; separating them would require passing the exact same content through two components for no additional behavior, creating a synchronization risk (the digest could be computed over content that later drifts from what the Preview Builder actually returned) that a merged pure-function design eliminates by construction |
| Evidence Coordinator | **Adopt** | IWC §8 (deterministic assembly, category discipline, uncertainty/conflict disclosure, substitution prevention) is a large, independently testable responsibility with its own failure modes (§12's "stale evidence" row) distinct from session-state management |
| Clarification Controller | **Adopt** | IWC §9's four-act boundary (Explanation/Clarification permitted, Recommendation/Persuasion forbidden) is a security-relevant boundary (§15, threat "prompt injection") that benefits from being its own enforceable choke point rather than diffused logic inside the Session Coordinator |
| Session Persistence Interface | **Adopt** | IWC §4.10 requires structural separation from CHGR canonical storage; an interface (not a concrete store) lets §7 (Persistence Planning) defer storage-technology choice while still letting every other component depend on a stable contract |
| Session Repository | **Rename to "Session Persistence Interface's default implementation"; do not adopt as a separate architectural component** | The governing prompt lists both "Session Persistence Interface" and "Session Repository" as candidates; IWC-001 draws no distinction between an abstract persistence contract and a concrete repository beyond "interface vs. implementation," which is one component with two facets, not two components — planning them as two invites exactly the kind of unforced complexity §1's ten invariants do not require |
| Expiry Manager | **Adopt, as a stateless policy function invoked by the State Machine, not a standalone running service** | IWC §4.7 requires transition to `Expired`, "never silently extend"; planning it as logic invoked at read/resume time (checking persisted `expires_at` against current time) rather than a background daemon avoids introducing a new runtime process this contract's Runtime Neutrality principle (§1 row 7) would have to account for |
| Cancellation Manager | **Merge into State Machine's transition surface; no separate component** | Cancellation (§4.8) is a single transition available from every non-terminal state, with no additional data or side effects beyond the transition itself (IWC-REQ-048: "no partial record, no residual claim") — it has no responsibility the State Machine does not already own |
| Abandonment Manager | **Merge into Expiry Manager as a shared "inactivity policy" concern, still invoked by the State Machine** | Both Expiry and Abandonment are policy-driven, time-based, non-terminal-state-triggered transitions (§4.4, §12) differing only in the threshold and the specific "why" recorded; one shared component with two named policies avoids duplicating the "check elapsed time against a threshold, transition if exceeded" logic twice |
| Publication Handoff Adapter | **Plan the interface only; do not implement, do not name an owner** | IWC §18.4 leaves ownership explicitly open; planning further than "here is the exact data this boundary hands off" would be inventing a role/responsibility this contract has no basis to invent (§1 row 6 and IWC-REQ-171) |
| Audit Recorder | **Adopt** | IWC §13's seven auditable boundaries are a distinct cross-cutting responsibility (every other component writes to it; no other component reads from it for its own operational purposes) — planning it separately keeps "what happened" (Audit Recorder) structurally distinct from "what state are we in" (State Machine), directly implementing IWC §13.1's requirement that a verifier distinguish these classes from retained state alone |
| Transport Abstraction Layer | **Adopt** | Required by IWC §16's transport-independence contract; without a named boundary, transport-specific concerns (CLI flag parsing, TUI rendering) would leak into the Session Coordinator, which IWC-REQ-155/156 forbid |
| Error Model | **Adopt, as a shared cross-cutting concern, not a runtime component** | A closed, deterministic error taxonomy (§12 planning below) is data/contract, not a running piece of software; planning it as a component would misrepresent its nature |
| Validation Layer | **Merge into Evidence Coordinator (evidence-shape validation) and State Machine (transition validation); no separate component** | "Validation" as named in the governing prompt is not one responsibility in IWC-001 — required-field/closed-set validation belongs to Decision Capture (owned by Session Coordinator, checked at `DecisionSelected`), evidence validation belongs to Evidence Coordinator, and Preview Digest validation belongs to Confirmation Engine; a fourth, generic "Validation Layer" would either duplicate these or become a grab-bag with no IWC-001 textual anchor |

**Resulting decomposition — nine components, down from the prompt's
eighteen candidates, each independently justified above:**

1. **Session Coordinator** — identity, ownership, template/subject
   binding, Decision Capture, orchestrates the others.
2. **State Machine** (absorbs Transition Validator, Cancellation Manager)
   — the ten-state table, transition enforcement, terminal-state
   guarantees.
3. **Confirmation Engine** — Confirmation Readiness computation,
   Confirmation act capture, replay/stale-preview rejection.
4. **Preview Builder** (absorbs Preview Digest Generator) — pure-function
   Preview rendering and digest computation.
5. **Evidence Coordinator** — deterministic assembly, categorization,
   staleness/conflict disclosure, substitution prevention.
6. **Clarification Controller** — Explanation/Clarification routing,
   Recommendation/Persuasion structural prohibition.
7. **Session Persistence Interface** (absorbs Session Repository as its
   default implementation) — the storage abstraction §4.10 requires.
8. **Expiry/Abandonment Policy** (absorbs Expiry Manager and Abandonment
   Manager) — shared time-threshold transition logic.
9. **Audit Recorder** — the seven-boundary Session Audit Evidence log.

Plus one **named-but-unbuilt boundary** (Publication Handoff — interface
described in §14 below, no code planned) and two **cross-cutting,
non-component concerns** (Transport Abstraction, planned in §12; Error
Model, planned in §13).

---

## 4. Responsibility Matrix

One owner per responsibility, per IWC §18's own discipline (IWC-REQ-168).

| Component | Purpose | Owned state | Inputs | Outputs | Authority | Lifecycle ownership | Dependencies | Prohibited responsibilities |
|---|---|---|---|---|---|---|---|---|
| **Session Coordinator** | Create/own a Decision Session; bind identity, template, subject; capture Decision Capture fields | `session_id (CDS-<uuid4>)`, `owner_identity`, `template_ref`, `subject_ref`, `human_selection_id`, `human_rationale_text`, `human_conditions_text`, `disclosure_acknowledgements` | Creation request (identity, template ref, subject ref); Decision Capture inputs from a transport | Session record deltas; Confirmation Readiness boolean (computed, never stored as override) | None — creates no authority | Owns session existence from `Created` through hand-off | Session Persistence Interface, State Machine, Evidence Coordinator, Clarification Controller | Selecting on a human's behalf (IWC-REQ-051); inferring consent (IWC-REQ-055); computing "is this authoritative" |
| **State Machine** | Enforce the ten-state table; validate every proposed transition against §4.4; guarantee terminal-state finality | Current `session_state` enum value only (not the rest of the session record) | Proposed transition (from-state, to-state, trigger) | Accept/reject decision; new state value | None | Owns state-value correctness only, not session content | Session Persistence Interface (read current state, write new state) | Introducing any transition not in §4.4's table (IWC-REQ-042); reasoning about *why* a transition is desirable — that judgment belongs to callers |
| **Confirmation Engine** | Gate entry to `Confirmed`; recompute and check Preview Digest; capture the confirming act | `confirmation_evidence` (digest reference, timestamp, identity evidence, acknowledgement flag) | Session's current Decision Capture state; a confirming action from a transport | Accept (triggers State Machine transition to `Confirmed`) or refusal (with fresh Preview) | None — session-confirmed is not record-confirmed (IWC §11.2) | Owns confirmation-evidence correctness only | Preview Builder (fresh digest), State Machine (transition), Audit Recorder | Treating session-Confirmed as CHGR-confirmed (IWC-REQ-115); accepting confirmation on identity-only or digest-only evidence (IWC-REQ-152) |
| **Preview Builder** | Deterministically render Preview and its digest from captured content | None (pure function; owns no persisted state) | Decision Capture snapshot, template scaffolding, assembled evidence | `(preview_content, preview_digest)` | None | N/A — stateless | Evidence Coordinator's assembled-evidence output, template rendering data | Caching a rendering across calls in a way that could go stale (IWC-REQ-105); any randomness or environment-dependence (IWC-REQ-098) |
| **Evidence Coordinator** | Assemble evidence per template declarations; detect gaps/conflicts/staleness; prevent cross-subject reuse | `evidence_snapshot` (per-session, timestamped) | Decision Subject, bound template's evidence-class declarations, current governing-artifact state | Categorized evidence set with provenance, gap/conflict flags | None — never ranks or weights (IWC-REQ-081) | Owns evidence-snapshot freshness only | External evidence sources (read-only), Session Persistence Interface | Weighting/ranking evidence; silently reusing evidence across subjects (IWC-REQ-087) |
| **Clarification Controller** | Route Explanation/Clarification; structurally block Recommendation/Persuasion; log every exchange | `clarification_log` entries (append-only within a session) | A clarification request plus current Decision Capture state (never the inferred target selection) | An Explanation/Clarification answer, or a structural refusal | None | Owns clarification-log completeness only | Audit Recorder (logs verbatim, IWC-REQ-096), template scaffolding text | Producing an answer whose content varies by inferred target (IWC-REQ-095); reframing template wording (IWC-REQ-097) |
| **Session Persistence Interface** | Abstract read/write/resume of session records, structurally separate from CHGR storage | The interface contract only; a default file-based implementation owns the actual bytes | Session record snapshots from any of the above | Persisted snapshot; resumed snapshot on read | None | Owns durability and structural-location correctness only (§4.10) | Filesystem (default impl only) | Colocating session files under any CHGR-schema-manifest-visible path (IWC-REQ-049) |
| **Expiry/Abandonment Policy** | Compute whether a session's elapsed time or inactivity has crossed a threshold | None (pure function of `created_at`/`last_activity_at` plus template-or-default thresholds) | Session timestamps, template-declared or system-default lifetime/idle thresholds | `Expired` / `Abandoned` / no-op transition proposal to the State Machine | None | N/A — stateless policy | State Machine (proposes transitions only, does not apply them) | Silently extending a lifetime (IWC-REQ-046); running as a background process (would introduce a new runtime capability — see §1 row 7) |
| **Audit Recorder** | Retain the seven auditable boundaries (§13.1) as Session Audit Evidence | Append-only log of: AI conversation, Clarification, Proposal, Evidence, Preview, Confirmation, (eventually) CHGR-reference-once-published | Emissions from every other component | A retrievable, structurally-separated evidence trail per session | None | Owns log completeness and structural separation only | Session Persistence Interface | Summarizing AI conversation (IWC-REQ-134 requires verbatim); treating its own content as itself canonical (IWC-REQ-135) |

Every "Authority: None" entry above is deliberate and identical across
all nine components: no planned component computes, stores, or exposes
an authority determination, matching CHGR-001 §11 and IWC-001 §11.2's
shared principle that recording/confirming a session is evidence a human
acted, never proof of eligibility.

---

## 5. Session State Planning

### 5.1 Transition ownership

The State Machine (§3, §4) is the sole owner of transition legality.
Every other component that wants a transition to occur — Session
Coordinator advancing `Created`→`EvidenceReady` once context acquisition
completes, Confirmation Engine advancing `AwaitingConfirmation`→
`Confirmed`, Expiry/Abandonment Policy proposing a terminal transition —
calls the State Machine as a single choke point rather than mutating a
state field directly. This is the direct implementation of IWC-REQ-042's
"no implementation shall introduce a transition not listed" — a single
choke point makes "is this transition listed" one code path to audit,
not nine.

### 5.2 Transition validation

Validation is table-driven: the State Machine holds §4.4's ten rows as
data (not as a chain of `if` statements), so IWC-REQ-041 ("unmodified
from the table") is enforced by construction — the table *is* the code,
not a paraphrase of it that could drift. This directly avoids repeating
143G/143H's root-cause error (a hand-authored table transcribed into
narrative prose that could silently diverge from the authoritative
version): the state table is planned to exist in exactly one place, and
every consumer (tests, the State Machine itself, documentation
generation) reads that one place.

### 5.3 Terminal enforcement

`Confirmed`, `Cancelled`, `Expired`, `Abandoned` are planned to have an
empty exit-list entry in the table structure itself (not "no code path
happens to call a transition out of them," which is a weaker guarantee).
The State Machine's transition check is planned to consult the exit list
before consulting anything else, so a terminal state's empty list is a
structural veto, not a convention.

### 5.4 Invariant checking

Three invariants are checked at the State Machine boundary on every
transition, independent of which specific transition is requested:
(a) the target state is one of the ten table states (never a
typo/unlisted string); (b) the current state's exit list contains the
target; (c) no transition into `Confirmed` is accepted without the
Confirmation Engine's own affirmative result already in hand (preventing
any caller from forging a `Confirmed` transition by calling the State
Machine directly).

### 5.5 Interruption recovery

Per IWC-REQ-121, state is planned to be persisted immediately after every
successful transition, before control returns to any caller. Recovery
reads the last-persisted state and resumes from exactly that state,
never a computed "best guess" — this requires the Session Persistence
Interface's write to be the last step of a successful transition, and
the read to be the first step of any resume, with no intervening
in-memory-only state that could be lost.

### 5.6 Resumability

Resumption (IWC §4.5, IWC-REQ-043/044) is planned as: verify owner
identity (§4.2) → read persisted state → re-enter exactly that state →
if the resumed state is `AwaitingConfirmation`, force a fresh Preview
regeneration before allowing any confirming action (never reuse a cached
Preview across a resume boundary, per IWC-REQ-105). Resuming into
`Confirmed` directly is structurally impossible because `Confirmed` is
only reachable via the Confirmation Engine's own gate (§5.4 above), never
via a generic "resume to state X" path.

**Disclosed judgment call (relates to OBS-1):** OBS-1 (143I) left open
whether a resumed session with an already-captured selection must force
fresh human re-affirmation before Preview generation, or may proceed
straight to Preview using the preserved selection. This plan adopts:
**preserve the selection verbatim (no re-prompt for the selection itself,
since IWC-REQ-127 requires partial progress preserved verbatim), but
always regenerate the Preview from that preserved selection before any
Confirmation act** (never reuse a pre-resume Preview rendering). This
satisfies IWC-REQ-127 (preservation) and IWC-REQ-105 (fresh rendering)
simultaneously without requiring a new re-affirmation act IWC-001 does
not itself mandate. This is a planning-level disposition of an
implementation-discretion gap, not a contract repair — OBS-1 remains
correctly recorded as an open contract-level observation for a future
contract revision to decide if a stricter rule is later wanted.

### 5.7 Timeout handling

Timeout is planned as data (a threshold), evaluated lazily at the next
read/resume attempt or at an explicit periodic check invoked by
whatever process already runs (never a new background daemon — see §1
row 7's runtime-neutrality constraint). An expired session transitions
to `Expired` the next time anything touches it, never "at the moment
the clock ticks past the threshold" through a live timer.

---

## 6. Persistence Planning

### 6.1 Persisted vs. transient fields

| Field class | Persisted? | Rationale |
|---|---|---|
| Session identity, owner identity, template/subject binding | Persisted | Required across every resume (§4.1–§4.3) |
| Current session state | Persisted | Required for interruption safety (IWC-REQ-121) |
| Decision Capture fields (selection, rationale, conditions, disclosure acknowledgements) | Persisted | Required for resumability (IWC-REQ-127) |
| Evidence snapshot | Persisted, timestamped | Required to detect staleness on resume/Preview-regeneration (§8.4, IWC-REQ-088) |
| Preview content and digest | **Not persisted as a cached artifact usable across a resume** — recomputed | IWC-REQ-105 forbids reusing a cached rendering across an interruption; persisting only the *last confirmed* digest (post-`Confirmed`) as part of Confirmation evidence is appropriate, persisting a pre-Confirmation Preview as something later trusted without recomputation is not |
| Confirmation evidence (digest reference, identity evidence, timestamp) | Persisted | Required as the sole input to a future Publication Handoff (§11.4) |
| Clarification log, AI conversation | Persisted (Audit Recorder's store) | Required for the seven-boundary audit reconstruction (§13.1) |
| In-memory-only scratch (e.g., a not-yet-submitted, unvalidated form draft in a transport's own UI layer) | Never persisted by this subsystem | Outside the Decision Session's own responsibility — a transport concern |

### 6.2 Preview Digest storage

The *digest of the Preview shown at the moment Confirmation was
accepted* is persisted as part of Confirmation evidence (this is what a
future Publication Handoff consumes). Any *earlier* Preview digest
(e.g., one generated for display before the human decided to confirm) is
not separately retained once superseded by a later regeneration — this
avoids a persisted trail of stale digests that a defect could later
mistake for the confirmed one.

### 6.3 Audit storage

The Audit Recorder's log is planned as append-only, keyed by session ID,
structurally partitioned by boundary (per §13.1's seven classes) so a
future verifier can query "show me only the Preview history" without
parsing a monolithic transcript (directly implementing IWC-REQ-061/062's
"structurally visible, never prose-tone-inferred" requirement one layer
up from field-separation to log-separation).

### 6.4 Resumability data

Everything needed for §5.6's resume path is a subset of §6.1's persisted
fields; no additional "resume token" or derived cache is planned, keeping
the persisted record itself the single source of truth for resumption.

### 6.5 Versioning and compatibility

The persisted session record schema is planned to carry its own schema
version field (mirroring the discipline CHGR-001's own schemas already
use), independent of the *template* version a session is bound to
(§4.3) and independent of IWC-001's own contract version. A future
IWC-001 revision (§20, §24 precedent) does not retroactively reinterpret
an already-terminal session's persisted record (IWC-REQ-182/183); the
schema version field is what lets a future reader distinguish "this
record predates a schema change" from "this record's meaning changed,"
which it structurally cannot (IWC-001 forbids the latter).

### 6.6 Migration expectations

Because no implementation exists yet, this phase plans no migration
*of existing data* — there is none. It does plan that the persisted
schema's own version field exists from the first implementing phase
onward, so that *if* a schema change is ever needed, a migration has
something to key off. This mirrors 143D's schema-versioning discipline
for CHGR records, applied here one layer earlier.

### 6.7 Privacy separation

Per IWC §14, this plan does not mandate a specific retention window
(that remains a future implementation decision per IWC-REQ-142) but does
require the persisted-record design to make a bounded-retention policy
*implementable later without a schema change* — i.e., every persisted
session record carries its own `created_at` and terminal-transition
timestamp, sufficient for a future retention sweep to act on without
needing new fields retrofitted.

### 6.8 Storage technology

**Not decided here, by design.** Per the governing prompt's own
instruction ("do not define storage technology") and per §4.10's
"structurally distinct from CHGR canonical storage" requirement, this
plan specifies only: (a) the Session Persistence Interface's read/write/
list-by-owner contract; (b) the structural non-collocation requirement
(never under any path a CHGR-manifest-driven consumer might scan); (c)
that a first implementing phase's default implementation choice (e.g., a
JSON-file-per-session directory, analogous to `.pcae/agent-locks/`'s own
existing single-file-per-concern convention already used elsewhere in
this repository) is exactly that — a first default, swappable behind
the interface without touching any of the nine components in §3–§4.

---

## 7. Confirmation Planning

### 7.1 Immutable preview

Preview Builder (§3, §4) is planned as a pure function; "immutable"
here means the *content of a given Preview* never changes after being
returned — any change to underlying Decision Capture state requires a
*new* Preview Builder call producing a *new* Preview and a *new* digest,
never an in-place mutation of a previously-returned Preview object.

### 7.2 Digest creation

Digest is computed by the Preview Builder immediately as part of
producing the Preview (§3's merge decision above) — never as a
separate, later step that could be skipped, reordered, or computed over
different content than what was actually shown.

### 7.3 Digest verification

The Confirmation Engine recomputes the digest against *current* session
content immediately before accepting a confirming action (IWC-REQ-100).
"Recompute," not "compare a stored value" — a stored digest is a
convenience cache to detect mismatch quickly, but the actual gate is
always a fresh computation, so no cached digest can itself become stale
data that is trusted without re-derivation.

### 7.4 Explicit confirmation capture

Confirmation capture requires three planned, independently-checkable
facts to co-occur: (a) a Preview was shown (session state is
`AwaitingConfirmation`); (b) the confirming action explicitly references
the Preview Digest just shown; (c) the confirming action itself is a
distinct, non-defaultable act (never inferred from any other event).
Planning these as three independently-checkable facts (not one combined
flag) directly supports IWC-REQ-107–109's three-part enumeration.

### 7.5 Stale preview rejection

If (b) above fails the fresh-recomputation check, the Confirmation
Engine returns a refusal plus a freshly regenerated Preview — it never
returns "confirmation accepted" with a stale digest, and never silently
substitutes the fresh Preview as if it had been the one reviewed.

### 7.6 Confirmation replay prevention

Once a session reaches `Confirmed` (a terminal state per §5.3), no
further confirming action against that session ID is accepted — the
State Machine's terminal-exit-list enforcement (§5.3) is the mechanism;
the Confirmation Engine additionally never accepts a confirming action
whose referenced digest belongs to a different session ID's Preview,
even if the digest values happened to collide (a belt-and-suspenders
check given the safety criticality IWC-001 §10.3 assigns this property).

---

## 8. Evidence Planning

### 8.1 Evidence collection

The Evidence Coordinator assembles evidence as a pure function of
(Decision Subject, template's evidence-class declarations, current
governing-artifact state) at context-acquisition time (`Created`→
`EvidenceReady`) and again, freshly, whenever a Preview is (re)generated
after that point (§8.4/§10.2's staleness-detection requirement) — never
assembled once and silently trusted thereafter.

### 8.2 Deterministic ordering

Evidence items within a category are planned to be ordered by a stable,
declared key (e.g., template-declared evidence-class order, then
citation path lexical order within a class) — never by assembly-time
incidental ordering (e.g., filesystem directory iteration order), so
two independent sessions against identical inputs produce byte-identical
evidence ordering, directly satisfying IWC-REQ-079.

### 8.3 Provenance preservation

Each evidence item's own provenance (source artifact, path, and — where
the source itself carries one — its own timestamp/commit) is carried
alongside the citation, never reconstructed later from the citation
alone, matching IWC §8.2's "provenance carried alongside, not asserted
separately."

### 8.4 Unavailable evidence handling

A template-declared evidence class that cannot be resolved is
represented as an explicit, structurally-distinct "gap" entry (not a
silently-omitted item, and not a null/empty placeholder indistinguishable
from "there was nothing to find") — this is planned as its own tagged
variant in the evidence-item data shape, so a Preview can render "the
following evidence could not be assembled" as its own visible section.

### 8.5 Conflicting evidence handling

Where two cited artifacts disagree, both are retained and a conflict
flag is attached to both — the Evidence Coordinator never resolves the
disagreement or silently prefers one, per IWC-REQ-085.

### 8.6 Evidence immutability

Once assembled for a given Preview generation, an evidence snapshot is
immutable for that snapshot's own lifetime; a later re-assembly (because
staleness was detected) produces a new, separately-timestamped snapshot
rather than mutating the prior one, preserving §13's audit requirement
that a verifier be able to see *which* evidence state a given past
Preview was actually built from.

---

## 9. Clarification Planning

### 9.1 Explanation and Clarification implementation

Both are planned as read-only operations over already-existing data
(template scaffolding text for Explanation; Decision Subject/evidence/
template-mechanics facts for Clarification) — neither is planned to
accept or consult any signal about which option the human currently
appears to favor, structurally enforcing IWC §9.2's "content invariant
to inferred target selection" test: the function signature itself never
receives a "current leaning" parameter, so it cannot condition on one
even inadvertently.

### 9.2 Recommendation/Persuasion prohibition enforcement

This plan places enforcement of the Recommendation/Persuasion
prohibition at the Clarification Controller's boundary as a structural
property (no function exists that could produce a recommendation),
consistent with IWC §15's framing of prompt-injection defense as
"structural, not instruction-following": there is no planned code path
where evidence or subject content, however phrased, could cause the
system to emit a preference, because no planned function accepts
"which option" as an input to its evidence-derived output.

**Disclosed judgment call (relates to OBS-2):** OBS-2 (143I) noted that
IWC-001 §9.2 dropped 143G's own explicit caveat that the
Explanation/Clarification-vs-Persuasion boundary test is
"judgment-dependent" in application, even though it is objectively
defined in principle. This plan does not resolve that disclosure gap
(it is IWC-001 text, out of this phase's authority to touch); it instead
plans the Clarification Controller's test suite (§17 below) to include
adversarial cases precisely at the boundary's judgment-dependent edge
(e.g., a factual answer that happens to be more useful to one option
than another purely because the underlying facts are asymmetric, not
because the answer was shaped) so that a future implementer has a
concrete, previously-adjudicated example set to apply the objective test
against, without the contract itself needing amendment.

### 9.3 Where enforcement belongs

Enforcement belongs entirely inside the Clarification Controller, never
distributed across transports (a CLI implementation and a web
implementation must both go through the same Controller, never each
reimplementing the boundary check independently) — this is the direct
mechanism by which IWC-REQ-161's "no transport shall silently skip"
requirement is satisfied structurally rather than by convention.

---

## 10. Publication Planning

### 10.1 Interface

The Publication Handoff interface is planned as a single, versioned data
contract: `{session_id, template_ref (with version), subject_ref,
decision_capture (selection, rationale, conditions, disclosure
acknowledgements), preview_content, preview_digest, confirmation_evidence
(identity evidence, timestamp, digest reference), audit_trail_ref}`,
exactly IWC §11.4's own enumerated list, no more and no less.

### 10.2 Data contract

The interface is planned to be read-only from the Publication side's
perspective — a future Publication implementation receives this payload
and does not write back into the session record; the session's own
lifecycle ends at `Confirmed` (IWC-REQ-120) regardless of what a future
Publication implementation does or does not do with the payload.

### 10.3 Validation

This plan specifies that the payload's own internal consistency (does
`preview_digest` match a recomputation over `preview_content`; is
`session_id` well-formed; is the session actually in state `Confirmed`)
is validated by the Interactive Workflow subsystem itself before
handoff, exactly once, as the last action the subsystem performs for
that session — not re-validated by a future Publication implementation
by trusted convention, but also not something Publication is forbidden
from re-checking; that is Publication's own future design choice.

### 10.4 Ownership transfer

Per IWC-REQ-120, once handoff occurs, the session has no further
responsibility; this plan does not specify *how* handoff is invoked
(a function call, an event, a file drop) because IWC §18.4 leaves the
callee's very existence and ownership undecided — inventing an invocation
mechanism for a callee that architecturally does not exist would itself
be inventing authority/responsibility this contract has no basis to
invent (§1 row 6). This plan's only obligation is to describe the exact
payload shape (§10.1) so that whichever future, separately authorized
phase builds Publication has an unambiguous contract to consume.

### 10.5 Failure handling

If a future Publication attempt fails after a session reaches
`Confirmed`, this plan requires that failure to be Publication's own
concern, not the session's: the session remains `Confirmed` (terminal,
per §5.3), and a Publication failure is recoverable by retrying the
handoff against the same, unchanged `Confirmed` session — never by
reopening the session to a non-terminal state, which would violate
§5.3's terminal-finality guarantee.

**This section plans the handoff boundary only. No handoff mechanism,
invocation code, or Publication implementation is built by this phase or
authorized by this plan.**

---

## 11. Transport Planning

### 11.1 Transport-independent core

Every component in §3–§4 is planned with no transport-specific
parameter anywhere in its interface (no CLI flag object, no HTTP
request object, no widget-event object) — each accepts and returns
plain data structures (session state, evidence sets, Preview content,
confirmation results), so a CLI, TUI, web, IDE, API, or mobile transport
is equally capable of driving the same core, satisfying IWC-REQ-155/156
by construction rather than by discipline alone.

### 11.2 Transport responsibilities

A transport is planned to own exactly: presenting data the core returns,
collecting input the core's interface expects, and translating between
its own native interaction model (keystrokes, HTTP verbs, widgets) and
the core's plain-data calls. A transport owns none of: transition
legality, digest computation, evidence assembly, or the
Recommendation/Persuasion boundary — all of which remain core
responsibilities per §3–§9, directly preventing IWC-REQ-161's forbidden
"transport silently skips a required check because it's easy to omit."

### 11.3 First transport

This plan recommends a CLI transport as the first implementing phase's
concrete transport (§15 below), consistent with every existing PCAE
surface (`pcae authority inspect`, `pcae governance-record inspect`)
being CLI-first; this is a sequencing choice (§15), not a narrowing of
the core's transport-independence, since the core interface planned in
§3–§10 above never references CLI concepts.

### 11.4 Evaluated transports

| Transport | Feasible under this plan's core interface? | Sequencing note |
|---|---|---|
| CLI | Yes | First implementing phase (§15) |
| TUI | Yes | No core change required; a later, separately scoped phase |
| Web | Yes | No core change required; a later, separately scoped phase |
| IDE | Yes | No core change required; a later, separately scoped phase |
| API | Yes | No core change required; a later, separately scoped phase |
| Mobile | Yes | No core change required; a later, separately scoped phase |

No transport in this table requires any change to the nine components'
interfaces as planned; each differs only in how it renders Preview
content and collects Decision Capture input, exactly the boundary
IWC §16 draws.

---

## 12. Error Model Planning

A single, closed, deterministic error taxonomy is planned (mirroring
TAMC-001/TAMPC-001's own closed-error-code discipline, extended here to
the session layer):

| Error condition | Component that detects it | Fail-closed behavior |
|---|---|---|
| Invalid transition requested | State Machine | Reject; report current state and permitted exits; no state change |
| Session already terminal (expired) | State Machine | Reject any further operation on the session ID; report terminal state |
| Session already terminal (cancelled) | State Machine | Same as above |
| Session already terminal (abandoned) | State Machine | Same as above |
| Stale Preview presented for confirmation | Confirmation Engine | Refuse; return freshly regenerated Preview and digest; no state change |
| Preview Digest mismatch | Confirmation Engine | Refuse; same as above |
| Confirmation replay (digest belongs to a different session) | Confirmation Engine | Refuse; no state change; log attempt to Audit Recorder |
| Invalid confirmation (missing identity evidence, missing digest reference, or a defaultable/implicit act) | Confirmation Engine | Refuse; require the missing element explicitly |
| Persistence read/write failure | Session Persistence Interface | Propagate failure to caller without partial state mutation; no silent retry that could double-apply a transition |
| Unavailable evidence (a declared class cannot be resolved) | Evidence Coordinator | Surface as an explicit gap in the evidence set; do not block session progress unless the template itself marks that class mandatory-before-Preview |
| Conflicting evidence | Evidence Coordinator | Surface both items with a conflict flag; do not block progress |
| Ownership mismatch on resume | Session Coordinator | Reject; fail closed; no partial resume |

Every row above defaults to "refuse/report," never "best-effort
continue," directly implementing IWC-REQ-153.

---

## 13. Extension Planning

Extension points named by IWC §17 are re-confirmed as attaching cleanly
to this decomposition without altering any of the nine components'
core interfaces:

| Extension | Attachment point in this decomposition | Confirmed non-disruptive because |
|---|---|---|
| Signatures | An additional field on Confirmation Engine's `confirmation_evidence` shape | Confirmation Engine's digest-binding logic (§7) is already signature-algorithm-agnostic; adding a signature is an additional evidence field, not a new code path |
| Enterprise identity | An additional identity-evidence source consulted by Session Coordinator's ownership-binding check (§4.2 planning) | Ownership binding is already planned as "verify identity evidence against bound identity," pluggable by identity-source, not hardcoded to one mechanism |
| Delegated authority | An extension of the identity-binding check, plus a new evidence field | No change to State Machine, Confirmation Engine's digest logic, or the human/AI boundary |
| Quorum approval | A future multi-session aggregation layer *above* this subsystem | This plan's Session Coordinator remains single-participant; quorum composes multiple single-participant sessions rather than reworking one |
| Committee workflows | Same as quorum, linked via CHGR-001's own supersession mechanics once Publication exists | No component here needs to know about committee semantics |
| Policy engines | An additional gate consulted before the State Machine accepts `DecisionSelected`→`AwaitingConfirmation` | Cannot be planned to *drive* the transition itself, only to block it — preserving IWC-REQ-165 |
| External governance systems | An additional evidence source for Evidence Coordinator | Cannot supply a selection or Confirmation without violating §4/§7's ownership of those acts |

No extension in this table requires touching the ten-state table, the
Confirmation binding, or the human/AI responsibility boundary, matching
IWC-REQ-162–164.

---

## 14. Security Planning

| Threat (IWC §15) | Planned mitigation mechanism | Component(s) |
|---|---|---|
| Replay | Confirmation Engine rejects any confirming action whose digest reference does not match the currently-valid Preview of *that* session; State Machine's terminal-exit-list blocks any post-`Confirmed` transition attempt | Confirmation Engine, State Machine |
| Prompt injection | Structural: no planned function accepts "current leaning" as an input; Clarification Controller and Evidence Coordinator treat all evidence/subject content as inert data passed through, never as instruction | Clarification Controller, Evidence Coordinator |
| Hidden defaults | Confirmation Readiness is planned as a pure function of field-presence, computed fresh on every check, never stored as an overridable flag | Session Coordinator |
| Accidental confirmation | Confirmation Engine's three-part check (§7.4) has no path satisfied by a single implicit event | Confirmation Engine |
| Stale previews | §7.5 | Confirmation Engine, Preview Builder |
| Altered evidence | Evidence Coordinator re-assembles and compares at every Preview (re)generation; a changed underlying artifact surfaces as staleness, never silently re-served | Evidence Coordinator |
| Altered templates | Session Coordinator's template binding is immutable per-session (§4.3); a mid-session template amendment surfaces as an informational note only, never auto-applied | Session Coordinator |
| Interface ambiguity | Transport Abstraction Layer is planned to render only what the core returns verbatim, with no transport permitted to reformat Preview content in a way that changes its meaning | Transport layer (all transports) |
| Session hijacking | Session Coordinator's ownership check (§4.2, §5.6) rejects any resume from a non-bound identity, fail-closed | Session Coordinator |
| Forged confirmation | Confirmation Engine requires both digest evidence and identity evidence together; neither alone suffices (§7.6, IWC-REQ-152) | Confirmation Engine |

For every row, the default response to an ambiguity or verification gap
is refusal (§12's Error Model), never a best-effort default, per
IWC-REQ-153.

**No security mechanism is implemented by this phase.** This section
plans *where* each mitigation will live and *what property* it must
guarantee; the mechanisms themselves (digest algorithm choice, identity
evidence format) are first-implementing-phase decisions (§15).

---

## 15. Test Strategy

| Category | Representative planned cases |
|---|---|
| **Unit — State Machine** | Every one of the ten states' permitted exits accepted; every unlisted transition rejected (exhaustive: 10 × 10 matrix, cross-checked against §4.4's table programmatically, not hand-enumerated, to prevent a future table/test divergence); terminal states reject every transition attempt |
| **Unit — Transition validator (merged)** | Covered by the State Machine's own exhaustive matrix above |
| **Unit — Digest** | Identical content produces identical digest across repeated calls; any single-byte content change produces a different digest; digest computation has no environment-dependence (e.g., no locale/timezone leakage into rendering) |
| **Unit — Confirmation** | Confirmation accepted only with matching digest + identity evidence + explicit act; each of the three individually withheld is rejected; a confirming action referencing a *different* session's digest is rejected even if the digest value happens to collide |
| **Unit — Persistence** | Write-then-read round-trip preserves every field exactly; a simulated crash between transition-decision and persistence-write leaves the session in its prior, still-valid state, never a half-written one |
| **Unit — Expiry** | A session past its threshold transitions to `Expired` on next access; a session just under threshold does not; template-declared thresholds override system defaults; system defaults apply when a template declares none |
| **Unit — Cancellation** | Available from every non-terminal state; never available from any terminal state; produces no Confirmation evidence, no CHGR reference |
| **Integration — session lifecycle** | End-to-end `Created`→`Confirmed` through the CLI transport, exercising every component in sequence; end-to-end `Created`→`Cancelled`; end-to-end `Created`→`Expired`; end-to-end `Created`→`Abandoned`, each via a distinct scenario |
| **Integration — publication handoff** | The interface payload (§10.1) is correctly assembled once a session reaches `Confirmed`, with no test attempting to invoke a real Publication implementation (none exists) — the test asserts payload shape and completeness only |
| **Integration — audit** | A completed session's Audit Recorder log reconstructs all seven boundaries (§13.1) distinctly, verified by a test that queries each boundary independently and confirms no cross-contamination |
| **Integration — transport independence** | The same core session, driven through two independently-implemented test harnesses simulating two different transports (e.g., a CLI-shaped driver and a plain-function-call driver standing in for a future second transport), produces identical session state and identical Preview content at every step |
| **Adversarial — replay** | A previously-successful confirming action, replayed verbatim after a subsequent Decision Capture change, is rejected |
| **Adversarial — stale preview** | Preview generated, Decision Capture changed, then the original Preview's digest presented for confirmation: rejected, fresh Preview returned |
| **Adversarial — race conditions** | Two logically-concurrent confirming actions against the same session, both referencing a valid-at-time-of-generation digest: exactly one is accepted (the one still matching current content at persistence-write time), the other is rejected as stale, never both accepted |
| **Adversarial — invalid transitions** | Every one of the 90 unlisted (10×10 minus the ~ listed) transition pairs attempted directly against the State Machine, all rejected |
| **Adversarial — concurrent expiry** | A session crossing its expiry threshold at the same moment a confirming action is submitted: whichever check runs first at persistence-write time wins deterministically, and the loser's action is rejected, never silently dropped without a reported error |
| **Adversarial — concurrent confirmation** | Two identity-bound owners is impossible by construction (single ownership per §4.2), but two rapid confirming actions from the same bound identity are tested for idempotence: the second is rejected as the session is already `Confirmed`, not double-processed |
| **Adversarial — persistence corruption** | A deliberately truncated/corrupted persisted record is read back: the Session Persistence Interface surfaces a read failure (§12's Error Model), never a silently-substituted default record |
| **Regression — every repaired transition from 143I.1** | The six specific cells 143I.1 added (Created+Cancelled/+Expired; EvidenceReady+Cancelled; AwaitingClarification+Cancelled/+Expired/+Abandoned; DecisionSelected+Abandoned; AwaitingConfirmation+Abandoned) each individually exercised and confirmed accepted |
| **Regression — Decision Existence semantics** | Each of the six IWC §7 conditions (session created; evidence assembled; clarification occurred; option selected; rationale entered; Preview generated), individually and in combination, confirmed to never report "decision exists" absent Confirmation |
| **Regression — Preview Digest binding** | Re-run of the digest-mismatch adversarial cases above as a standing regression suite, not a one-time check |
| **Regression — terminal state behavior** | Standing suite re-confirming no terminal state ever gains an exit as future components are added |

Test-suite design deliberately generates the State Machine's exhaustive
10×10 matrix *from* the same table data structure §5.2 specifies as the
single source of truth, rather than hand-writing 100 individual test
cases — this is a planning decision, not an implementation act, aimed at
preventing exactly the kind of table/prose divergence that produced
Finding B-1.

---

## 16. Dependency Graph

```
foundational components
  Session Persistence Interface  (no dependencies within this subsystem)
  Error Model                    (data/contract only; no dependencies)
        │
        ▼
shared services
  State Machine                  (depends on: Persistence Interface)
  Preview Builder                (depends on: nothing stateful — pure function;
                                   consumes Evidence Coordinator's + Session
                                   Coordinator's output as plain data)
  Audit Recorder                 (depends on: Persistence Interface)
  Expiry/Abandonment Policy      (depends on: State Machine, Persistence Interface)
        │
        ▼
workflow engine
  Evidence Coordinator           (depends on: Persistence Interface, external
                                   evidence sources — read-only)
  Clarification Controller       (depends on: Audit Recorder, template data)
  Session Coordinator            (depends on: State Machine, Evidence
                                   Coordinator, Clarification Controller,
                                   Persistence Interface)
  Confirmation Engine            (depends on: Preview Builder, State Machine,
                                   Audit Recorder)
        │
        ▼
transport adapters
  CLI (first), TUI/Web/IDE/API/Mobile (later)
        (each depends on: Session Coordinator, Confirmation Engine, and
         read access to Evidence Coordinator / Clarification Controller
         output — no transport depends on any other transport)
        │
        ▼
publication handoff
  Interface/data-contract only (§10) — depends on: Confirmation Engine's
  output shape; has no implemented callee
        │
        ▼
future integrations
  Signatures, enterprise identity, delegated authority, quorum, committee
  workflows, policy engines, external governance systems (§13) — each
  attaches at a named point without requiring a cycle back into any
  earlier layer
```

**Acyclicity check:** No component in a later layer is depended upon by
any component in an earlier layer. The one relationship requiring
explicit note is Confirmation Engine → State Machine: the Confirmation
Engine *proposes* a transition to `Confirmed` but does not itself own
state storage; State Machine remains the sole state-mutation authority
(§5.1), so the dependency is one-directional (Confirmation Engine calls
State Machine; State Machine never calls back into Confirmation Engine),
preserving acyclicity.

---

## 17. Phase Decomposition

The governing prompt's own example decomposition (143K Session
infrastructure, 143L Transition engine, 143M Confirmation workflow, 143N
Persistence, 143O Evidence orchestration, 143P Publication handoff) is
evaluated against this plan's nine-component decomposition and adopted
**with two adjustments**, disclosed below, rather than unmodified —
mirroring 143D's own disciplined independent evaluation of its governing
prompt's suggested ordering (which it partly rejected) rather than
rubber-stamping it.

| Adjustment | Reason |
|---|---|
| Merge "143N Persistence" into 143K rather than sequencing it third | Every other component (State Machine, Evidence Coordinator, Audit Recorder) depends on the Persistence Interface (§16's dependency graph); building it after the components that need it would require stubbing it out temporarily for no benefit — 143D independently made an analogous correction (rejecting its own governing prompt's CLI-before-schema and lifecycle-before-first-record suggestions) for the identical reason: build what the dependency graph says is foundational, first |
| Do not schedule a "143P Publication handoff" implementation phase at all | §10 and §18.4 above establish that Publication Handoff has no implemented callee and no assigned owner; scheduling an implementation phase for a boundary with nothing on the other side would either implement something unauthorized (a real Publication path) or produce an empty phase with no falsifiable deliverable — the interface description in this plan's §10 is the entirety of what can be responsibly produced until a future, separately authorized phase architects Publication itself |

**Resulting recommended decomposition:**

| Phase | Scope | Depends on | Deliverable |
|---|---|---|---|
| **143K** | Session infrastructure: Session Persistence Interface (+ default file-based implementation), Session Coordinator (identity/ownership/template-subject binding, Decision Capture field storage), Error Model (as shared data/contract) | This plan (143J) | A session can be created, its identity/ownership/binding persisted, and Decision Capture fields recorded — no state transitions, no evidence, no confirmation yet |
| **143L** | Transition engine: State Machine (ten-state table, exhaustive transition matrix, terminal enforcement), Expiry/Abandonment Policy | 143K | A session can move through every table-defined transition, including all six 143I.1-repaired cells, expire, be abandoned, and be cancelled — no evidence assembly, no Preview, no confirmation yet |
| **143M** | Evidence and clarification: Evidence Coordinator (deterministic assembly, categorization, staleness/conflict handling), Clarification Controller (Explanation/Clarification routing, structural Recommendation/Persuasion prohibition), Audit Recorder (all seven boundaries wired in) | 143K, 143L | A session can acquire evidence, answer clarifications under the objective boundary test, and retain a complete audit trail — no Preview/confirmation yet |
| **143N** | Confirmation workflow: Preview Builder (pure-function rendering + digest), Confirmation Engine (readiness, digest recheck, replay/stale-preview rejection, confirming-act capture) | 143K, 143L, 143M | A session can reach `Confirmed` through the full exact-digest-binding discipline; this is the first phase where Decision Existence semantics (IWC §7) become fully exercisable end-to-end |
| **143O** | First transport: CLI adapter wiring 143K–143N's core into a concrete command surface; end-to-end integration and transport-independence test harness (§15) | 143K, 143L, 143M, 143N | A human can actually drive a Decision Session through a CLI from `Created` to `Confirmed`/`Cancelled`/`Expired`/`Abandoned` |
| **143P** (independent verification) | Independent verification of 143K–143O's cumulative implementation against IWC-001 v1.1 in full, mirroring the 143E→143F precedent | 143K, 143L, 143M, 143N, 143O | Verdict on whether the built subsystem satisfies all 184 IWC-REQ items applicable to an implementation (excludes the ~20 requirements that apply only to future Publication/runtime-consumption, per §18 traceability below) |

Publication Handoff execution, signing, identity-provider integration,
multi-participant capability, and any additional transport remain
explicitly unscheduled, pending separate future authorization, per §2.1
and §13 above.

---

## 18. Requirement Traceability

Every one of IWC-001's 184 requirements is mapped below by section range
to the component(s) responsible for satisfying it, and to which
recommended phase (§17) implements it. This mirrors 143D's own
range-based traceability discipline (mapping CHGR-001's 193 requirements
to §23.x ranges and increment/deferred status) rather than repeating a
line-by-line restatement of every requirement's text.

| IWC-001 range | Section | Responsible component(s) | Phase |
|---|---|---|---|
| IWC-REQ-001–005 | Purpose | Session Coordinator (never asserts authority/Publication) | 143K |
| IWC-REQ-006–016 | Definitions | All components (terminology discipline; no code, but naming conventions in every component must match) | 143K–143O |
| IWC-REQ-017–032 | Core Invariants | Cross-cutting — enforced by the combination of Session Coordinator, State Machine, Confirmation Engine as specified in §1's constraint table | 143K–143N |
| IWC-REQ-033–039 | Session identity/ownership/binding | Session Coordinator | 143K |
| IWC-REQ-040–049 | Ten-state model, resumability, expiry, cancellation, replay, persistence boundary | State Machine, Session Persistence Interface, Expiry/Abandonment Policy | 143K, 143L |
| IWC-REQ-050–062 | AI Responsibility | Session Coordinator, Clarification Controller, Evidence Coordinator (structural prohibitions, §14) | 143K, 143M |
| IWC-REQ-063–069 | Human Responsibility | Session Coordinator (Decision Capture fields), Confirmation Engine | 143K, 143N |
| IWC-REQ-070–077 | Decision Existence | Confirmation Engine (the sole path to "decision exists") | 143N |
| IWC-REQ-078–090 | Evidence | Evidence Coordinator | 143M |
| IWC-REQ-091–097 | Clarification | Clarification Controller | 143M |
| IWC-REQ-098–112 | Confirmation | Preview Builder, Confirmation Engine | 143N |
| IWC-REQ-113–120 | State classes | Cross-cutting — enforced by never importing/exporting fields across Session state / CHGR lifecycle / runtime / project-lifecycle boundaries (§1 row 5–6); independently verifiable by absence of cross-imports | 143K–143O (structural, checked at 143P) |
| IWC-REQ-121–129 | Failure | State Machine, Session Persistence Interface, Confirmation Engine, Evidence Coordinator | 143L, 143M, 143N |
| IWC-REQ-130–136 | Audit | Audit Recorder | 143M |
| IWC-REQ-137–142 | Privacy | Session Persistence Interface (retention-ready design, §6.7); no retention policy itself implemented | 143K (design only; policy deferred) |
| IWC-REQ-143–154 | Security | Cross-cutting, per §14's table | 143K–143N |
| IWC-REQ-155–161 | Transport Independence | Core interfaces (§11.1) + Transport Abstraction (CLI) | 143K–143O |
| IWC-REQ-162–167 | Extensibility | Not implemented; confirmed non-disruptive by §13's attachment-point analysis | Deferred (no phase) |
| IWC-REQ-168–171 | Governance Responsibility | Not implemented; no new role created; Publication Handoff ownership remains explicitly unassigned | N/A — contract-level, not implementation-level |
| IWC-REQ-172–179 | Compatibility | Verified by construction: no component imports CHGR schema modules, TAMC/TAMPC modules, or `lifecycle.py`; independently re-checked at 143P | 143K–143O (checked at 143P) |
| IWC-REQ-180–184 | Amendment | Not applicable to an implementation phase (governs future contract revisions only) | N/A |

**Requirements with no implementation-phase mapping** (IWC-REQ-162–171,
180–184) are contract-governance provisions this plan correctly leaves
unimplemented — they constrain *future contract evolution and
role-assignment*, not code, and no phase in §17 is scheduled to "build"
them, consistent with §2's implementation boundary.

---

## 19. Risk Assessment

| Risk | Category | Likelihood | Impact | Mitigation | Detection strategy |
|---|---|---|---|---|---|
| State table implemented as scattered conditionals rather than single-source-of-truth data, silently diverging from §4.4 over time | Technical | Medium | High — would reproduce exactly the class of defect Finding B-1 was | §5.2's table-as-data design; §15's matrix-generated tests read the same table the implementation uses | 143P's independent verification explicitly diffs the implemented table against IWC-001 §4.4 cell-by-cell, as 143I.2 did against the repaired contract text |
| Preview/digest computed over slightly different content than what is actually displayed (a rendering-layer transformation applied after digest computation) | Technical | Medium | High — would violate the single most safety-critical property in IWC-001 (§10.3) | §3's merge of Preview Builder and Digest Generator into one pure-function call, so digest is always computed over the exact returned content, never a separately-rendered copy | Adversarial test: assert digest recomputed from the returned `preview_content` byte-for-byte always matches the returned `preview_digest` |
| A future implementer reintroduces coupling to `lifecycle.py` or CHGR schema modules for "convenience" (e.g., reusing a timestamp helper) | Governance | Low–Medium | High — would violate IWC §11.5/§19 lifecycle and compatibility independence | §1 row 5 explicit constraint; §16's dependency graph names zero such edges | 143P checks import graphs of all nine components for any reference to `lifecycle.py`, `phase_reports.py`, or `schema_resources/chgr/**` beyond read-only, non-authoritative citation |
| Migration risk: none currently, but a future schema change to persisted session records without the version field planned in §6.5 | Migration | Low (mitigated at design time) | Medium | §6.5/§6.6 mandate the version field from 143K onward | Schema tests assert every persisted record carries a version field from the first implementing phase |
| Testing risk: exhaustive 10×10 transition matrix and multi-transport parity tests are expensive to author and maintain | Testing | Medium | Medium | §15 specifies generating the matrix from the same table data structure the implementation uses, minimizing authoring burden and structurally preventing drift | Test-suite size/runtime monitored at each phase; if the matrix approach proves unwieldy, a future phase may propose (not silently adopt) a reduced representative subset, disclosed as a judgment call |
| Future extensibility risk: quorum/committee workflows are deferred, but a future phase might be tempted to "future-proof" the Session Coordinator now with speculative multi-participant fields | Extensibility | Low–Medium | Medium — speculative fields left unused are themselves a form of scope creep this repository's own engineering discipline (see CLAUDE.md-equivalent conventions) discourages | §13 explicitly plans single-participant-only fields for 143K–143O; multi-participant capability is named as an *attachment point*, not a partially-built field set | 143P checks that no unused multi-participant field exists in the shipped schema |
| Governance risk: a future phase implements Publication Handoff execution without separate authorization, treating this plan's §10 interface description as implicit permission | Governance | Low | High — would violate IWC §18.4 and CHGR §17's explicit no-runtime-implementation boundary | §10's explicit closing statement ("no handoff mechanism, invocation code, or Publication implementation is built or authorized by this phase") | Any future phase proposing Publication implementation must independently justify authorization from a separately governed decision, not cite 143J as its basis — checked by any future Independent Contract/Implementation Verifier reviewing that phase's own governing inputs |

No risk above was manufactured to pad this section; each traces to a
concrete, previously-observed failure mode in this track (B-1's root
cause for the first two rows) or to an explicit contract boundary this
plan must not cross (the governance risk row, directly mirroring IWC
§18.4's own disclosed open question).

---

## 20. Implementation Readiness

**No remaining architectural blocker exists.** Specifically:

- IWC-001 is FROZEN at v1.1, independently re-verified as internally
  coherent with zero outstanding Blocking or Non-Blocking findings
  (143I.2 CERTIFIED verdict).
- CHGR-001 remains FROZEN at v1.0, unaffected by this plan.
- The two carried-forward Observations (OBS-1, OBS-2) are both
  implementation-discretion or disclosure-only in nature, not blocking;
  this plan has disposed of both at the planning level (§5.6, §9.2)
  without touching contract text, leaving a future implementing phase
  with a concrete, non-ambiguous design to build against.
- The codebase's existing CHGR foundation (six frozen schemas, three
  read-only CLI commands, `src/pcae/governance/` package) provides a
  precedent package structure (`src/pcae/governance/session/` or
  equivalent, a first-implementing-phase naming decision) without any
  code-level dependency this plan's nine components would need to
  break.
- No open question in this plan requires a further architecture or
  contract phase before 143K can begin — the sole deliberately-left-open
  item, Publication Handoff ownership (IWC §18.4), is explicitly *not* a
  blocker for 143K–143O, because none of those phases builds across that
  boundary (§2.1, §10, §17).

**This plan alone does not authorize 143K.** Exactly as 143D's own
implementation plan did not authorize 143E, this plan's completion is a
necessary but not sufficient condition; a separate governed decision
authorizes each subsequent implementation phase.

---

## 21. Deliverables Summary

This phase produces, within this single document:

- Implementation architecture decomposition (§3)
- Component responsibility matrix (§4)
- Dependency graph (§16)
- Implementation sequencing (§17)
- Persistence plan (§6)
- Transport plan (§11)
- Confirmation plan (§7)
- Evidence plan (§8)
- Publication handoff plan — interface only (§10)
- Error model (§12)
- Security planning (§14)
- Testing strategy (§15)
- Implementation roadmap (§17)
- Risk assessment (§19)
- Implementation readiness verdict (§20)
- Requirement traceability (§18)

---

## 22. Adversarial Planning Exercises

Twenty scenarios probing whether this *plan* (not yet an implementation)
contains a decomposition error, an omitted responsibility, or a boundary
this plan itself would violate if followed literally:

1. **Two components both think they own transition legality.** Resolved:
   only State Machine does (§3 merge decision, §5.1); Confirmation
   Engine *proposes*, never applies, a transition.
2. **Preview Builder is asked to cache a rendering for performance.**
   Resolved: forbidden by design (§7.1); any caching optimization must
   still recompute on every Confirmation-adjacent check, never trust a
   cache across a resume boundary.
3. **A future engineer adds an "administrator override" to force a
   transition.** Resolved: no component in §3–§4 has an override
   parameter; adding one would require a governed IWC-001 amendment
   (IWC-REQ-042), which this plan does not propose.
4. **Evidence Coordinator is asked to rank evidence "just for UI
   sorting."** Resolved: forbidden — §8.2's deterministic-ordering rule
   is the only permitted ordering discipline; "ranking by relevance"
   is a distinct, prohibited concept (IWC-REQ-081) this plan does not
   conflate with stable ordering.
5. **A transport wants to skip showing the full Preview "for a quick
   confirm" UX shortcut.** Resolved: forbidden by §11.2 — no transport
   owns digest computation or confirmation gating; the core simply
   will not accept a confirming action without a matching, freshly
   computed digest, regardless of what the transport displayed.
6. **Two sessions for the same subject and template run concurrently.**
   Resolved: permitted — nothing in IWC-001 or this plan serializes
   sessions per subject; each session has its own identity, evidence
   snapshot, and Preview; Publication-time same-subject conflicts are
   explicitly out of this plan's scope (an OBS from 143C, CHGR-layer,
   not IWC-layer).
7. **A component silently retries a failed persistence write.**
   Resolved: forbidden by §12's Error Model — failure propagates to the
   caller; any retry policy is a future, explicit design choice at
   143K, not a silent default this plan pre-approves.
8. **The Expiry/Abandonment Policy is implemented as a background
   daemon for "responsiveness."** Resolved: forbidden by §5.7/§3's
   runtime-neutrality constraint (§1 row 7); lazy evaluation at
   read/resume time is the only planned mechanism.
9. **A future phase adds a `recommended_option` field to the session
   schema "just as metadata, never shown."** Resolved: forbidden — any
   such field is itself evidence of a Recommendation-capable code path
   even if unused today, violating §9.2's structural (not merely
   behavioral) prohibition.
10. **Confirmation Engine accepts a confirming action carrying only a
    valid digest, with identity evidence "to be added later."**
    Resolved: forbidden by §7.6/§14 — both are required together from
    the first implementing phase, not phased in.
11. **A schema migration silently reinterprets an old terminal session's
    meaning.** Resolved: forbidden by §6.5 — IWC-REQ-182/183 forbid
    retroactive reinterpretation; the version field exists precisely so
    a migration can distinguish format from meaning.
12. **Session Persistence Interface's default file-based implementation
    is placed under `.pcae/governance-records/`.** Resolved: forbidden
    by §6.8/§4.10 (IWC-REQ-049); default implementation must use a
    structurally distinct path, decided at 143K, never this one.
13. **Audit Recorder is asked to summarize AI conversation "to save
    space."** Resolved: forbidden by §6.3/IWC-REQ-134 — verbatim
    retention is mandatory.
14. **A future Publication implementation reaches back into a session's
    persisted record directly, bypassing the handoff payload.**
    Resolved: this plan's §10.2 specifies the payload as the sole input;
    a future Publication phase reaching around it would violate IWC
    §11.4's "sole input" framing — flagged here as a boundary a future
    phase must respect, not one this plan can enforce in code (no
    Publication code exists yet to constrain).
15. **Clarification Controller is given access to the human's
    in-progress (not yet submitted) selection to "personalize"
    answers.** Resolved: forbidden by §9.1 — the function signature is
    planned to never receive a "current leaning" input at all.
16. **A test suite hand-writes the 10×10 transition matrix separately
    from the implementation's own table, "for independence."**
    Resolved: rejected as a testing approach in §15 — hand-duplicating
    the table reintroduces exactly the divergence risk row one of §19's
    risk table describes; tests must read the same table the
    implementation uses, with adversarial hand-picked cases layered on
    top, not a wholesale hand-copy.
17. **A quorum extension is prototyped early "to validate the extension
    point."** Resolved: forbidden by §17 phase decomposition — quorum is
    named as an attachment point, not scheduled work; prototyping it
    would be unauthorized implementation beyond this plan's scope.
18. **Session Coordinator computes and stores an `is_authoritative`
    boolean "for convenience."** Resolved: forbidden by §1 row 6 and the
    responsibility matrix's "Authority: None" column (§4) — no
    component may expose this judgment.
19. **A future phase treats 143J's existence as authorizing 143K to
    begin without separate confirmation.** Resolved: explicitly false —
    §20 states this plan alone does not authorize implementation, exactly
    mirroring IWC-001's own "no provision authorizes a future
    implementation phase to begin merely by this contract's own freeze."
20. **The phase decomposition in §17 is treated as immutable once
    written.** Resolved: false — §17 itself states the decomposition may
    be revised if a future phase independently justifies a different
    ordering, exactly as 143D's own decomposition was partially adjusted
    here rather than inherited unmodified.

All twenty scenarios resolve deterministically against this plan's own
text; none required this plan to add a new component, a new persisted
field, or a new authority beyond what §1–§18 already specify.

---

## 23. Validation

The following validations were run against this phase's own state (a
documentation-only phase; no source code changed):

- `pcae check` — passed (session coherence verified).
- `pcae health` — to be re-confirmed immediately before `pcae phase
  complete` is invoked, per this repository's standing acceptance-check
  discipline.
- `python -m pytest -m fast_green -n auto` — to be re-run immediately
  before phase completion, per this repository's standing requirement
  that the fast_green sentinel be actually re-executed and cited (not a
  placeholder value) even for a doc-only phase.
- Planning consistency review — self-conducted throughout §1–§22 above;
  every component in §3 traces to at least one IWC-001 requirement
  range in §18; every risk in §19 traces to either an observed defect
  class (B-1) or an explicit contract boundary (§18.4).
- Dependency validation — §16's graph independently checked for cycles;
  none found.

`pcae push readiness` and the actual commit/push sequence are performed
after this document is finalized and the task contract's acceptance
checks are re-confirmed, per this repository's governed commit
procedure.

---

## 24. Explicit No-Go

This phase does **not**, and this document does not authorize any future
phase to construe it as having:

- Implemented Session Coordinator, State Machine, Confirmation Engine,
  Preview Builder, Evidence Coordinator, Clarification Controller,
  Session Persistence Interface, Expiry/Abandonment Policy, or Audit
  Recorder.
- Implemented persistence of any kind.
- Implemented Preview Digest computation or verification.
- Implemented confirmation capture.
- Implemented publication or any Publication Handoff invocation
  mechanism.
- Created a CHGR, assigned a `chgr-<uuid4>` identifier, or written
  anything under `.pcae/governance-records/`.
- Implemented runtime consumption of any kind.
- Implemented authority resolution of any kind.
- Implemented any execution capability.
- Modified `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
  (CHGR-001).
- Modified `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001).
- Modified `docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
  (TAMC-001).
- Modified
  `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (TAMPC-001).

Runtime remains: **State: Observed. Maximum Capability: observe.
Execution Availability: unavailable.** — unchanged before and after this
phase, independently confirmable via `pcae runtime inspect`.

---

## 25. Exit Criteria

Phase 143J is complete because:

1. The implementation architecture is fully decomposed (§3) — nine
   components, each independently justified, none invented beyond the
   governing prompt's own eighteen candidates.
2. Component ownership is defined (§4) — one owner per responsibility,
   no shared-write state between components.
3. Dependency ordering is complete (§16) — acyclic, four layers plus a
   named-but-unbuilt handoff layer and a deferred future-integration
   layer.
4. Test strategy is complete (§15) — unit, integration, adversarial, and
   regression categories all populated with concrete, IWC-REQ-traceable
   cases.
5. Risks are documented (§19) — seven risks, each with likelihood,
   impact, mitigation, and detection strategy, none manufactured.
6. Implementation sequencing is justified (§17) — the governing prompt's
   example decomposition independently evaluated, two adjustments
   disclosed with reasons, mirroring 143D's own disciplined evaluation
   method.
7. No implementation has occurred (§24) — confirmed by the Explicit
   No-Go list and by this phase's task contract's own allowed-files
   scope (documentation and governance metadata only).
8. Runtime remains unchanged (§24) — confirmed unchanged, Observed/
   observe/unavailable.
9. The implementation roadmap is sufficient to begin 143K without
   reopening architecture (§20) — no remaining architectural blocker;
   the two carried-forward Observations (OBS-1, OBS-2) are disposed of
   at the planning level (§5.6, §9.2) without requiring further
   architecture work before 143K.

---

## 26. Expected Outcome and Recommended Next Phase

This document is the authoritative implementation blueprint for the
Interactive Workflow subsystem: a nine-component decomposition, a
one-owner-per-responsibility matrix, an acyclic dependency graph, a
six-phase implementation roadmap (143K–143P), a closed error taxonomy,
a security-mitigation map, a four-category test strategy, a full
requirement-traceability table, a seven-item risk assessment, and an
unambiguous implementation-readiness verdict — establishing a governed,
independently justifiable path from IWC-001 v1.1's verified contract
text to production implementation, while preserving every invariant
CHGR-001 and IWC-001 already froze.

**The expected next phase is 143K — Interactive Workflow Session
Infrastructure Architecture & Skeleton Implementation**, scoped per
§17's table to Session Persistence Interface, Session Coordinator, and
the shared Error Model.

**This recommendation does not authorize 143K.**
