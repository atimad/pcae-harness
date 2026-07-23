# IWC-001 v1.1 — Interactive Workflow Contract

## Contract identity and status

**Contract:** IWC-001
**Version:** 1.1
**Status:** FROZEN
**Frozen by:** Phase 143H — Canonical Human Governance Record Interactive
Decision Workflow Contract Freeze
**Revised by:** Phase 143I.1 — Interactive Workflow Contract
State-Transition Table Repair (§24 below; repairs Finding B-1, the sole
Blocking finding from Phase 143I's Independent Verification; no semantic
expansion)
**Architecture basis:** Phase 143G — Canonical Human Governance Record
Interactive Decision Workflow Architecture, GLP-001 §6.1 Stage 1 —
Architecture, applied to the interactive-workflow layer that sits above the
already-frozen CHGR-001 schema/publication contract
(`docs/PHASE_143G_CANONICAL_HUMAN_GOVERNANCE_RECORD_INTERACTIVE_DECISION_WORKFLOW_ARCHITECTURE.md`)
**Governed subject:** The **Interactive Decision Session** by which a named
human authority reviews a Decision Subject, an already-governed Decision
Template (CHGR-001 §6), and machine-assembled evidence; optionally supplies
rationale and conditions; previews exact confirmable content; and performs
Confirmation (CHGR-001 §7) — the bounded, ephemeral, pre-publication
workflow layer this contract freezes purpose, invariants, session model,
AI/human responsibility separation, decision-existence semantics, evidence
discipline, clarification boundary, confirmation mechanics, state
separation, failure handling, audit properties, privacy boundaries,
security posture, transport independence, extensibility, governance
responsibility, compatibility, and amendment discipline for.

IWC-001 is the sole normative authority governing **the Interactive
Decision Session layer** that produces the input to CHGR-001 Publication.
It does not govern the Canonical Human Governance Record artifact class
itself (that remains CHGR-001's sole normative authority, unmodified), does
not redefine GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001 (collectively,
"the framework contracts"), does not redefine or narrow the Typed Authority
Model Consumption Contract (TAMC-001) or the Typed Authority Model
Production Consumption Contract (TAMPC-001), does not modify GPC6-001,
GPC6R-001, or GPC6C-001, and does not modify or reinterpret the existing
`docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` record. Where this
contract cites CHGR-001, a framework contract, a GPC6-family contract, or a
Typed-Authority-family provision, the citation illustrates an obligation
this contract itself imposes on the Interactive Decision Session layer
specifically; it does not redefine the underlying provision (mirrors
CHGR-001 §1's identical illustrative-citation discipline, itself mirroring
GPC6C-001 §1, GPC6R-001 §1, GPC6-001 §1, and AGOC-001 §1 AGOC-REQ-002).

Phase 143G's Architecture stage is the approved design basis for every
section below. This contract independently re-derives every requirement
directly from
`docs/PHASE_143G_CANONICAL_HUMAN_GOVERNANCE_RECORD_INTERACTIVE_DECISION_WORKFLOW_ARCHITECTURE.md`,
treated as evidence of architectural intent, never as contractual
authority; from `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
(CHGR-001), read directly and cited by `CHGR-REQ-###` identifier throughout
rather than assumed from 143G's own summary of it; from
`docs/PHASE_143A_CANONICAL_HUMAN_GOVERNANCE_RECORD_ARCHITECTURE.md`,
`docs/PHASE_143C_CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT_INDEPENDENT_VERIFICATION.md`,
`docs/PHASE_143D_CANONICAL_HUMAN_GOVERNANCE_RECORD_IMPLEMENTATION_PLANNING.md`,
`docs/PHASE_143E_CANONICAL_HUMAN_GOVERNANCE_RECORD_SCHEMA_AND_ARTIFACT_FOUNDATION_IMPLEMENTATION.md`,
`docs/PHASE_143F_CANONICAL_HUMAN_GOVERNANCE_RECORD_SCHEMA_AND_ARTIFACT_FOUNDATION_INDEPENDENT_VERIFICATION.md`,
and `docs/PHASE_143F.1_PHASE_143E_CANONICAL_REPORT_AND_METADATA_REPAIR.md`,
each read as evidence of what already exists in the repository (the six
frozen CHGR schemas, the three read-only `pcae governance-record` CLI
commands, and the confirmed absence of `DecisionSession`, session
persistence, and `.pcae/governance-records/`), never as contractual
authority in its own right; and from
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` and
`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`,
read directly for §19's compatibility analysis rather than assumed from
143G's own summary of them. Where this contract and Phase 143G differ in
force, this contract is normative for Interactive Decision Session
compliance-evaluation purposes only, and any such difference is itself a
defect to be resolved by a governed contract revision, not by silently
preferring one document over another in practice. Where Phase 143G left a
design question genuinely open, this contract resolves it explicitly and
discloses the resolution as a judgment call, rather than silently picking
one reading (see §4.6 and §18.4 below).

This is contract text only. It does not implement any session, does not
implement any CLI, does not implement any storage or persistence mechanism,
does not implement any migration, does not implement any cryptographic
signing, does not implement any runtime enforcement, does not implement any
authority-resolution behavior, does not modify CHGR-001, TAMC-001,
TAMPC-001, GPC6-001, GPC6R-001, or GPC6C-001, does not modify the existing
GPC6-REQ-075(b) election record, and does not create any new human
governance decision. It preserves every provision of CHGR-001, GLP-001,
GAC-001, PGP-001, PPA-001, AGOC-001, TAMC-001, TAMPC-001, GPC6-001,
GPC6R-001, and GPC6C-001, unchanged. Runtime remains Observed / observe /
unavailable throughout every operation this contract governs.

## 0. Normative Language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**,
**SHOULD**, **SHOULD NOT**, and **MAY** are normative, with the meanings
given in GLP-001 §0, which this contract adopts unchanged.

This contract does not itself perform, and is not evidence of, any act of
creating, resuming, presenting, clarifying, capturing, confirming, or
publishing an Interactive Decision Session or a CHGR. No provision below
authorizes a future implementation phase to begin merely by this
contract's own freeze; §17 and the Non-Goals below state this explicitly.

Every mandatory obligation below is stated in §21 as a single, atomic,
independently identified `IWC-REQ-###` requirement. Sections 1–20 state
the normative rules in narrative form; §21 is the authoritative,
falsifiable enumeration of those rules. Where narrative prose in §1–§20
and a requirement in §21 differ in force, §21 is normative.

---

## 1. Purpose Contract

The Interactive Decision Session exists solely to enable a human authority
to make a governed decision that may later become a Canonical Human
Governance Record (CHGR-001 §2 "Human Decision," §7 "Confirmation," §8
"Publication"). It exists to satisfy CHGR-REQ-039 through CHGR-REQ-048
(the Interactive Decision Contract) and CHGR-REQ-059 through CHGR-REQ-066
(the Confirmation Contract) with a concrete, falsifiable session model,
mirroring exactly how Phase 143G's architecture (§1) filled the gap
between CHGR-001's already-frozen text and a buildable design.

The workflow itself SHALL NEVER create authority. Authority derives only
from the confirmed Human Governance Act that Publication (CHGR-001 §8)
converts into a published CHGR (CHGR-REQ-090). This contract freezes, as
its central and non-negotiable governing principle:

> A Decision Session is scaffolding for producing a CHGR; it is never
> itself evidence of a Human Governance Act, is never published, is never
> assigned a `chgr-<uuid4>` identifier, and is never referenced by any
> future consumer as if it were a record (143G §1.2).

Normatively, and without exception:

- A Decision Session SHALL NEVER be treated as, substituted for, or
  conflated with a CHGR.
- A Decision Session SHALL NEVER, by reaching any state defined in §4
  below, itself convey authority.
- A Decision Session SHALL NEVER, by reaching any state defined in §4
  below, itself constitute Publication.

## 2. Definitions

The following terms are normative and SHALL be used with exactly the
meaning given here by every document, phase, or future implementation that
invokes this contract, in addition to the terms CHGR-001 §2, GLP-001 §4,
GAC-001 §3, PGP-001 §3, PPA-001 §3, and AGOC-001's own terminology already
define, which this contract adopts unchanged where applicable. This
contract does not redefine any CHGR-001 term (`Human Governance Act`,
`Canonical Human Governance Record`, `Decision Template`, `Decision
Subject`, `Human Decision`, `Confirmation`, `Publication`, `Supersession`,
`Revocation`, `Suspension`, `Assurance Level`, `Legacy Governance Record`,
`Interactive Decision Session`); it adopts CHGR-001 §2's definition of
"Interactive Decision Session" unchanged and elaborates it operationally
below.

- **Decision Session** — the bounded, ephemeral, operational context,
  identified by a `CDS-<uuid4>` identifier, in which one human authority
  works through one Decision Template instance toward, at most, one Human
  Decision (143G §1.1, §2.1).
- **Session State** — the current position of a Decision Session within
  the ten-state model §4.4 below freezes; distinct from, and never a
  substitute for, CHGR record lifecycle state (CHGR-001 §13.1).
- **Decision Capture** — the session-local act of recording a human's
  selected option, optional rationale, optional conditions, inherited
  scope, inherited authority basis, and acknowledged disclosures prior to
  Confirmation (143G §8).
- **Confirmation Readiness** — a computed boolean, true only when every
  field Decision Capture requires is present and every disclosure the
  selected option attaches is acknowledged; never manually overridden
  (143G §8.1).
- **Preview** — the exact, verbatim rendering of the content Confirmation
  would cause to be published, generated deterministically from Decision
  Capture's current state (143G §1.3 stage 9, §9).
- **Preview Digest** — a content digest of the exact Preview at the moment
  it is generated, recomputed immediately before Confirmation is accepted
  (143G §9.2).
- **Explanation** — restating a Decision Template's fixed scaffolding or
  boundary text in different words, on request, without introducing any
  new claim (143G §7.1).
- **Clarification** — answering a factual question about the Decision
  Subject, evidence, or template mechanics, whose content does not vary
  with any inferred target selection (143G §7.1, §7.2).
- **Recommendation** — suggesting which option a human "should" pick;
  forbidden outright, performed by no architectural element (143G §7.1).
- **Persuasion** — any framing, emphasis, repetition, or selective evidence
  presentation intended to move a human toward a particular option;
  forbidden outright (143G §7.1).
- **Disclosure Acknowledgement** — a distinct, tracked session field
  recording that a human has acknowledged a mandatory non-effect statement
  attached to their in-progress selection; never inferred from a passive
  signal (143G §6.4).
- **Session Audit Evidence** — every artifact a Decision Session produces
  up to and including `Confirmed` (conversation, clarification, proposal,
  evidence, Preview, Decision Capture, Confirmation evidence); retained
  per §13 below, citable by a future verifier, never itself canonical, and
  never itself carrying independent authority (143G §13.2).
- **Publication Handoff** — the precise, described-but-unimplemented
  boundary at which a session reaching `Confirmed` hands its bound
  template reference, captured decision content, exact Preview and
  Preview Digest, and Confirmation evidence to a future Publication
  implementation, after which the session has no further responsibility
  (143G §18.2).

## 3. Core Invariants

The following fourteen properties are frozen as mandatory, non-negotiable,
and immutable for every Decision Session, regardless of transport,
template, or future extension. Each is independently re-derived from
Phase 143G's architecture and from CHGR-001's own core invariants (§3),
restated here at session-architecture granularity; none is invented by
this contract, and none may be waived by convenience or by a future
implementation's own discretion.

1. **AI assistance only.** PCAE tooling may assemble, render, validate,
   explain, and preview; it may never select, infer, complete, or confirm
   a Human Decision on a human's behalf (§5 below; CHGR-REQ-020).
2. **Human-exclusive decision authority.** Selecting a decision from a
   Decision Template's closed option set is exclusively a human act;
   no architectural element may perform it on a human's behalf (§6 below;
   CHGR-REQ-019).
3. **Explicit confirmation.** No Decision Session may reach `Confirmed`
   through any mechanism other than a distinct, non-defaultable
   Confirmation act bound to the exact Preview Digest (§10 below;
   CHGR-REQ-059–066).
4. **Deterministic workflow.** Given identical inputs (Decision Subject,
   bound Decision Template version, evidence-source state), two
   independent sessions SHALL assemble identical evidence and render
   identical Previews (§8.1, §10.1 below; CHGR-REQ-023 restated one layer
   earlier).
5. **Interruption safety.** A Decision Session interrupted at any
   non-terminal state SHALL be recoverable from its last-persisted state
   without loss, corruption, or silent advancement (§12 below).
6. **Resumability.** A Decision Session in `Created` through
   `AwaitingConfirmation` MAY be resumed only by the identity bound at
   creation, re-entering exactly the stage it left (§4.5, §4.7 below).
7. **Replay resistance.** A Confirmation act SHALL be rejected unless it
   carries evidence tied to the specific, currently-valid Preview Digest;
   a Decision Session ID, once terminal, SHALL NEVER be reused for a new
   interaction (§10.3, §4.9 below).
8. **Provenance completeness.** Every artifact a Decision Session produces
   up to `Confirmed` SHALL be retained as Session Audit Evidence sufficient
   to reconstruct what was presented, discussed, selected, and confirmed
   (§13 below).
9. **Authority neutrality.** Reaching `Confirmed` is evidence a human
   performed Confirmation inside that session; it is never, by itself,
   proof the human held eligible authority under the bound template (§11.2
   below; CHGR-REQ-090–097 restated one layer earlier).
10. **Transport independence.** Every requirement in this contract SHALL be
    satisfiable by a CLI, TUI, web, IDE, API, or mobile transport, and
    SHALL NOT depend on any transport-specific mechanism (§16 below).
11. **Lifecycle independence.** A Decision Session's state SHALL NEVER
    substitute for, be substituted by, or advance PCAE phase or task
    lifecycle state (§11.5 below).
12. **Runtime independence.** No Decision Session state, before or after
    `Confirmed`, is visible to, consumable by, or capable of triggering
    any runtime capability change (§19 below; CHGR-REQ-029, CHGR-REQ-142).
13. **Auditability.** A future verifier SHALL be able to distinguish, from
    the session's own retained state alone, AI conversation, clarification,
    proposal, evidence, Preview, Decision Capture, and Confirmation as
    seven structurally separate classes (§13 below).
14. **Privacy separation.** Temporary interaction state SHALL NEVER become
    canonical governance state automatically; only an explicit Publication
    Handoff (§2 above, §11.4 below) converts Session Audit Evidence into
    CHGR provenance (§14 below).

## 4. Session Contract

### 4.1 Identity

Every Decision Session SHALL carry exactly one canonical session
identifier, of the form `CDS-<uuid4>` ("Confirmable Decision Session"),
assigned at session creation, collision-resistant without requiring a
central counter, and structurally distinct in prefix and allocation
timing from a CHGR's own `chgr-<uuid4>` identifier and from any Typed
Authority Model identifier (143G §2.1–§2.2). A session identifier SHALL
NEVER be pre-minted as, reused as, or substituted for a future CHGR's own
canonical identifier (CHGR-REQ-076's Publication-time-only assignment rule
is never violated by a session's own identity allocator).

### 4.2 Ownership

A Decision Session SHALL be bound at creation to the identity of the
human who created it. This binding SHALL be evaluated, and enforced, at
every subsequent resumption attempt: a resumption request from an
identity other than the one bound at creation SHALL be rejected, fail
closed (143G §2.3, §12).

### 4.3 Template and Subject Binding

A Decision Session SHALL be bound at creation to exactly one Decision
Template (identified inclusive of its specific version) and exactly one
Decision Subject, for its entire lifetime. Neither binding SHALL be
silently swapped mid-session; switching either requires abandoning the
session and creating a new one (143G §1.3 stages 1–2, §5).

### 4.4 The Ten-State Model

This contract freezes the following ten states as the complete Decision
Session state model. The states themselves, their entry conditions, and
`AwaitingDecision`'s and the four terminal states' exit lists are
unmodified from 143G §10.1. The five non-terminal states other than
`AwaitingDecision` — `Created`, `EvidenceReady`, `AwaitingClarification`,
`DecisionSelected`, and `AwaitingConfirmation` — had their exit lists
widened by Phase 143I.1 (§24 below) to make explicit the
`Cancelled`/`Expired`/`Abandoned` exits that §4.7, §4.8, §12, and §16
already required to be universally available; no state was added,
removed, merged, or renamed, and no entry condition changed:

| State | Entry condition | Permitted exits |
|---|---|---|
| `Created` | Session opened, bound to template + subject | `EvidenceReady`, `Cancelled`, `Expired`, `Abandoned` |
| `EvidenceReady` | Context acquisition complete | `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `AwaitingDecision` | Options presented, no selection yet | `AwaitingClarification`, `DecisionSelected`, `Expired`, `Cancelled`, `Abandoned` |
| `AwaitingClarification` | A clarification exchange is in progress | `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `DecisionSelected` | Selection plus required fields/disclosures captured | `AwaitingConfirmation`, `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `AwaitingConfirmation` | Preview generated, awaiting Confirmation | `Confirmed`, `DecisionSelected`, `Cancelled`, `Expired`, `Abandoned` |
| `Confirmed` | Confirmation act completed and digest-matched | Terminal for session purposes; hands off per §2's Publication Handoff |
| `Cancelled` | Human explicitly cancels before `Confirmed` | Terminal |
| `Expired` | Maximum lifetime elapsed before `Confirmed` | Terminal |
| `Abandoned` | Inactivity past a shorter idle threshold, or explicit discard | Terminal |

No implementation SHALL add, remove, merge, or rename a state in this
table, and no implementation SHALL introduce a transition not listed
above, without a governed amendment to this contract (§20 below). No
terminal state (`Confirmed`, `Cancelled`, `Expired`, `Abandoned`) has any
exit; none may transition back into an active state, and none may
transition into another terminal state.

### 4.5 Resumability

A Decision Session in `Created` through `AwaitingConfirmation` MAY be
resumed by the identity bound at creation (§4.2). Resumption SHALL always
re-enter exactly the stage left; it SHALL NEVER fast-forward past
Confirmation, and SHALL NEVER resume directly into `Confirmed` (143G
§2.3, §11). Confirmation, once resumed to, SHALL always be freshly
performed against a freshly-validated Preview (§10.2 below).

### 4.6 Judgment call: adoption of the ten-state model unmodified

Phase 143G's governing prompt named ten candidate states in its own §10;
Phase 143G's architecture independently derived and adopted all ten,
unmodified, because each names a structurally distinct condition no other
listed state can represent without loss of information — precisely the
same fail-closed reasoning CHGR-001 §13.4 used to justify retaining
`invalidated` in its own eight-state record model against an abbreviated
prompt-provided list. This contract adopts 143G's ten-state model without
narrowing, for the same reason: collapsing `Expired` and `Abandoned` into
one state would destroy the diagnostic distinction between "this ran out
of allotted time" and "this was quietly walked away from" (143G §10.3);
collapsing `AwaitingClarification` into `AwaitingDecision` would destroy
the auditable boundary §7 and §13 below require between ordinary
option-review and an active clarification exchange. No prompt-provided
list in this phase's own governing prompt proposed fewer than ten states,
so no reconciliation judgment analogous to CHGR-001 §13.4 was required
here; this subsection exists to disclose that the adoption was
independently re-verified, not merely inherited.

### 4.7 Expiry

Every Decision Session SHALL carry a template-defined or system-default
maximum lifetime. An expired session SHALL transition to `Expired`, never
silently extend (143G §2.3).

### 4.8 Cancellation

A human MAY cancel a Decision Session at any point before `Confirmed`.
Cancellation SHALL be terminal and SHALL produce no CHGR, no partial
record, and no residual claim on the session's template/subject binding
(143G §2.3, §9.1).

### 4.9 Replay Prevention

A session identifier, once it reaches `Confirmed`, `Cancelled`,
`Expired`, or `Abandoned`, SHALL NEVER be reused for a new interaction; a
new decision requires a new session, even against the same template and
subject (143G §2.3, mirroring CHGR-REQ-077's non-reuse rule one layer
earlier).

### 4.10 Persistence Boundary

A Decision Session's state is operational, ephemeral storage, structurally
distinct from CHGR canonical storage. No implementation SHALL colocate
session state files under `.pcae/governance-records/records/` or any path
a manifest-driven consumer might mistake for a frozen CHGR schema instance
(143G §2.3, §14).

## 5. AI Responsibility Contract

### 5.1 Permitted Operations

PCAE tooling MAY, and only MAY:

- assemble governing and supporting evidence and authoritative context;
- present a Decision Template's fixed scaffolding, options, consequence
  statements, and mandatory non-effect statements;
- validate that a selection exists among the closed set and that required
  fields are present;
- explain a Decision Subject, evidence item, or template's own fixed
  meaning, on request;
- answer a Clarification whose content does not vary with any inferred
  target selection (§9 below);
- identify conflicts, gaps, or staleness in assembled evidence or a bound
  template version, surfacing them rather than resolving them;
- summarize the consequences and non-effects a selected option actually
  carries, drawn verbatim from the template;
- generate a deterministic Preview from current Decision Capture state.

(143G §3.1; CHGR-REQ-032.)

### 5.2 Prohibited Operations

PCAE tooling SHALL NOT, under any circumstance, including where the
system judges itself confident of what the human would want:

- select, choose, or pre-select an option on a human's behalf;
- infer a selection from partial input, or optimize a selection toward
  any outcome;
- fabricate, complete, reinterpret, broaden, or narrow a human-authored
  rationale or condition field;
- silently modify a human's already-made selection;
- infer consent from silence, inactivity, timeout, or the mere passage of
  a screen;
- fabricate a rationale or condition the human did not author;
- perform Confirmation on a human's behalf;
- elevate the assurance level, authority basis, or eligibility claimed
  for a decision beyond what session evidence actually supports;
- persuade a human toward a particular option, whether through framing,
  emphasis, repetition, or selective evidence presentation;
- manufacture, imply, or suggest authority the session's own evidence does
  not support.

(143G §3.2; CHGR-REQ-033–036, CHGR-REQ-057.)

Each prohibition above is independently frozen as its own requirement in
§21.5 below; none is merged with another to avoid dilution of any single
prohibition's falsifiability.

### 5.3 Mechanical Separation

A Decision Session's internal representation SHALL make the AI-authored/
human-authored boundary structurally visible through distinct fields
(e.g., `machine_scaffolding_text`, `machine_boundary_language`,
`human_rationale_text`, `human_conditions_text`, `human_selection_id`),
never through a single free-form transcript a verifier would have to
parse by prose tone (143G §3.3; CHGR-REQ-037, CHGR-REQ-038).

## 6. Human Responsibility Contract

The following operations remain exclusively human, in every Decision
Session, regardless of transport or template:

| Responsibility | Never implicit because |
|---|---|
| Selecting a decision from the closed option set | Absence of input is never a selection (CHGR-REQ-021) |
| Supplying rationale where the bound template requires it, or choosing to leave it blank where optional | Optional unless the template's own text mandates it (CHGR-REQ-040) |
| Acknowledging every mandatory non-effect statement attached to the in-progress selection | Acknowledgement is a tracked, explicit field, never inferred from having merely viewed the screen (§8.4 below) |
| Reviewing the exact Preview before Confirmation | CHGR-REQ-047, CHGR-REQ-060 |
| Performing Confirmation as a distinct, deliberate, non-defaultable act | CHGR-REQ-059–062 |

(143G §4.)

No architectural element permits implicit consent. No sequence of
intermediate actions — reviewing evidence, asking clarifying questions,
selecting an option, entering rationale, viewing a Preview — SHALL, by
itself or in any combination short of Confirmation, constitute a
decision. Every one of the five responsibilities above requires session
state to record an explicit, attributable human action before the
session may advance past the stage that action gates (§4.4's state model
formalizes the gating).

## 7. Decision Existence Contract

This contract freezes the following semantic definition as immutable and
non-negotiable:

**A governance decision does not exist** merely because:

- a Decision Session is created;
- evidence is assembled;
- clarification occurs;
- an option is selected;
- rationale is entered;
- a Preview is generated.

**A governance decision exists only after** the human authority performs
the distinct Confirmation act (§10 below) over the exact, currently-valid
Preview content.

Any one of the six listed conditions, individually or in combination,
short of Confirmation, SHALL NEVER be treated, stored, indexed, or
referenced as if a decision had been made (143G §8.2, restating
CHGR-REQ-066 and CHGR-001 §16.2's silence/timeout/default prohibition at
the session-internal layer). This invariant is immutable: no future
implementation, transport, or extension (§17 below) may introduce a path
that satisfies "a decision exists" through any condition other than
completed Confirmation.

## 8. Evidence Contract

### 8.1 Deterministic Assembly

Evidence presentation is a pure function of the Decision Subject, the
bound template's evidence-class declarations, and the state of governing
artifacts at context-acquisition time. Given identical inputs, two
independent sessions against the same template and subject SHALL assemble
identical evidence (143G §6.1; CHGR-REQ-023 restated one layer earlier).

### 8.2 Evidence Categories

Governing references and supporting references SHALL be cited by path or
identifier, never inlined-and-editorialized, and SHALL NEVER be ranked or
weighted by PCAE tooling; a "supporting" label SHALL be template-declared,
never AI-judged. Each cited artifact's own provenance SHALL be carried
alongside its citation, not asserted separately (143G §6.2).

### 8.3 Uncertainty, Unavailability, and Conflict Disclosure

Where an evidence item's currency cannot be confirmed, the session SHALL
surface this explicitly rather than presenting the citation as trustworthy
(fail-closed; CHGR-REQ-030 restated at the evidence layer). A
template-declared evidence class that cannot be resolved SHALL be
presented as an explicit gap, never omitted silently. Where two cited
artifacts disagree, the session SHALL present both and flag the conflict;
it SHALL NEVER silently pick the "more likely correct" one (143G §6.2).
Any evidence PCAE computes (e.g., a derived count of prior CHGRs for the
subject) SHALL be labeled as derived/computed, distinct from evidence
sourced verbatim from another artifact.

### 8.4 Prevention of Evidence Substitution

A session SHALL NOT allow evidence assembled for one Decision Subject to
be silently reused for another. A session SHALL NOT present evidence
assembled at session-creation time unchanged at Confirmation time if the
underlying artifacts changed in between, without surfacing that drift
(143G §6.3; §12 below, "stale evidence").

### 8.5 Disclosure Acknowledgement

Every mandatory non-effect statement a template attaches to an
in-progress selection SHALL require a distinct, tracked Disclosure
Acknowledgement before the session may proceed to Preview generation.
Acknowledgement SHALL NEVER be inferred from "the human scrolled past
this text" or any other passive signal (143G §6.4).

## 9. Clarification Contract

### 9.1 The Four Distinct Acts

| Act | Permitted? | Performed by |
|---|---|---|
| Explanation | Yes — bounded to the template's own meaning | AI |
| Clarification | Yes — factual, content invariant to inferred target selection | AI |
| Recommendation | **No — forbidden outright** | Nobody |
| Persuasion | **No — forbidden outright** | Nobody |

(143G §7.1.)

### 9.2 The Objectively Testable Boundary

The dividing line between permitted Explanation/Clarification and
forbidden Recommendation/Persuasion is: **whether the AI's output could
be true or useful regardless of which option the human ultimately picks.**
A valid Clarification answer SHALL NOT change in content based on which
option the AI infers the human is leaning toward. If an answer would
differ depending on an inferred target selection, it is Persuasion by
construction and is out of bounds (143G §7.2). Every clarification
exchange SHALL be logged verbatim as Session Audit Evidence (§13 below)
precisely so this boundary remains auditable after the fact, not merely
asserted by design.

### 9.3 No Coercive Reframing

Clarification SHALL NOT reframe an option's consequence or non-effect
text; it may only explain the template's own fixed words, never
substitute new wording, even wording the AI judges clearer (143G §7.3,
mirroring CHGR-REQ-035's prohibition on reinterpreting a human-authored
field, extended here to the template's own machine-authored text).

## 10. Confirmation Contract

### 10.1 Confirmation as a Distinct Stage

Once Decision Capture reaches Confirmation Readiness, the session SHALL
compute a Preview that is a pure function of captured content; this
Preview SHALL be fixed the instant Confirmation begins. The human SHALL
be shown the literal content that will become the CHGR's
provenance-recorded preview (CHGR-REQ-085) — no paraphrase, no summary
view (143G §9.1).

### 10.2 Stale-Preview Rejection

The session SHALL recompute the Preview Digest against current session
content immediately before accepting a confirming action. A mismatch —
caused by, e.g., a concurrent template amendment invalidating cached
evidence, or a defect that mutated session state after Preview generation
— SHALL fail closed: Confirmation SHALL be refused, and the human SHALL be
shown a freshly regenerated Preview rather than being allowed to confirm
content they did not actually review (143G §9.2).

### 10.3 Exact-Content Binding

Confirmation SHALL bind to the exact digest of what was shown, not to
"the current state of the session" in the abstract. No implementation may
satisfy Confirmation by checking merely "has the human clicked confirm at
some point in this session" — it SHALL check "does the human's confirming
action carry evidence tied to this specific, currently-valid Preview
Digest" (143G §9.3). This is frozen as the single most safety-critical
property in this contract.

### 10.4 Replay Protection

A Confirmation act SHALL be bound to a specific Preview-content digest;
presenting that same confirmation evidence against different content
SHALL be rejected, never silently accepted (143G §9.1).

### 10.5 Interruption Handling

If a session is interrupted between Preview generation and Confirmation,
resuming SHALL re-render the Preview from current session state rather
than reusing a cached rendering, so an interruption can never smuggle
stale content past a human who resumes expecting to see what they last
reviewed (143G §9.1).

### 10.6 Cancellation Availability

Cancellation SHALL remain available up to the instant Confirmation
completes; no point in the flow is "too late to cancel" until Confirmation
itself has occurred (143G §9.1).

### 10.7 Confirmation Completeness

Confirmation SHALL require: (a) that the human authority has reviewed the
exact Preview content; (b) an explicit acknowledgement of that content,
distinct from having merely viewed it; and (c) a deliberate,
non-defaultable confirming action (CHGR-REQ-059–062). Confirmation SHALL
NOT be satisfied by a session timeout, by inactivity, by pressing Enter on
a default value, by any implicit-acceptance mechanism, or by any
command-line flag that skips displaying the exact Preview content before
confirming (CHGR-REQ-063–066).

## 11. State Contract

### 11.1 Five Distinct State Classes

This contract freezes five state classes as permanently distinct, none
substituting for another:

| State class | Owned by | Never substitutes for |
|---|---|---|
| Session state (§4.4) | This contract | CHGR record lifecycle state |
| Confirmation state (Preview-Digest-bound evidence, §10) | This contract | Publication — Confirmation evidence is an input to Publication, never Publication itself |
| CHGR lifecycle state | CHGR-001 §13.1 (already frozen) | Session state, PCAE phase/task lifecycle |
| Runtime state | `pcae runtime inspect` (existing, unrelated machinery) | Any of the above |
| Project/phase lifecycle | `PROJECT_STATUS.md`, `.pcae/phase-completion-*`, `pcae phase complete` (existing, unrelated machinery) | Any of the above |

(143G §20.)

### 11.2 Session-Confirmed vs. Record-Confirmed

A session reaching `Confirmed` (§4.4) is not the same fact as a future
`HumanGovernanceRecord`'s own `lifecycle_state` field reaching
`confirmed`. The two are related one-to-one for a successful session, but
they are not the same field, the same timestamp, or the same artifact.
Session-Confirmed evidence becomes the record's `confirmation_evidence_ref`
payload only once the Publication Handoff (§2, §11.4) runs; it does not
retroactively become the record's own state before that (143G §18,
restating CHGR-001 §13.2's Confirmation/Publication distinctness one layer
earlier).

### 11.3 Decision Exists vs. Session Exists vs. CHGR Exists

| Concept | Exists when | Distinct from |
|---|---|---|
| Session exists | From `Created` | Never itself a CHGR |
| Decision exists | From `DecisionSelected` — captured, not yet confirmed | A decision without Confirmation carries no evidentiary weight beyond "a human, at this point, had selected this"; it can be changed or abandoned freely |
| Confirmation exists | At session `Confirmed` | Session-Confirmed is the input to record-Confirmation, not the record's own confirmed state (§11.2 above) |
| CHGR exists | Only after a future Publication implementation runs | Every earlier row |

(143G §18.)

### 11.4 The Publication Handoff Boundary

A future implementation that builds Publication takes, as its sole input,
a session in state `Confirmed`: its bound template reference, its captured
decision content, its exact Preview and Preview Digest, and its
Confirmation evidence. Publication then performs exactly what CHGR-001 §8
already requires — atomically, immediately, with no discretionary step —
and the session's own lifecycle ends at `Confirmed`; it has no further
responsibility once handoff occurs (143G §18.2). This contract does not
build the handoff mechanism, only names its exact boundary, mirroring
143G's identical stance.

### 11.5 Lifecycle Independence

No Decision Session state SHALL be read, written, or inferred as if it
were PCAE phase or task lifecycle state, and no PCAE phase or task
lifecycle state SHALL be read, written, or inferred as if it were Decision
Session state. This is the same discipline CHGR-001 §15 already enforces
between phase reports and CHGR records, generalized here to session state
and Confirmation state as two additional state classes (143G §20).

## 12. Failure Contract

| Scenario | Required handling |
|---|---|
| Interruption (process crash, connection loss) | Session state persisted after every stage transition; resuming re-enters the exact last-persisted state, never a reconstructed guess |
| Timeout | Governed by `Expired` (§4.4, §4.7); no silent extension, no auto-confirmation on timeout |
| Cancellation | Terminal, per §4.8; produces no CHGR |
| Abandonment | Reachable from any non-terminal state via inactivity past the abandonment threshold (§4.4); produces no CHGR |
| Validation failure | A required-field or closed-set violation blocks advancement past `AwaitingDecision`/`DecisionSelected`; surfaced to the human, never silently defaulted or auto-corrected |
| Stale evidence | Detected at Preview-(re)generation time (§10.2); triggers a fresh evidence re-assembly (§8.4) and a fresh Preview, never a silent reuse of outdated evidence |
| Stale template | If the bound template version is amended after session creation, the session's own bound version remains authoritative for that session; the session surfaces "a newer template version now exists" as an informational note, never auto-migrates mid-session content |
| Replay attempts | Rejected per §10.2/§10.4's digest-binding requirement |
| Partial progress | Preserved verbatim across a resume (§4.5); nothing already reviewed is silently re-presented as still-current without the staleness checks above |

(143G §11.)

No failure scenario listed above, and no failure scenario this contract
does not anticipate, SHALL, through any recovery, retry, or fallback
mechanism, accidentally create a governance decision. Recovery SHALL
preserve determinism throughout: given the same persisted session state
and the same current evidence/template state, resuming twice SHALL
produce the same next-presented content both times (143G §11, extending
CHGR-REQ-023's determinism principle to session-level recovery).

## 13. Audit Contract

### 13.1 Seven Auditable Boundaries

A future verifier or auditor SHALL be able to distinguish, from a
session's own retained Session Audit Evidence alone:

| Boundary | What it contains |
|---|---|
| AI conversation | Free-form exchange during clarification; logged verbatim, never summarized |
| Clarification | A subset of AI conversation, structurally tagged distinct from evidence presentation |
| Proposal | The template-rendered scaffolding and option set as presented — an AI/system artifact, never itself evidence of a decision |
| Evidence | The assembled context, separately logged from the conversation that discusses it |
| Preview | The exact confirmable content — a distinct, digest-bound artifact |
| Confirmation | The distinct act and its evidence, tagged separately from Decision Capture even though they occur in sequence |
| Resulting CHGR | Produced by Publication, outside this contract's scope; the audit trail up to `Confirmed` is handed to Publication as an input, never merged into it silently |

(143G §13.1.)

### 13.2 Canonical Artifact Designation

Only the resulting, published CHGR — once a future implementation builds
Publication — becomes canonical, per CHGR-001's own discipline. Every
artifact in §13.1's list up through `Confirmed` is Session Audit Evidence:
retained per §14 below, citable by a future verifier reconstructing "what
led to this decision," but never itself a CHGR, never itself published,
and never itself carrying independent authority (143G §13.2, mirroring
CHGR-REQ-004's proposal/record separation across the entire pre-publication
trail).

## 14. Privacy Contract

| State class | Nature | Retention posture |
|---|---|---|
| Temporary interaction state (in-progress session fields, not yet Confirmed) | Ephemeral, mutable | Retained only for the session's own resumability window (§4.5, §12); a future implementation SHOULD define a bounded retention period for `Cancelled`/`Expired`/`Abandoned` sessions rather than retaining them indefinitely by default |
| Canonical governance state | The eventual published CHGR (future Publication) | Governed entirely by CHGR-001's own immutability/retention discipline — outside this contract's scope to alter |
| Transient AI conversation (clarification exchanges) | Logged for audit (§13.1) | Retained alongside the session's audit trail, not indefinitely by default; a future implementation determines a concrete retention window as an implementation decision |
| Retained audit evidence (post-Confirmation trail handed to Publication) | Becomes part of the CHGR's own provenance per CHGR-001 §10/§12.1 | Governed by CHGR-001's provenance retention discipline once Publication exists |

(143G §14.)

Temporary interaction state SHALL NEVER become canonical governance state
automatically; only the explicit Publication Handoff (§2, §11.4)
transfers Session Audit Evidence into a future CHGR's provenance. This
contract does not require retaining full conversational transcripts beyond
what CHGR-001 §10's provenance requirements already demand (options
presented, exact Preview content, Confirmation evidence); a future
implementation MAY retain more for audit richness, but any additional
retention is itself a privacy decision a future implementation phase must
make explicitly, never one this contract mandates.

## 15. Security Contract

This contract freezes protections, drawn from Phase 143G §12's security
architecture, against the following threats. For every scenario below,
the default response to any detected ambiguity or verification gap is to
refuse advancement, fail-closed — never a best-effort or
benefit-of-the-doubt default.

| Threat | Frozen mitigation |
|---|---|
| Replay (reusing an old confirmation against new content) | §10.2/§10.4 digest binding |
| Prompt injection (evidence or subject content attempting to instruct the AI to auto-select or auto-confirm) | §5.2's absolute prohibitions are structural, not instruction-following; no evidence content, however phrased, can cause the AI to perform an act the contract assigns exclusively to the human; all assembled evidence and clarification input SHALL be treated as untrusted data, never as executable instruction |
| Hidden defaults | §5, §6: no field has a default-value path; Confirmation Readiness (§2) is computed strictly from presence, never from a fallback value |
| Accidental confirmation | §10.7's distinct, deliberate, non-defaultable act requirement; no "Enter accepts" path exists anywhere in the state model |
| Stale previews | §10.2 |
| Altered evidence (tampered with between assembly and confirmation) | §8.4/§10.2's re-validation-at-confirmation-time requirement |
| Altered templates (mid-session tampering) | §4.3's version-binding; a session's bound template version is immutable for that session's life |
| Interface ambiguity (a transport rendering the Preview in a way that could mislead) | §16's transport-independence requirement: interaction semantics are transport-independent and testable independent of any specific UI |
| Session hijacking (a different actor resuming someone else's session) | §4.2's ownership-binding requirement: resumption is permitted only to the identity bound at creation |
| Forged confirmation | §10.3's digest-and-identity binding: a confirming action SHALL carry both the correct Preview Digest and evidence of the bound identity, never accepted from identity evidence alone or digest evidence alone |

(143G §12.)

## 16. Transport Independence Contract

Every requirement in §1–§15 above is specified in terms of stages, states,
and required acts, never in terms of keystrokes, screens, HTTP verbs, or
widget types. A CLI prompt sequence, a TUI form, a web wizard, an IDE
panel, a REST API exchange, and a mobile flow are all equally valid
transports for the same Decision Session architecture, provided each:

- presents the Decision Subject before any option (§4.4 `Created` →
  `EvidenceReady`);
- presents the full, un-editorialized option set with no visual emphasis
  implying a preferred choice (§5.2, §6);
- requires the same distinct, non-defaultable Confirmation act bound to
  the same exact-Preview-Digest discipline (§10);
- exposes cancellation at every non-terminal stage (§4.8);
- cannot silently skip Disclosure Acknowledgement (§8.5) or clarification
  logging (§13.1) merely because a given transport makes it easy to omit.

(143G §15.1.) User experience MAY differ across transports; governance
semantics SHALL NOT. Concrete flag syntax, screen layouts, HTTP routes,
and API payload shapes are implementation concerns for the phase(s) that
eventually build a specific transport, not this contract's concern (143G
§15.2).

## 17. Extensibility Contract

This contract freezes the following as additive extension points, none of
which SHALL require altering the state model (§4.4), the Confirmation
binding (§10), or the human/AI responsibility boundary (§5–§6):

| Future capability | Attachment point | Constraint |
|---|---|---|
| Signatures | An additional confirmation-evidence class at §10, extending CHGR-001 §12's L0–L5 assurance model | §10.3's digest-binding is signature-algorithm-agnostic |
| Enterprise identity | An additional identity-evidence source at §4.2's ownership-binding | Within the existing L0–L5 extension point |
| Delegated authority | An extension of §10's identity-binding to a delegation record | A candidate future CHGR type, not invented by this contract |
| Quorum approval | The L5 "multi-party confirmation" assurance level CHGR-001 §12 already reserves | This contract's single-participant session model is the case quorum would extend, not replace |
| Committee workflows | A quorum-bound multi-session aggregation, chained via CHGR-001 §13's existing supersession/predecessor-successor mechanics | No new state-model concept required, only a linking convention |
| Policy engines | An additional gate before `AwaitingConfirmation`, evaluating template eligibility or evidence sufficiency | Cannot drive decision selection or Confirmation without becoming a prohibited AI-selection or AI-confirmation path |
| External governance systems | An additional evidence (§8) or identity-assertion (§4.2, an L4 assurance level already reserved) source | Cannot supply a selection or Confirmation without violating §5.2/§10 regardless of claimed authority |

(143G §16, §17.) Multi-participant capability (multiple reviewers,
sequential approvals, quorum, committee decisions) is explicitly deferred:
none of it is required to satisfy CHGR-001's frozen text for a
single-authority decision, the only kind any existing Decision Template
currently anticipates, and building it now would be architecture
speculatively extending beyond what any frozen contract requires (143G
§16.2). This contract names the attachment points precisely so a future,
separately scoped and separately authorized phase can add them without
disturbing §1–§16's single-participant design.

## 18. Governance Responsibility Contract

This contract introduces **no new role, responsibility, or authority**
beyond GPC6-REQ-040's existing table and CHGR-001 §20's existing
responsibility mapping, following the same "one owner per responsibility"
discipline. Responsibility mapping, restated for the Interactive Decision
Session layer specifically:

| Responsibility | Owner | Basis |
|---|---|---|
| Decision Session presentation, evidence assembly, Preview rendering | PCAE tooling, strictly bounded per §5 above | §5, §8, §10 above |
| Decision selection, rationale, condition authorship | The eligible Human Authority the bound Decision Template names — the same "Human Authority" concept CHGR-001 §20 already assigns, never a new role | §6 above |
| Confirmation | The same Human Authority, via the distinct act of §10 | §10 above |
| Session persistence/custody | Repository or operational-storage custody; no new custodial role | §4.10 above |
| Verification | Independent Contract Verifier or Independent Implementation Verifier (existing roles), depending on what is being verified | §9.2, §21 below |
| Publication Handoff execution | **Not yet assigned — an explicitly open question, per §18.4 below**, mirroring CHGR-001 §20.5's identical deferral | §11.4 above |

### 18.4 Judgment call: Publication Handoff ownership left open

CHGR-001 §20.5 explicitly declined to assign runtime-consumption
ownership to any existing role, naming it "an open question for a future,
separately governed contract revision." This contract preserves an
analogous gap deliberately: the Publication Handoff (§2, §11.4) is
described but not implemented by Phase 143G's architecture or by this
contract, and assigning ownership of a capability this contract does not
implement, describe operationally, or authorize would itself be an
instance of inventing authority this contract has no basis to invent —
GPC6-REQ-040's existing table names no role positioned to own a handoff
mechanism that does not yet architecturally exist. Any apparent gap here
is evidence of a defect requiring a future, separately governed contract
revision once the Publication Handoff is itself separately architected and
authorized, not license to informally assign the responsibility now
(mirrors CHGR-001 §20.5's and GPC6R-REQ-020's identical no-informal-
assignment rule).

## 19. Compatibility Contract

This contract SHALL remain compatible with, and SHALL NOT redefine,
narrow, or supersede:

- **CHGR-001** — this contract adds no new obligation to the Canonical
  Human Governance Record artifact class itself; it constrains only the
  pre-publication layer that produces Publication's input. Every
  CHGR-001 requirement this contract restates (CHGR-REQ-019–023,
  CHGR-REQ-030, CHGR-REQ-032–048, CHGR-REQ-057, CHGR-REQ-059–066,
  CHGR-REQ-085, CHGR-REQ-090–097, CHGR-REQ-142) is restated without
  narrowing, one layer earlier.
- **The Typed Authority Model (TAMC-001, TAMPC-001)** — independently
  re-confirmed below (§19.1).
- **Advisory Governance contracts (AGOC-001)** — this contract introduces
  no new advisory artifact class beyond what CHGR-001 §16 already
  anticipates ("AI proposal" = the Decision Session's own proposal stage,
  §13.1 above).
- **Canonical artifact architecture (Phase 114A `ArtifactState`, Phase
  134E.1 `CanonicalEngineeringEvidence`)** — consulted as non-binding
  precedent only, exactly as 143A/143G already treat them; this contract
  composes with neither.
- **Lifecycle architecture (`src/pcae/lifecycle.py`, Phase 80A)** —
  unrelated domain (backend-output-adoption lifecycle); §11.5 above
  explicitly separates session state from this and from PCAE phase/task
  lifecycle.
- **Runtime architecture** — §19.1 below restates CHGR-001 §17's frozen
  future boundary without extension.

### 19.1 Typed Authority Model and Runtime — Independent Re-confirmation

This contract independently re-confirms, from direct re-reading of
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` (TAMC-001)
and `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(TAMPC-001), CHGR-001 §19.1's conclusion that the Stage 3 Typed Authority
Model family SHALL remain a wholly separate artifact family from CHGR —
and, by direct extension, from the Decision Session layer this contract
governs. TAMC-REQ-005's sixteen frozen record families (including
`human_authorization`) and TAMC-REQ-036's rule that record
existence/validity SHALL NEVER imply authorization, completion, approval,
certification, publication, execution, or runtime permission apply with
equal force to a Decision Session: a session's own `CDS-<uuid4>` identity
(§4.1) is not a `record_type` in either the CHGR-001 schema family or the
Typed Authority Model's sixteen families, and is not eligible for either
family's identity namespace, manifest, or any future runtime-consumption
check (143G's Architecture Validation table). No runtime code path reads
Decision Session state today, and this contract creates none: `pcae
runtime inspect` before and after this contract's own freeze shows Runtime
state Observed, execution capability unavailable, maximum plugin
capability observe — unchanged (§3 invariant 12; CHGR-REQ-029,
CHGR-REQ-142–146 restated one layer earlier for session state
specifically).

## 20. Amendment Contract

IWC-001 MAY evolve only through governed superseding contracts, each
identifying its predecessor, version, changed requirements, migration
effect, and backward-compatibility impact, mirroring CHGR-001 §22's
identical extensibility discipline (itself mirroring GLP-001 §13,
GAC-001 §18, and TAMC-001 §15). A Decision Session's own recorded
Session Audit Evidence, once a session reaches a terminal state, SHALL
NEVER change meaning through an amendment to this contract — IWC-001's
own evolution governs future session behavior only, never the
retroactive reinterpretation of an already-terminal session's retained
evidence (mirrors CHGR-REQ-191's non-retrospective-invalidation guarantee,
restated here for the session layer).

---

## 21. Requirement Set

Every substantive `SHALL`/`SHALL NOT`/`MUST` statement in §1–§20 above
corresponds to at least one requirement below. Requirement identifiers
are sequential, stable, non-reused, and independently traceable to the
section they freeze.

### 21.1 Purpose Requirements

**IWC-REQ-001.** A Decision Session SHALL exist solely to enable a human
authority to make a governed decision that may later become a CHGR.

**IWC-REQ-002.** A Decision Session SHALL NEVER, by existing or by
reaching any defined state, itself create authority.

**IWC-REQ-003.** A Decision Session SHALL NEVER be treated as,
substituted for, or conflated with a CHGR.

**IWC-REQ-004.** A Decision Session SHALL NEVER, by reaching any defined
state, itself convey authority.

**IWC-REQ-005.** A Decision Session SHALL NEVER, by reaching any defined
state, itself constitute Publication.

### 21.2 Definitions Requirements

**IWC-REQ-006.** The term "Decision Session" SHALL be used only with the
meaning §2 defines.

**IWC-REQ-007.** The term "Session State" SHALL be used only with the
meaning §2 and §4.4 define.

**IWC-REQ-008.** The term "Decision Capture" SHALL be used only with the
meaning §2 defines.

**IWC-REQ-009.** The term "Confirmation Readiness" SHALL be used only with
the meaning §2 defines: a computed boolean, never manually overridden.

**IWC-REQ-010.** The term "Preview" SHALL be used only with the meaning §2
and §10.1 define.

**IWC-REQ-011.** The term "Preview Digest" SHALL be used only with the
meaning §2 and §10.2 define.

**IWC-REQ-012.** The terms "Explanation," "Clarification," "Recommendation,"
and "Persuasion" SHALL be used only with the meanings §2 and §9.1 define.

**IWC-REQ-013.** The term "Disclosure Acknowledgement" SHALL be used only
with the meaning §2 and §8.5 define.

**IWC-REQ-014.** The term "Session Audit Evidence" SHALL be used only with
the meaning §2 and §13 define.

**IWC-REQ-015.** The term "Publication Handoff" SHALL be used only with the
meaning §2 and §11.4 define.

**IWC-REQ-016.** No term this contract defines SHALL redefine, narrow, or
conflict with any term CHGR-001 §2 already defines.

### 21.3 Core Invariants Requirements

**IWC-REQ-017.** PCAE tooling SHALL assist a Decision Session only through
the operations §5.1 enumerates.

**IWC-REQ-018.** Selecting a decision from a Decision Template's closed
option set SHALL be exclusively a human act.

**IWC-REQ-019.** No Decision Session SHALL reach `Confirmed` through any
mechanism other than the distinct Confirmation act of §10.

**IWC-REQ-020.** Two independent sessions against identical inputs SHALL
assemble identical evidence and render identical Previews.

**IWC-REQ-021.** A Decision Session interrupted at any non-terminal state
SHALL be recoverable from its last-persisted state without loss,
corruption, or silent advancement.

**IWC-REQ-022.** A Decision Session in `Created` through
`AwaitingConfirmation` MAY be resumed only by the identity bound at
creation.

**IWC-REQ-023.** A Confirmation act SHALL be rejected unless it carries
evidence tied to the specific, currently-valid Preview Digest.

**IWC-REQ-024.** A Decision Session identifier, once terminal, SHALL
NEVER be reused for a new interaction.

**IWC-REQ-025.** Every artifact a Decision Session produces up to
`Confirmed` SHALL be retained as Session Audit Evidence.

**IWC-REQ-026.** Reaching `Confirmed` SHALL NEVER, by itself, prove the
human held eligible authority under the bound template.

**IWC-REQ-027.** Every requirement in this contract SHALL be satisfiable
by a CLI, TUI, web, IDE, API, or mobile transport.

**IWC-REQ-028.** A Decision Session's state SHALL NEVER substitute for, or
be substituted by, PCAE phase or task lifecycle state.

**IWC-REQ-029.** No Decision Session state, before or after `Confirmed`,
SHALL be visible to, consumable by, or capable of triggering any runtime
capability change.

**IWC-REQ-030.** A future verifier SHALL be able to distinguish, from a
session's own retained state alone, all seven boundaries §13.1 lists.

**IWC-REQ-031.** Temporary interaction state SHALL NEVER become canonical
governance state automatically.

**IWC-REQ-032.** Any ambiguity in a Decision Session's subject, authority,
scope, or state SHALL resolve to "not authoritative here" / "not
applicable," never to an assumed favorable reading.

### 21.4 Session Requirements

**IWC-REQ-033.** Every Decision Session SHALL carry exactly one canonical
session identifier of the form `CDS-<uuid4>`.

**IWC-REQ-034.** A session identifier SHALL be structurally distinct in
prefix and allocation timing from a CHGR's `chgr-<uuid4>` identifier and
from any Typed Authority Model identifier.

**IWC-REQ-035.** A session identifier SHALL NEVER be pre-minted as, reused
as, or substituted for a future CHGR's own canonical identifier.

**IWC-REQ-036.** A Decision Session SHALL be bound at creation to the
identity of the human who created it.

**IWC-REQ-037.** A resumption request from an identity other than the one
bound at creation SHALL be rejected, fail closed.

**IWC-REQ-038.** A Decision Session SHALL be bound at creation to exactly
one Decision Template, inclusive of version, and exactly one Decision
Subject, for its entire lifetime.

**IWC-REQ-039.** Neither the template nor the subject binding SHALL be
silently swapped mid-session.

**IWC-REQ-040.** The Decision Session state model SHALL consist of exactly
the ten states §4.4 lists: `Created`, `EvidenceReady`, `AwaitingDecision`,
`AwaitingClarification`, `DecisionSelected`, `AwaitingConfirmation`,
`Confirmed`, `Cancelled`, `Expired`, `Abandoned`.

**IWC-REQ-041.** Each state's entry conditions and permitted exits SHALL
be as §4.4's table specifies, unmodified.

**IWC-REQ-042.** No implementation SHALL add, remove, merge, or rename a
state in §4.4's table without a governed amendment to this contract.

**IWC-REQ-043.** Resumption SHALL always re-enter exactly the stage left.

**IWC-REQ-044.** Resumption SHALL NEVER fast-forward past Confirmation or
resume directly into `Confirmed`.

**IWC-REQ-045.** Every Decision Session SHALL carry a template-defined or
system-default maximum lifetime.

**IWC-REQ-046.** An expired session SHALL transition to `Expired`, never
silently extend.

**IWC-REQ-047.** A human MAY cancel a Decision Session at any point before
`Confirmed`.

**IWC-REQ-048.** Cancellation SHALL be terminal and SHALL produce no CHGR,
no partial record, and no residual claim on the session's binding.

**IWC-REQ-049.** No implementation SHALL colocate session state files
under `.pcae/governance-records/records/` or any path a manifest-driven
consumer might mistake for a frozen CHGR schema instance.

### 21.5 AI Responsibility Requirements

**IWC-REQ-050.** PCAE tooling MAY assemble evidence, present template
scaffolding, validate presence and closed-set membership, explain, answer
permitted clarification, surface conflicts/gaps, summarize consequences
verbatim, and generate a deterministic Preview.

**IWC-REQ-051.** PCAE tooling SHALL NOT select, choose, or pre-select an
option on a human's behalf.

**IWC-REQ-052.** PCAE tooling SHALL NOT infer a selection from partial
input, or optimize a selection toward any outcome.

**IWC-REQ-053.** PCAE tooling SHALL NOT fabricate, complete, reinterpret,
broaden, or narrow a human-authored rationale or condition field.

**IWC-REQ-054.** PCAE tooling SHALL NOT silently modify a human's
already-made selection.

**IWC-REQ-055.** PCAE tooling SHALL NOT infer consent from silence,
inactivity, timeout, or the mere passage of a screen.

**IWC-REQ-056.** PCAE tooling SHALL NOT fabricate a rationale or condition
the human did not author.

**IWC-REQ-057.** PCAE tooling SHALL NOT perform Confirmation on a human's
behalf under any circumstance.

**IWC-REQ-058.** PCAE tooling SHALL NOT elevate the assurance level,
authority basis, or eligibility claimed for a decision beyond what session
evidence actually supports.

**IWC-REQ-059.** PCAE tooling SHALL NOT persuade a human toward a
particular option through framing, emphasis, repetition, or selective
evidence presentation.

**IWC-REQ-060.** PCAE tooling SHALL NOT manufacture, imply, or suggest
authority the session's own evidence does not support.

**IWC-REQ-061.** A Decision Session's internal representation SHALL make
the AI-authored/human-authored boundary structurally visible through
distinct fields.

**IWC-REQ-062.** A Decision Session SHALL NOT rely on prose tone alone to
distinguish AI-authored from human-authored content.

### 21.6 Human Responsibility Requirements

**IWC-REQ-063.** Selecting a decision from the closed option set SHALL be
exclusively human, with no implicit-selection path.

**IWC-REQ-064.** Supplying rationale SHALL remain optional in every
Decision Session unless the bound template's own text mandates it.

**IWC-REQ-065.** Acknowledging every mandatory non-effect statement
attached to the in-progress selection SHALL be a distinct, explicit,
tracked human act.

**IWC-REQ-066.** Reviewing the exact Preview before Confirmation SHALL be
a distinct human act.

**IWC-REQ-067.** Performing Confirmation SHALL be a distinct, deliberate,
non-defaultable human act.

**IWC-REQ-068.** No sequence of intermediate actions short of Confirmation
SHALL constitute a decision.

**IWC-REQ-069.** No architectural element SHALL permit implicit consent at
any of the five human responsibilities §6 lists.

### 21.7 Decision Existence Requirements

**IWC-REQ-070.** A governance decision SHALL NOT be deemed to exist merely
because a Decision Session is created.

**IWC-REQ-071.** A governance decision SHALL NOT be deemed to exist merely
because evidence is assembled.

**IWC-REQ-072.** A governance decision SHALL NOT be deemed to exist merely
because clarification occurs.

**IWC-REQ-073.** A governance decision SHALL NOT be deemed to exist merely
because an option is selected.

**IWC-REQ-074.** A governance decision SHALL NOT be deemed to exist merely
because rationale is entered.

**IWC-REQ-075.** A governance decision SHALL NOT be deemed to exist merely
because a Preview is generated.

**IWC-REQ-076.** A governance decision SHALL be deemed to exist only after
the human authority performs the distinct Confirmation act over the exact,
currently-valid Preview content.

**IWC-REQ-077.** This decision-existence semantic (IWC-REQ-070 through
IWC-REQ-076) SHALL be immutable and SHALL NOT be narrowed by any future
implementation, transport, or extension.

### 21.8 Evidence Requirements

**IWC-REQ-078.** Evidence presentation SHALL be a pure function of the
Decision Subject, the bound template's evidence-class declarations, and
the state of governing artifacts at context-acquisition time.

**IWC-REQ-079.** Two independent sessions against the same template and
subject SHALL assemble identical evidence.

**IWC-REQ-080.** Governing and supporting references SHALL be cited by
path or identifier, never inlined-and-editorialized.

**IWC-REQ-081.** PCAE tooling SHALL NEVER rank or weight cited evidence.

**IWC-REQ-082.** Each cited artifact's own provenance SHALL be carried
alongside its citation.

**IWC-REQ-083.** Uncertain evidence currency SHALL be surfaced explicitly,
never presented as trustworthy by default.

**IWC-REQ-084.** An unresolvable template-declared evidence class SHALL be
presented as an explicit gap, never omitted silently.

**IWC-REQ-085.** Conflicting cited evidence SHALL be presented as a flagged
conflict, never silently resolved in favor of one item.

**IWC-REQ-086.** Derived or computed evidence SHALL be labeled as such,
distinct from verbatim-sourced evidence.

**IWC-REQ-087.** Evidence assembled for one Decision Subject SHALL NOT be
silently reused for another.

**IWC-REQ-088.** Evidence assembled at session-creation time SHALL NOT be
presented unchanged at Confirmation time if underlying artifacts changed,
without surfacing that drift.

**IWC-REQ-089.** Every mandatory non-effect statement attached to an
in-progress selection SHALL require a distinct, tracked Disclosure
Acknowledgement before Preview generation.

**IWC-REQ-090.** Disclosure Acknowledgement SHALL NEVER be inferred from a
passive signal.

### 21.9 Clarification Requirements

**IWC-REQ-091.** Explanation SHALL be permitted, bounded to the template's
own fixed meaning.

**IWC-REQ-092.** Clarification SHALL be permitted, bounded to factual
content invariant to any inferred target selection.

**IWC-REQ-093.** Recommendation SHALL be forbidden outright, performed by
no architectural element.

**IWC-REQ-094.** Persuasion SHALL be forbidden outright, performed by no
architectural element.

**IWC-REQ-095.** A Clarification answer whose content varies with an
inferred target selection SHALL be treated as Persuasion and is out of
architectural bounds.

**IWC-REQ-096.** Every clarification exchange SHALL be logged verbatim as
Session Audit Evidence.

**IWC-REQ-097.** Clarification SHALL NOT reframe an option's consequence
or non-effect text with substitute wording, even wording judged clearer.

### 21.10 Confirmation Requirements

**IWC-REQ-098.** Once Decision Capture reaches Confirmation Readiness, the
session SHALL compute a Preview that is a pure function of captured
content, fixed the instant Confirmation begins.

**IWC-REQ-099.** The human SHALL be shown the literal content that will
become the CHGR's provenance-recorded preview, with no paraphrase or
summary view.

**IWC-REQ-100.** The session SHALL recompute the Preview Digest against
current session content immediately before accepting a confirming action.

**IWC-REQ-101.** A Preview Digest mismatch SHALL fail closed: Confirmation
SHALL be refused and a freshly regenerated Preview SHALL be shown.

**IWC-REQ-102.** Confirmation SHALL bind to the exact digest of what was
shown, never to the abstract current state of the session.

**IWC-REQ-103.** A confirming action SHALL carry evidence tied to the
specific, currently-valid Preview Digest, not merely evidence that a
confirming click occurred at some point.

**IWC-REQ-104.** A Confirmation act SHALL be bound to a specific
Preview-content digest; the same confirmation evidence against different
content SHALL be rejected.

**IWC-REQ-105.** A session interrupted between Preview generation and
Confirmation SHALL, on resume, re-render the Preview from current session
state rather than reuse a cached rendering.

**IWC-REQ-106.** Cancellation SHALL remain available up to the instant
Confirmation completes.

**IWC-REQ-107.** Confirmation SHALL require the human to have reviewed the
exact Preview content.

**IWC-REQ-108.** Confirmation SHALL require an explicit acknowledgement of
the reviewed content, distinct from having merely viewed it.

**IWC-REQ-109.** Confirmation SHALL require a deliberate, non-defaultable
confirming action.

**IWC-REQ-110.** Confirmation SHALL NOT be satisfied by a session timeout
or by inactivity.

**IWC-REQ-111.** Confirmation SHALL NOT be satisfied by pressing Enter on
a default value or by any implicit-acceptance mechanism.

**IWC-REQ-112.** No command interface SHALL provide a flag or mode that
skips displaying the exact Preview content before Confirmation.

### 21.11 State Requirements

**IWC-REQ-113.** Session state, Confirmation state, CHGR lifecycle state,
runtime state, and project/phase lifecycle state SHALL remain five
permanently distinct state classes.

**IWC-REQ-114.** No state class SHALL be read, written, or inferred as if
it were another.

**IWC-REQ-115.** A session reaching `Confirmed` SHALL NOT be treated as
identical to a future CHGR's `lifecycle_state` reaching `confirmed`.

**IWC-REQ-116.** Session-Confirmed evidence SHALL become a record's
`confirmation_evidence_ref` payload only once the Publication Handoff
runs, never retroactively before that.

**IWC-REQ-117.** A decision captured but not yet confirmed SHALL carry no
evidentiary weight beyond "a human, at this point, had selected this."

**IWC-REQ-118.** A CHGR SHALL be deemed to exist only after a future
Publication implementation runs; no earlier session state SHALL be
treated as if a CHGR already existed.

**IWC-REQ-119.** A future Publication implementation SHALL take as its
sole input a session in state `Confirmed`, together with its bound
template reference, captured decision content, exact Preview and Preview
Digest, and Confirmation evidence.

**IWC-REQ-120.** A Decision Session's own lifecycle SHALL end at
`Confirmed`; it SHALL have no further responsibility once Publication
Handoff occurs.

### 21.12 Failure Requirements

**IWC-REQ-121.** Session state SHALL be persisted after every stage
transition; resuming SHALL re-enter the exact last-persisted state, never
a reconstructed guess.

**IWC-REQ-122.** A timeout SHALL be governed by `Expired` with no silent
extension and no auto-confirmation on timeout.

**IWC-REQ-123.** A required-field or closed-set validation failure SHALL
block advancement past `AwaitingDecision`/`DecisionSelected`, surfaced to
the human, never silently defaulted or auto-corrected.

**IWC-REQ-124.** Stale evidence detected at Preview-(re)generation time
SHALL trigger a fresh evidence re-assembly and a fresh Preview, never a
silent reuse of outdated evidence.

**IWC-REQ-125.** If a bound template version is amended after session
creation, the session's own bound version SHALL remain authoritative for
that session; the session SHALL surface the existence of a newer version
as an informational note, never auto-migrate.

**IWC-REQ-126.** A replay attempt SHALL be rejected per the digest-binding
requirements of §10.

**IWC-REQ-127.** Partial progress SHALL be preserved verbatim across a
resume.

**IWC-REQ-128.** No failure, recovery, retry, or fallback mechanism SHALL
accidentally create a governance decision.

**IWC-REQ-129.** Recovery SHALL preserve determinism: given the same
persisted session state and current evidence/template state, resuming
twice SHALL produce the same next-presented content both times.

### 21.13 Audit Requirements

**IWC-REQ-130.** A future verifier SHALL be able to distinguish AI
conversation from clarification from a session's own retained state.

**IWC-REQ-131.** A future verifier SHALL be able to distinguish proposal
content from evidence content from a session's own retained state.

**IWC-REQ-132.** A future verifier SHALL be able to distinguish Preview
content from Confirmation evidence from a session's own retained state.

**IWC-REQ-133.** A future verifier SHALL be able to distinguish the
resulting CHGR (once published) from the session's own pre-Confirmation
audit trail.

**IWC-REQ-134.** AI conversation SHALL be logged verbatim, never
summarized.

**IWC-REQ-135.** Only a published CHGR SHALL be canonical; every earlier
artifact through `Confirmed` SHALL be Session Audit Evidence, never
itself carrying independent authority.

**IWC-REQ-136.** The audit trail up to `Confirmed` SHALL be handed to
Publication as an input, never merged into it silently.

### 21.14 Privacy Requirements

**IWC-REQ-137.** Temporary interaction state SHALL be retained only for
the session's own resumability window.

**IWC-REQ-138.** A future implementation SHOULD define a bounded retention
period for `Cancelled`/`Expired`/`Abandoned` sessions rather than
retaining them indefinitely by default.

**IWC-REQ-139.** Transient AI conversation logged for audit SHALL NOT be
retained indefinitely by default.

**IWC-REQ-140.** Temporary interaction state SHALL NEVER become canonical
governance state automatically; only the Publication Handoff transfers
Session Audit Evidence into CHGR provenance.

**IWC-REQ-141.** This contract SHALL NOT require retaining full
conversational transcripts beyond what CHGR-001 §10's provenance
requirements demand.

**IWC-REQ-142.** Any retention beyond CHGR-001 §10's minimum SHALL be an
explicit implementation decision, never mandated by this contract.

### 21.15 Security Requirements

**IWC-REQ-143.** A Decision Session implementation SHALL prevent a
replayed confirmation from being accepted against different content.

**IWC-REQ-144.** A Decision Session implementation SHALL treat all
assembled evidence and clarification input as untrusted data, never as
executable instruction.

**IWC-REQ-145.** A Decision Session implementation SHALL prevent any field
from carrying a default-value path that could satisfy Confirmation
Readiness without explicit human input.

**IWC-REQ-146.** A Decision Session implementation SHALL prevent
accidental confirmation through any "Enter accepts" or equivalent path.

**IWC-REQ-147.** A Decision Session implementation SHALL prevent a stale
Preview from being confirmed without a digest re-check.

**IWC-REQ-148.** A Decision Session implementation SHALL prevent evidence
tampered with between assembly and Confirmation from being confirmed
without detection.

**IWC-REQ-149.** A Decision Session implementation SHALL prevent a bound
template version from being altered mid-session.

**IWC-REQ-150.** A Decision Session implementation SHALL prevent a
transport from rendering the Preview in a way that could mislead the
human about its exact content.

**IWC-REQ-151.** A Decision Session implementation SHALL prevent resumption
by an identity other than the one bound at creation.

**IWC-REQ-152.** A Decision Session implementation SHALL prevent a
confirming action from being accepted on identity evidence alone or
digest evidence alone, without both.

**IWC-REQ-153.** For every security scenario in §15, the default response
to a detected ambiguity or verification gap SHALL be to refuse
advancement, fail-closed.

**IWC-REQ-154.** No prompt-injection vector originating from assembled
evidence or clarification content SHALL be capable of causing an AI system
to select, infer, or confirm a decision.

### 21.16 Transport Independence Requirements

**IWC-REQ-155.** Every requirement in §1–§15 SHALL be satisfiable by a
CLI, TUI, web, IDE, API, or mobile transport.

**IWC-REQ-156.** No requirement in §1–§15 SHALL depend on any
transport-specific mechanism.

**IWC-REQ-157.** Every transport SHALL present the Decision Subject before
any option.

**IWC-REQ-158.** Every transport SHALL present the full, un-editorialized
option set with no visual emphasis implying a preferred choice.

**IWC-REQ-159.** Every transport SHALL require the same distinct,
non-defaultable Confirmation act bound to the same exact-Preview-Digest
discipline.

**IWC-REQ-160.** Every transport SHALL expose cancellation at every
non-terminal stage.

**IWC-REQ-161.** No transport SHALL silently skip Disclosure
Acknowledgement or clarification logging merely because the transport
makes it easy to omit.

### 21.17 Extensibility Requirements

**IWC-REQ-162.** No extension listed in §17 SHALL require altering the
state model of §4.4.

**IWC-REQ-163.** No extension listed in §17 SHALL require altering the
Confirmation binding of §10.

**IWC-REQ-164.** No extension listed in §17 SHALL require altering the
human/AI responsibility boundary of §5–§6.

**IWC-REQ-165.** A future policy-engine extension SHALL NOT drive decision
selection or Confirmation.

**IWC-REQ-166.** A future external-governance-system extension SHALL NOT
supply a selection or Confirmation regardless of its claimed authority.

**IWC-REQ-167.** Multi-participant capability (multiple reviewers,
sequential approvals, quorum, committee decisions) SHALL remain
unimplemented until separately scoped and separately authorized.

### 21.18 Governance Responsibility Requirements

**IWC-REQ-168.** This contract SHALL introduce no new role, responsibility,
or authority beyond GPC6-REQ-040's existing table and CHGR-001 §20's
existing mapping.

**IWC-REQ-169.** Decision selection, rationale, and condition authorship
responsibility SHALL belong exclusively to the eligible Human Authority
the bound Decision Template names.

**IWC-REQ-170.** Confirmation responsibility SHALL belong to the same
Human Authority who performed selection.

**IWC-REQ-171.** Publication Handoff execution ownership SHALL remain
unassigned by this contract, named explicitly as an open question for a
future, separately governed phase.

### 21.19 Compatibility Requirements

**IWC-REQ-172.** This contract SHALL NOT redefine, narrow, or supersede
any requirement of CHGR-001.

**IWC-REQ-173.** This contract SHALL NOT redefine, narrow, or supersede
any requirement of GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001.

**IWC-REQ-174.** This contract SHALL NOT redefine, narrow, or supersede
any requirement of TAMC-001 or TAMPC-001.

**IWC-REQ-175.** The Typed Authority Model family and the Decision Session
layer SHALL remain wholly separate, never composed, subclassed, or
wrapped one within the other.

**IWC-REQ-176.** A Decision Session's `CDS-<uuid4>` identity SHALL NOT be a
`record_type` in either the CHGR-001 schema family or the Typed Authority
Model's record families.

**IWC-REQ-177.** No `docs/contracts/**` file other than this contract's
own new document SHALL be modified by the phase that freezes this
contract.

**IWC-REQ-178.** This contract's compatibility conclusions SHALL be
independently re-derivable from TAMC-001's and TAMPC-001's own frozen
text, not merely assumed from Phase 143G's architectural summary.

**IWC-REQ-179.** `pcae runtime inspect` SHALL show Runtime state Observed,
execution capability unavailable, and maximum plugin capability observe,
unchanged before and after this contract's freeze.

### 21.20 Amendment Requirements

**IWC-REQ-180.** IWC-001 MAY evolve only through governed superseding
contracts.

**IWC-REQ-181.** A superseding contract SHALL identify its predecessor,
version, changed requirements, migration effect, and backward-compatibility
impact.

**IWC-REQ-182.** A terminal Decision Session's own retained Session Audit
Evidence SHALL NEVER change meaning through an amendment to this contract.

**IWC-REQ-183.** No governed superseding contract SHALL retroactively
reinterpret an already-terminal session's retained evidence.

**IWC-REQ-184.** Backward compatibility with IWC-001 v1.0 SHALL be
mandatory for any future revision unless that revision explicitly states
its compatibility impact and supersedes a named requirement.

---

## 22. Adversarial Validation

Each scenario below attempts to invalidate this contract. Every scenario
is mitigated by at least one existing `IWC-REQ-###`; none required a gap
to be left open in the final text, because each gap discovered during
this pass was closed by adding the corresponding requirement to §21
before this document was finalized.

| # | Scenario | Mitigating requirement(s) |
|---|---|---|
| W1 | An AI selects an option on the human's behalf mid-session | IWC-REQ-018, 051, 052, 063 |
| W2 | A session silently treats inactivity or a timeout as acceptance | IWC-REQ-055, 070–076, 110, 122 |
| W3 | A confirming click is accepted without checking it matches the currently-valid Preview | IWC-REQ-023, 100–104 |
| W4 | A session resumes directly into `Confirmed`, skipping a fresh Preview review | IWC-REQ-044, 105 |
| W5 | A different identity resumes someone else's in-progress session | IWC-REQ-022, 037, 151 |
| W6 | Evidence assembled for one subject is silently reused for another | IWC-REQ-087 |
| W7 | Stale evidence or a stale bound template is presented as current at Confirmation time | IWC-REQ-088, 124, 125, 147, 148, 149 |
| W8 | A clarification answer subtly steers the human toward an option | IWC-REQ-092–095, 097 |
| W9 | An AI-authored rationale is fabricated or silently edited | IWC-REQ-053, 056 |
| W10 | A captured-but-unconfirmed selection is stored or referenced as if it were a CHGR | IWC-REQ-003, 070–077, 117, 118 |
| W11 | Evidence or subject content is crafted to instruct the AI to auto-select or auto-confirm (prompt injection) | IWC-REQ-144, 154 |
| W12 | A session's own identifier is mistaken for, or reused as, a CHGR's canonical identifier | IWC-REQ-034, 035, 176 |
| W13 | A session's `Confirmed` state is treated as identical to a CHGR's own `confirmed` lifecycle state | IWC-REQ-115, 116 |
| W14 | Multi-participant machinery is quietly built into the single-participant session model, disturbing its state shape | IWC-REQ-162–164, 167 |
| W15 | An implementation claims Publication-Handoff ownership without separate authorization | IWC-REQ-171 |

No scenario above required inventing a new mitigation outside the §21
requirement set; each citation above resolves to a requirement already
present in §21.1–§21.20.

---

## 23. Success Criteria

IWC-001 is contractually demonstrated successful, without requiring any
implementation, when a future implementing phase can show:

1. A Decision Session can carry a human from Decision Subject presentation
   through Confirmation without requiring hand-authored prose, per §4,
   §6, IWC-REQ-063–069.
2. No default, timeout, silence, or inactivity can substitute for
   Confirmation, per §7, §10.7, IWC-REQ-070–077, IWC-REQ-110–111,
   IWC-REQ-122.
3. Confirmation binds to the exact, currently-valid Preview Digest, never
   to an abstract "confirmed at some point," per §10, IWC-REQ-098–112.
4. AI responsibility remains strictly bounded to assistance, with every
   prohibited operation independently falsifiable, per §5,
   IWC-REQ-050–062.
5. The ten-state session model is implemented unmodified, with no added,
   removed, or merged state, per §4.4, IWC-REQ-040–042.
6. Session state, Confirmation state, CHGR lifecycle state, runtime
   state, and project/phase lifecycle state remain five distinct,
   non-substitutable classes, per §11, IWC-REQ-113–120.
7. Every failure scenario in §12 is handled without accidentally creating
   a governance decision, per IWC-REQ-121–129.
8. A future verifier can reconstruct, from retained Session Audit
   Evidence alone, all seven audit boundaries of §13.1, per
   IWC-REQ-130–136.
9. The Decision Session architecture is demonstrably transport-independent
   across at least two distinct transports, per §16, IWC-REQ-155–161.
10. Every adversarial scenario in §22 remains mitigated by a citable
    requirement, not by narrative assurance alone.

---

## Non-Goals

This contract does not authorize, perform, or imply any of the following:

- **Session implementation.** No `src/pcae/governance/session.py` or
  equivalent is created; no session engine of any kind is implemented.
- **CLI implementation.** No command, flag, or exit-code contract for a
  Decision Session is created or implemented.
- **Persistence implementation.** No file, directory, or persistence
  mechanism for session state is created.
- **Publication implementation.** No code path is added that writes a
  CHGR anywhere; `.pcae/governance-records/` remains untouched by this
  contract.
- **Signing implementation.** No cryptographic signing mechanism is
  implemented; §17's signature extension point remains descriptive only.
- **Identity-provider integration.** No external identity-provider
  integration is implemented or authorized.
- **Runtime enforcement.** No runtime code path is added that reads,
  gates on, or enforces anything against Decision Session state; §19.1
  restates a future relationship only.
- **Authority-resolver changes.** No authority-resolution behavior is
  implemented or changed.
- **Modification of CHGR-001.** CHGR-001's text remains byte-identical;
  this contract only restates, without narrowing, obligations CHGR-001
  already imposes, one layer earlier.
- **Modification of Typed Authority Model contracts.** TAMC-001 and
  TAMPC-001 remain byte-identical.
- **Any Stage 3/pilot authorization.** This contract does not advance,
  authorize, or evaluate `GLP-PILOT-C6` or any other GLP-designated
  initiative.
- **New human governance decision.** This contract's own freeze is not
  itself a Human Governance Act and creates no new one; it does not
  perform or presume the GPC6-REQ-075(b) election and does not perform,
  authorize, or imply any GAC-001 §9 Stage 6 governance decision.

## 24. Phase 143I.1 repair confirmation

**Version:** 1.1
**Predecessor:** IWC-001 v1.0 (Phase 143H)
**Repaired by:** Phase 143I.1 — Interactive Workflow Contract
State-Transition Table Repair

**Reason:** Independently reproduced Finding B-1 (Phase 143I Independent
Verification, Blocking) — §4.4's normative state-transition table omitted
required `Cancelled`, `Expired`, and/or `Abandoned` exits from five of
the ten states (`Created`, `EvidenceReady`, `AwaitingClarification`,
`DecisionSelected`, `AwaitingConfirmation`), directly contradicting
IWC-REQ-045, IWC-REQ-046, IWC-REQ-047, and IWC-REQ-160's universal
cancellation/expiry-availability language and §12's universal
abandonment-availability language, while IWC-REQ-042 simultaneously
forbade an implementation from introducing any transition not listed in
§4.4's table. Root cause independently traced to Phase 143G §10.1's
original ten-state table (`docs/PHASE_143G_CANONICAL_HUMAN_GOVERNANCE_RECORD_INTERACTIVE_DECISION_WORKFLOW_ARCHITECTURE.md`,
lines 425–441), which Phase 143H's contract freeze transcribed verbatim
without independently re-deriving exit-list completeness against the
surrounding narrative's own universal-availability claims (143G's own
§11 makes the same "any non-terminal state" abandonment claim its own
§10.1 table did not support); Phase 143H's fifteen-scenario adversarial
pass (W1–W15, §22) contained no scenario shaped to test internal
table-vs-narrative consistency, only external-boundary violations, so the
omission was not detected at freeze time. This defect affects
documentation only as of this repair — no implementation of the
Interactive Workflow exists, so no in-flight behavior is corrected;
absent this repair, a future implementer could not have simultaneously
satisfied IWC-REQ-041/042 and IWC-REQ-045/046/047/160 as originally
drafted.

**Changed requirements:** None. No `IWC-REQ-###` text was added, removed,
renumbered, or reworded. §4.4's table — six missing table cells across
five rows — was widened to add: `Cancelled` and `Expired` to `Created`;
`Cancelled` to `EvidenceReady`; `Cancelled`, `Expired`, and `Abandoned` to
`AwaitingClarification`; `Abandoned` to `DecisionSelected`; `Abandoned` to
`AwaitingConfirmation`. `AwaitingDecision`'s and the four terminal
states' rows are byte-identical to v1.0. §4.4's narrative was extended by
one sentence disclosing the widening and one sentence making explicit
that no terminal state has any exit (a restatement of the pre-existing
invariant, not a new rule). No other section, and no requirement in
§21.1–§21.20, was modified. IWC-REQ-040 (state count), IWC-REQ-041
(pointer to "§4.4's table, unmodified" — now the widened table), and
IWC-REQ-042 (prohibition on unlisted transitions) required no wording
change: IWC-REQ-041's pointer remains accurate by construction, and
IWC-REQ-042's own text constrains state identity, not the transition
list, so its fail-closed purpose is unweakened and unchanged.

**OBS-1 and OBS-2 disposition (Phase 143I observations):**

- **OBS-1** (smart-resume re-affirmation gap, §4.5/§9 resumability
  discretion) — **Not applicable to this repair.** OBS-1 concerns whether
  a resumed session must require fresh re-affirmation of a preserved
  selection before Preview generation; it does not reference §4.4's
  transition table, any of the five widened rows, or any
  cancellation/expiry/abandonment semantics. The table widening changes
  no resumability rule (§4.5, IWC-REQ-043/044 unmodified) and does not
  interact with IWC-REQ-121/127. **Retained, unrepaired, disclosed** —
  remains an implementation-discretion gap for a future implementing
  phase to resolve explicitly, per Phase 143I's own disposition.
- **OBS-2** (§9.2 disclosure regression relative to 143G §21's
  judgment-dependency caveat) — **Not applicable to this repair.** OBS-2
  concerns §9.2's Clarification-vs-Persuasion boundary heading, a
  section untouched by this repair; it has no textual or structural
  dependency on §4.4's transition table. **Retained, unrepaired,
  disclosed** — no minimal wording clarification was necessary to keep
  the amended state contract coherent, since OBS-2 does not bear on
  transition-table coherence.

Neither observation was silently discarded; both are explicitly
carried forward exactly as Phase 143I disclosed them.

**Regression review:** independently reconfirmed unchanged by this
revision — session identity (§4.1, untouched), ownership (§4.2,
untouched), template/subject binding (§4.3, untouched), the state-count
and state-identity invariants (§4.4 narrative's first two sentences and
the ten row labels/entry-conditions, untouched), the ten-state-adoption
judgment call (§4.6, untouched — no state was added, removed, merged, or
renamed, so its reasoning is unaffected), resumability (§4.5, IWC-REQ-043
and IWC-REQ-044, untouched), expiry policy narrative (§4.7, untouched —
already stated the universal claim the table now supports), cancellation
policy narrative (§4.8, untouched — same), replay prevention (§4.9,
untouched), persistence boundary (§4.10, untouched), the Decision
Existence Contract (§7, untouched — "a governance decision exists only
after Confirmation" is independent of which pre-`Confirmed` transitions
exist), Preview Digest/Confirmation binding (§10, untouched), the
Publication Handoff boundary (§2, §11.4, untouched — only `Confirmed`
hands off; the widened table still permits no terminal-state hand-off
from `Cancelled`/`Expired`/`Abandoned`), the Failure Contract (§12,
untouched text; its abandonment row's "any non-terminal state" claim is
now fully supported by §4.4 rather than contradicted by it), Transport
Independence (§16, untouched), and Success Criteria item 5 (§23,
untouched — "implemented unmodified" still means no state added, removed,
or merged, which remains true).

**Compatibility review:** independently confirmed. CHGR-001, TAMC-001,
and TAMPC-001 remain byte-identical (confirmed by independent grep sweep
finding zero references to Decision Session states or IWC-001 in either
Typed Authority Model contract, and confirming CHGR-001 defines
"Interactive Decision Session" only as a term and narrative stage
sequence, never as a state-transition table, so it imposes no
independent constraint this repair could conflict with). No authority
derivation, CHGR lifecycle, publication semantics, runtime consumption,
or Typed Authority semantics is altered. The widened table introduces no
new capability: every added exit is to an already-existing terminal
state via an already-existing, already-defined transition kind
(cancellation, expiry, abandonment), none of which creates a governance
decision (§7, §10 unchanged) or permits publication from a non-`Confirmed`
terminal state (§11.4 unchanged).

**Adversarial validation:** the twenty scenarios required by this
repair's governing prompt were each evaluated against the widened §4.4
table and resolve deterministically:

1–5. Cancellation from `Created`, `EvidenceReady`, `AwaitingClarification`,
`DecisionSelected`, `AwaitingConfirmation` — all now explicitly permitted
(previously 3 of 5 were table-unlisted); each terminates the session with
no CHGR, per §4.8/IWC-REQ-047/048, unchanged.
6. Expiry from every applicable active state (`Created`, `EvidenceReady`,
`AwaitingDecision`, `AwaitingClarification`, `DecisionSelected`,
`AwaitingConfirmation`) — all now explicitly permitted (previously 2 of 6
were table-unlisted); each terminates per §4.7/IWC-REQ-045/046,
unchanged.
7. Abandonment from every applicable active state — all six now
explicitly permitted (previously 3 of 6 were table-unlisted); each
terminates per §12's Failure Contract, unchanged.
8–9. Cancellation/expiry after `Confirmed` — `Confirmed`'s row lists no
`Cancelled` or `Expired` exit (unmodified by this repair); both remain
impossible, preserving "a Confirmed session shall not transition to
Cancelled" and the equivalent expiry invariant.
10–11. Resumption of an expired or abandoned session — `Expired` and
`Abandoned` remain terminal with no listed exits (unmodified); neither
resumes into any state.
12–14. Confirmation after cancellation, expiry, or abandonment —
`Cancelled`, `Expired`, and `Abandoned` list no exit to
`AwaitingConfirmation` or `Confirmed`; all three remain impossible.
15. Publication from a terminal non-confirmed state — §11.4's Publication
Handoff triggers only from `Confirmed` (unmodified); `Cancelled`,
`Expired`, and `Abandoned` remain terminal with no hand-off, so
publication from any of them remains impossible.
16. An implementation attempting an unlisted transition — IWC-REQ-042
still forbids this; because the table is now complete against every
requirement that claims universal cancellation/expiry/abandonment
availability, no legitimate implementation need for an unlisted
transition remains.
17–18. Concurrent expiry/confirmation and concurrent cancellation/
confirmation — race-condition handling is governed by §10's Preview
Digest currently-valid-content binding (IWC-REQ-098–112, unmodified) and
§4.9's replay prevention (unmodified), not by the state table's static
exit list; the table widening does not alter, weaken, or resolve
concurrency handling, which remains a future implementing phase's
obligation exactly as before this repair.
19. Stale preview following a resume — governed by IWC-REQ-088, 124, 125,
147, 148, 149 (all unmodified); unaffected by this repair.
20. Terminal-state replay — §4.4's narrative now explicitly states no
terminal state has any exit and none may transition into another
terminal or active state (restating, not creating, the pre-existing
invariant); §4.9's replay prevention (unmodified) independently forbids
identifier reuse after any terminal state is reached.

All twenty scenarios resolve deterministically under the repaired
contract; none required a new requirement or a narrowing of any existing
requirement.

**Migration effect:** None. No Interactive Workflow implementation exists
as of this revision (independently reconfirmed — this repair phase
implements nothing, per its own No-Go list below); no in-flight session,
schema, or code path is affected by this documentation-only correction.

**Backward-compatibility impact:** None beyond the widened exit lists
themselves. Every IWC-001 v1.0 requirement remains textually and
positionally unchanged; the ten state names, all ten entry conditions,
`AwaitingDecision`'s exit list, and all four terminal states' exit lists
(`Terminal`, unmodified) are byte-identical to v1.0. A v1.0-conformant
implementation description that already treated cancellation, expiry, and
abandonment as universally available (as the surrounding narrative always
required) needs no change; only a hypothetical implementation that had
relied on §4.4's incomplete table to justify withholding cancellation,
expiry, or abandonment at one of the five affected states would need to
add the now-explicit transition — which IWC-REQ-047/045-046/160 already
obligated it to support.

No implementation of the Interactive Workflow is authorized, performed,
or implied by this repair. No Decision Session schema, persistence,
CLI/TUI/GUI/web/IDE/mobile/API interaction, decision capture, preview
generation, confirmation capture, publication, CHGR creation, storage,
signing, or identity-provider integration is implemented. CHGR-001,
TAMC-001, and TAMPC-001 are not modified. The human/AI responsibility
boundary, Decision Existence semantics, and Typed Authority semantics are
unchanged. Runtime remains State: Observed, Maximum Capability: observe,
Execution Availability: unavailable, unchanged before and after this
repair.

## 25. Post-repair next phase

The expected next phase is **143I.2 — Interactive Workflow Contract
State-Transition Repair Independent Verification**, mirroring the
143H→143I precedent (a contract change is independently re-verified by a
phase distinct from the one that made the change) and the
138C.1→138C.2 / 137M→137MV precedent for repair-then-reverify sequencing.
This recommendation does not authorize 143I.2.
