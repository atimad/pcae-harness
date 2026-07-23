# Phase 143G — Canonical Human Governance Record Interactive Decision Workflow Architecture

**Status:** Complete (architecture-stage design document only; no session, CLI,
TUI, GUI, API, persistence, publication, signature, identity-provider,
runtime-consumption, or authority-resolution capability implemented; no
existing CHGR-001 contract text, Typed Authority Model contract, or runtime
architecture modified)
**Mode:** A dedicated Architecture-stage design (GLP-001 §6.1 Stage 1
pattern) applied to the interactive-workflow layer this repository's
already-verified CHGR schema/artifact foundation (Phase 143E, verified by
Phase 143F/143F.1) does not yet have — not a redesign of CHGR-001, not a
new pilot track, and not itself a Human Governance Act, election, or GAC-001
§9 Stage 6 decision.
**Governing authority:** CHGR-001 v1.0 (FROZEN), Phase 143A architecture,
Phase 143C independent contract verification, Phase 143D implementation
planning, Phase 143E implementation (ground truth: schema/artifact
foundation only), Phase 143F independent verification, Phase 143F.1 report
repair, GLP-001, GAC-001, PGP-001, PPA-001, AGOC-001, TAMC-001, TAMPC-001,
GPC6-001/GPC6R-001/GPC6C-001, `src/pcae/lifecycle.py` (Phase 80A),
`src/pcae/core/canonical_artifact_promotion.py` (Phase 114A),
`src/pcae/core/canonical_engineering_evidence.py` (Phase 134E.1).
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Deliverable:** This design document only. No file under `src/pcae/` is
touched. No schema file under `src/pcae/schema_resources/chgr/` is added,
removed, or modified. No CLI command is added. No file under
`.pcae/governance-records/` is created (that path still does not exist on
disk, confirmed unchanged from Phase 143E/143F).

---

## 0. Framing and Relationship to Prior State

Phase 143E built the CHGR schema and artifact foundation: six frozen JSON
Schema record types (`DecisionTemplate`, `HumanGovernanceRecord`,
`HumanConfirmationEvidence`, `GovernanceRecordProvenance`,
`GovernanceRecordIntegrity`, `GovernanceRecordLifecycleEvent`), a 12-entry
manifest, and three read-only CLI commands (`pcae governance-record
inspect`, `verify`, `template inspect`). Phase 143F independently verified
that foundation (127/129 tests, 12/12 digests, zero authority-bypass
paths) and disclosed one Non-Blocking, non-implementation finding about
canonical-report bookkeeping, since repaired in scope by Phase 143F.1.

What exists today, confirmed directly against the repository rather than
assumed from prior phase prose:

| Exists today | Does not exist today |
|---|---|
| Six CHGR record schemas, frozen and manifest-verified | `DecisionSession` schema (143D planned it; 143E explicitly deferred it — no interactive workflow to have session state) |
| `pcae governance-record inspect/verify/template inspect` (read-only, single-path, no mutation) | `create`, `confirm`, `publish`, `list`, `resume`, `suspend`, `supersede`, `revoke`, `import` — none exist anywhere in `commands/` or the CLI dispatcher |
| `HumanGovernanceRecord`, `HumanConfirmationEvidence`, `GovernanceRecordProvenance`, `GovernanceRecordIntegrity` schemas that describe the *shape* a confirmed decision and its evidence must have | Any code path that produces an instance of those shapes from a live human interaction |
| CHGR-001's normative Interactive Decision Contract (§5), Confirmation Contract (§7), and Decision Template Contract (§6) — binding obligations on what a future workflow must satisfy | Any workflow, session, or engine that satisfies those obligations |
| `.pcae/governance-records/` referenced as a future storage location in Phase 143A §7.2 (evaluated, not adopted) | The directory itself — confirmed absent on disk |

This phase's sole activity is to **architect** the missing layer: the
bounded, interactive, staged workflow by which a named human authority
reviews a Decision Subject, selects among a Decision Template's closed
options, optionally supplies rationale and conditions, previews exact
content, and performs the distinct Confirmation act CHGR-001 §7 requires —
so that a future implementation phase can build it against a design that
has already been checked for consistency with the frozen contract, rather
than improvising the shape of `DecisionSession` and its supporting engines
from scratch.

This phase does not perform any Human Governance Act, does not simulate
GPC6-REQ-075(b) or a GAC-001 §9 Stage 6 election, does not import the
existing election, and does not modify CHGR-001, TAMC-001, TAMPC-001, or
any runtime architecture. Per this repository's standing rule, the phase
prompt is authoritative over scope.

---

## 1. Human Decision Session Architecture

### 1.1 Purpose

A **Decision Session** is the bounded, ephemeral, operational context in
which one human authority works through one Decision Template instance
toward, at most, one Human Decision. It is the missing counterpart to
143D's planned (but 143E-deferred) `DecisionSession` schema type.

### 1.2 Governing Principle

A session is *scaffolding for producing a CHGR*; it is never itself
evidence of a Human Governance Act, is never published, is never assigned
a `chgr-<uuid4>` identifier, and is never referenced by any future
consumer as if it were a record (CHGR-REQ-004, CHGR-REQ-018). Everything a
session does is a rehearsal for a single atomic act — Confirmation
followed immediately by Publication (CHGR-001 §7–§8) — that this phase
does not implement.

### 1.3 Workflow Stages (Session Lifecycle, Narrative Form)

This restates, without narrowing, CHGR-001 §5's normative ordered sequence
and CHGR-REQ-041–048, mapped onto session-internal stages a future
implementation must realize:

1. **Session creation** — a human, through some future transport (§15),
   opens a session bound to exactly one Decision Template and exactly one
   Decision Subject. No content exists yet beyond that binding.
2. **Template selection** — the template is fixed at creation and never
   silently swapped mid-session (§5, §11 below); switching templates
   requires abandoning the session and creating a new one.
3. **Context acquisition** — PCAE tooling assembles authoritative context
   (governing artifact/evidence references) mechanically, never argued or
   weighted (CHGR-REQ-042).
4. **Proposal generation** — PCAE tooling renders the template's fixed
   scaffolding (subject statement, option set, consequence/non-effect
   text) into a session-scoped, unconfirmed proposal. This proposal is an
   AI/system artifact, not a Human Decision (§16 below; CHGR-001 §16).
5. **Evidence presentation** — the assembled context is shown to the human
   (§6 below).
6. **Clarification** — the human may ask questions; the AI may explain,
   never persuade (§7 below).
7. **Rationale collection** — an optional, entirely human-authored free
   text field (CHGR-REQ-045).
8. **Decision selection** — the human picks exactly one option from the
   template's closed, exhaustive set (CHGR-REQ-043).
9. **Preview generation** — an exact, verbatim rendering of what
   Confirmation would publish, generated deterministically from session
   state (§9 below; CHGR-REQ-047).
10. **Confirmation** — the distinct, non-defaultable act of §9 below
    (CHGR-001 §7).
11. **CHGR generation** — the confirmed content is handed to Publication
    (CHGR-001 §8), which this phase does not implement; a future
    implementation phase performs this step, immediately and atomically,
    never as a session-owned responsibility.
12. **Publication (future)** — out of this phase's scope entirely; §18
    below states precisely where session responsibility ends and
    Publication's already-frozen contract begins.

### 1.4 A Session Never Becomes a Governance Record

No session state, by itself, satisfies any entry condition in CHGR-001
§13.1's eight-state record model. A session reaching its terminal
`Confirmed` state (§10 below) produces the *input* to Publication; it does
not, by reaching that state, publish anything. This mirrors CHGR-001
§13.2's requirement that Confirmation and Publication remain two distinct
acts, extended one level earlier: Session-Confirmed and Record-Confirmed
are related but not identical concepts (§18 below disambiguates them
precisely).

---

## 2. Session Identity

### 2.1 Chosen Form

**`CDS-<uuid4>`** ("Confirmable Decision Session"), deliberately
namespace-distinct from `chgr-<uuid4>` (the CHGR record identity Phase
143E already implemented) and from `cltr_cutover`'s identifiers (Typed
Authority Model), so that a session ID can never be mistaken for, or
substituted for, a record ID at any layer, including logging and error
messages.

### 2.2 Rejected Alternative

Reusing the eventual CHGR record ID pre-assigned at session creation was
considered and rejected: CHGR-001 §9's Canonical Identity Contract
(CHGR-REQ-076) requires a record's identifier be assigned **only at
confirmed Publication** — pre-minting one at session creation would either
violate that requirement directly or require silently discarding
pre-minted IDs for abandoned sessions, creating an observable identifier
gap CHGR-001 never anticipated. Session identity and record identity must
therefore be assigned by two structurally separate allocators, at two
different times, under two different prefixes.

### 2.3 Identity Requirements

| Requirement | Design |
|---|---|
| Uniqueness | UUID4, collision-resistant without a central counter (unlike CHGR's monotonic sequence — a session has no need for the ordering property a canonical record's sequence provides) |
| Session identity never becomes governance authority | A session ID never appears in a published CHGR's substantive content; only the resulting record's own `chgr-<uuid4>` ID is ever cited by future consumers (§13 mirrors this) |
| Lifecycle | Bound to exactly one Decision Template and one Decision Subject for its entire life (§1.3); a session cannot be repurposed |
| Ownership | Bound at creation to the identity of the human who created it (§10.1's assurance-level identity evidence, reused here at session scope, not yet at record-confirmation strength) |
| Persistence boundary | A session's state is **operational, ephemeral storage** (§14), structurally distinct from CHGR canonical storage (§7 of 143A/143E); a future implementation must not colocate session state files under `.pcae/governance-records/records/` or any path a manifest-driven consumer might mistake for a frozen schema instance |
| Expiry | Every session carries a template-defined or system-default maximum lifetime; an expired session transitions to `Expired` (§10), never silently extends |
| Resumability | A session in `Created` through `AwaitingConfirmation` MAY be resumed by the same bound identity; resumption never skips a stage — a resumed session re-enters exactly the stage it left, with the same content, never a fast-forwarded or auto-confirmed state (§11 below) |
| Cancellation | A human MAY cancel a session at any point before Confirmation; cancellation is terminal and produces no CHGR, no partial record, and no residual claim on the session's template/subject binding |
| Replay prevention | A session ID, once it reaches `Confirmed` or `Cancelled`/`Expired`/`Abandoned`, is never reused for a new interaction; a new decision requires a new session, even against the same template and subject (mirrors CHGR-REQ-077's non-reuse rule for record identity, applied one layer earlier) |

---

## 3. AI Responsibilities

This section restates, at session-architecture granularity, CHGR-001 §4's
Human Authorship Contract (CHGR-REQ-031–038) and 143A §3.4, without
narrowing either.

### 3.1 What AI/PCAE Tooling May Do

| Responsibility | Bound by |
|---|---|
| Assemble governing evidence and authoritative context | CHGR-REQ-042 |
| Present the template's fixed scaffolding, options, and mandatory non-effect statements | CHGR-REQ-044, CHGR-REQ-032 |
| Validate that a selection exists among the closed set and that required fields are present | CHGR-REQ-032, CHGR-REQ-054 |
| Explain consequences and non-effects verbatim from the template | CHGR-REQ-044 |
| Identify conflicts (e.g., stale evidence, a template version mismatch) and surface them, never silently resolve them | CHGR-REQ-030 (fail-closed ambiguity) |
| Highlight missing required information without supplying it | CHGR-REQ-054 |
| Answer clarifying questions about what a template's fixed text means (§7 below) | 143A §3.4 |
| Produce the deterministic preview (§9) | CHGR-REQ-023, CHGR-REQ-047 |

### 3.2 What AI/PCAE Tooling SHALL NOT Do

Restated verbatim in force from CHGR-REQ-033–036 and CHGR-REQ-057:

- SHALL NOT choose an option on the human's behalf.
- SHALL NOT infer a selection from partial input, or optimize a selection
  toward any outcome.
- SHALL NOT fabricate, complete, reinterpret, broaden, or narrow a
  human-authored rationale or condition field.
- SHALL NOT silently modify a human's already-made selection.
- SHALL NOT elevate the assurance level, authority basis, or eligibility
  claimed for a decision beyond what session evidence actually supports.
- SHALL NOT perform Confirmation on the human's behalf under any
  circumstance, including where the system judges itself confident of
  what the human would want (CHGR-REQ-036).
- SHALL NOT embed, suggest, or order options to imply a preferred or
  default choice (CHGR-REQ-057), including through clarification-stage
  phrasing (§7 below draws this boundary precisely).

### 3.3 Mechanical, Not Stylistic, Separation

Per CHGR-REQ-037/038, a session's internal representation SHALL make the
AI-authored/human-authored boundary structurally visible — e.g., distinct
fields for `machine_scaffolding_text`, `machine_boundary_language`,
`human_rationale_text`, `human_conditions_text`, `human_selection_id` —
never a single free-form transcript a verifier would have to parse by
prose tone to determine authorship.

---

## 4. Human Responsibilities

| Responsibility | Never implicit because |
|---|---|
| Selecting a decision from the closed option set | CHGR-REQ-021: absence of input is never a selection |
| Supplying rationale (where the template requires it) or choosing to leave it blank (where optional) | CHGR-REQ-040/045: optional unless the template's own text mandates it |
| Acknowledging disclosures (mandatory non-effect statements) | §6.4 below: acknowledgement is itself a tracked, explicit step, never inferred from having merely viewed the screen |
| Reviewing the exact preview before Confirmation | CHGR-REQ-047, CHGR-REQ-060 |
| Performing Confirmation as a distinct, deliberate act | CHGR-REQ-059–062 |

No architecture element in this design permits implicit consent: every
one of these five responsibilities requires session state to record an
explicit, attributable human action before the session may advance past
the stage that action gates (§10's state model formalizes the gating).

---

## 5. Decision Template Architecture (Interactive Operation)

CHGR-001 §6 and 143A §4 already freeze what a Decision Template *is* and
what it *must specify* (CHGR-REQ-049–058); this section architects how an
already-governed template *operates* inside a live session, without
redefining template governance itself.

| Concern | Design |
|---|---|
| Versioning | A session binds to one immutable template **version** at creation (§1.3 stage 2); if the template is amended mid-session (a governed change process event, never a session-time edit per CHGR-REQ-058), the session's bound version is unaffected — this is a stale-template scenario handled in §11 |
| Mandatory fields | Enforced identically to CHGR-REQ-054: a session cannot reach `AwaitingConfirmation` while any required field is unpopulated |
| Optional rationale | A session's rationale field is absent from the required-field gate unless the bound template's own text marks it mandatory (CHGR-REQ-040) |
| Branching logic | A template MAY define conditional follow-up fields keyed to the selected option (e.g., "if Option C, a scope-limitation field becomes required"); branching is evaluated deterministically from the template's own declarative rules, never from AI judgment about what question "makes sense" next |
| Conditional questions | Same rule as branching: template-declared, not session-improvised |
| Disclosures | Mandatory non-effect statements (CHGR-REQ-044, CHGR-REQ-055) are rendered verbatim and require an explicit acknowledgement step (§6.4) before the option they attach to can be selected |
| Consequence summaries | Machine-rendered per option, verbatim from the template (CHGR-REQ-055) |
| Non-effect summaries | Same, mandatory, never optional (CHGR-REQ-055, generalizing GAC-REQ-043's automatic-adoption prohibition) |
| Evidence references | A template MAY declare which evidence classes its Decision Subject requires (§6 below); the session's context-acquisition stage (§1.3 stage 3) is driven by this declaration |
| Validation | A session validates structurally (required fields present, selection within closed set) using the same schema discipline Phase 143E's `governance/verification.py` already applies to published records — architected here as a **pre-publication** validation pass a future implementation reuses, never duplicates with different rules |
| Extensibility | New template fields extend the interactive engine only by adding new declarative template vocabulary (§17); the session-stage-machine (§1.3, §10) itself never changes shape to accommodate a new template |

Templates remain authority-neutral throughout: nothing in this section
grants a template the power to determine eligibility beyond restating
CHGR-REQ-051's requirement that the template itself names the eligible
human authority (§9.3 of CHGR-001, and the NB-1 resolution 143D/143E
already adopted — eligibility is read from the template's own
`eligible_authority` field, never from a generic role lookup).

---

## 6. Evidence Presentation

### 6.1 Deterministic Assembly

Evidence presentation is a pure function of: the Decision Subject, the
bound template's evidence-class declarations (§5), and the state of the
governing artifacts at context-acquisition time (§1.3 stage 3). Given
identical inputs, two independent sessions against the same template and
subject SHALL assemble identical evidence, mirroring CHGR-REQ-023's
determinism requirement one layer earlier than record rendering.

### 6.2 Evidence Categories

| Category | Handling |
|---|---|
| Governing references | Cited by path/identifier, never inlined-and-editorialized; PCAE tooling assembles the list, never ranks or weights it (CHGR-REQ-042) |
| Supporting references | Same rule; a "supporting" label is template-declared, not AI-judged |
| Provenance of the evidence itself | Each cited artifact's own provenance (e.g., a prior CHGR's ID + digest, a contract's version) is carried alongside the citation, not asserted separately |
| Uncertainty | Where an evidence item's currency cannot be confirmed (e.g., a referenced file's digest doesn't match a recorded value), the session surfaces this explicitly rather than silently presenting the citation as trustworthy (fail-closed, CHGR-REQ-030) |
| Unavailable evidence | A template-declared evidence class that cannot be resolved (missing file, unreachable reference) is presented as an explicit gap, never omitted silently — mirrors CHGR-001 §10.1's `repository_provenance.available: bool` pattern already implemented in `governance_record_provenance.schema.json` |
| Conflicting evidence | Where two cited artifacts disagree (e.g., a superseded template version still referenced by an older evidence pointer), the session presents both and flags the conflict; it never picks the "more likely correct" one |
| Derived information | Any evidence PCAE computes (e.g., "this subject already has 2 prior published CHGRs") is labeled as derived/computed, distinct from evidence sourced verbatim from another artifact |

### 6.3 Prevention of Evidence Substitution

A session SHALL NOT allow evidence assembled for one Decision Subject to
be silently reused for another, and SHALL NOT allow evidence assembled at
session-creation time to be presented unchanged at Confirmation time if
the underlying artifacts changed in between without surfacing that drift
(§11, "stale evidence").

### 6.4 Disclosure Acknowledgement

Every mandatory non-effect statement the template attaches to the
in-progress selection requires a distinct, tracked acknowledgement before
the session may proceed to preview generation. Acknowledgement is
recorded as its own field, never inferred from "the human scrolled past
this text" or any other passive signal.

---

## 7. Clarification Model

### 7.1 The Four Distinct Acts

| Act | Definition | Who performs it | Persuasion risk |
|---|---|---|---|
| Explanation | Restating template-fixed scaffolding/boundary text in different words, on request | AI, bounded to the template's own meaning | None — no new claim is introduced |
| Clarification | Answering a factual question about the Decision Subject, evidence, or template mechanics ("what does Option B's non-effect statement mean," "what evidence backs this citation") | AI | Low, but see §7.2 |
| Recommendation | Suggesting which option the human "should" pick | **Nobody.** No architectural element performs this. | N/A — forbidden outright |
| Persuasion | Any framing, emphasis, repetition, or selective evidence presentation intended to move the human toward a particular option | **Nobody.** Forbidden outright. | N/A |

### 7.2 The Explanation/Clarification vs. Persuasion Boundary

The dividing line is **whether the AI's output could be true or useful
regardless of which option the human ultimately picks.** A valid
clarification answer does not change in content based on which option the
AI infers the human is leaning toward; if an answer would differ depending
on an inferred target selection, it is persuasion by construction and is
out of architectural bounds. A future implementation must log every
clarification exchange verbatim as part of session state (§13) precisely
so this boundary is auditable after the fact, not merely asserted by
design.

### 7.3 No Coercive Reframing

Clarification SHALL NOT reframe an option's consequence or non-effect
text — it may only explain the template's own fixed words, never
substitute new wording, even if clearer (mirrors CHGR-REQ-035's
prohibition on reinterpreting a human-authored field, extended here to
forbid reinterpreting the template's own machine-authored text mid-session
in a way that could shade its meaning).

---

## 8. Decision Capture

### 8.1 Captured Fields

| Field | Source | Mandatory? |
|---|---|---|
| Explicit choice identifier | Human selection from the template's closed set | Yes |
| Rationale | Human free text | Only if template requires it |
| Conditions | Human free text | Optional always unless template mandates |
| Scope | Bound from the Decision Subject at session creation, restated at capture time for the human to see, never independently re-derived by the human | Yes (inherited, not entered) |
| Authority basis | The template's own declared authoritative-basis citation (CHGR-REQ-050), attached automatically — the human does not compose this text | Yes (inherited) |
| Disclosures acknowledged | Tracked per §6.4 | Yes, for every disclosure the selected option attaches |
| Confirmation readiness | A computed boolean: true only when every required field above is present and every required disclosure is acknowledged | Yes (computed, never manually overridden) |

### 8.2 No CHGR Before Confirmation

Decision Capture populates session-local state only. Nothing in this
architecture allows a captured-but-unconfirmed selection to be treated,
stored, indexed, or referenced as a CHGR, restating CHGR-REQ-066 and
§16.2's silence/timeout/default prohibition at the session-internal layer.

---

## 9. Confirmation Architecture

### 9.1 Confirmation as a Distinct Stage

Restating CHGR-001 §7 (CHGR-REQ-059–066) at session-architecture
granularity:

| Requirement | Session-level design |
|---|---|
| Immutable preview | Once decision capture (§8) reaches Confirmation-readiness, the session computes a preview that is a pure function of captured content (mirrors CHGR-REQ-023); this preview is fixed the instant Confirmation begins |
| Exact-content confirmation | The human is shown the literal content that will become the CHGR's provenance-recorded preview (CHGR-REQ-085) — no paraphrase, no summary view |
| Acknowledgement | A distinct, tracked act, separate from having merely viewed the preview |
| Replay protection | A confirmation act is bound to a specific preview-content digest (§9.2); presenting that same confirmation evidence against different content is rejected, never silently accepted |
| Interruption | If the session is interrupted between preview generation and Confirmation, resuming re-renders the preview from current session state rather than reusing a cached rendering, so an interruption can never smuggle stale content past a human who resumes expecting to see what they last reviewed |
| Cancellation | Always available up to the instant Confirmation completes; no point in the flow is "too late to cancel" until Confirmation itself has occurred |
| Stale preview detection | §9.2 |

### 9.2 Stale Preview Detection

The session computes and stores a content digest of the exact preview at
the moment it is generated (mirroring `governance_record_integrity.schema.json`'s
`payload_digest`/`rendering_digest` pattern already implemented for
published records, applied here pre-publication). Confirmation SHALL
recompute this digest against current session content immediately before
accepting the confirming action; a mismatch (caused by, e.g., a
concurrent template amendment invalidating cached evidence, or a bug that
mutated session state after preview generation) fails closed: Confirmation
is refused and the human is shown a freshly regenerated preview rather
than being allowed to confirm content they did not actually review.

### 9.3 Binding to Exact Content

This is the single most safety-critical property in this document:
**Confirmation binds to the exact digest of what was shown, not to "the
current state of the session" in the abstract.** No implementation may
satisfy Confirmation by checking "has the human clicked confirm at some
point in this session" — it must check "does the human's confirming
action carry evidence tied to this specific, currently-valid preview
digest."

---

## 10. Session State Model

### 10.1 Canonical States (Independently Derived)

The governing prompt's own §10 lists ten candidate states. This
architecture adopts all ten, unmodified, as the complete session state
model, because each names a structurally distinct condition no other
listed state can represent without loss of information (the same
fail-closed reasoning CHGR-001 §13.4 used to justify retaining
`invalidated` against a shorter prompt-provided list):

| State | Entry condition | Exit transitions |
|---|---|---|
| `Created` | Session opened, bound to template + subject | → `EvidenceReady`, → `Abandoned` |
| `EvidenceReady` | Context acquisition (§1.3 stage 3) complete | → `AwaitingDecision`, → `Expired`, → `Abandoned` |
| `AwaitingDecision` | Options presented, no selection yet | → `AwaitingClarification`, → `DecisionSelected`, → `Expired`, → `Cancelled`, → `Abandoned` |
| `AwaitingClarification` | A clarification exchange is in progress (§7) | → `AwaitingDecision` (always returns here, never advances past it directly) |
| `DecisionSelected` | A selection plus all required fields/disclosures are captured (§8) | → `AwaitingConfirmation`, → `AwaitingDecision` (human changes selection), → `Cancelled`, → `Expired` |
| `AwaitingConfirmation` | Preview generated (§9), awaiting the distinct confirming act | → `Confirmed`, → `DecisionSelected` (human backs out to change something), → `Cancelled`, → `Expired` |
| `Confirmed` | Confirmation act completed and digest-matched (§9.2–9.3) | Terminal for session purposes — hands off to Publication (§18), never re-enters any earlier state |
| `Cancelled` | Human explicitly cancels at any point before `Confirmed` | Terminal |
| `Expired` | Session's maximum lifetime elapsed before `Confirmed` | Terminal |
| `Abandoned` | Session inactive past a shorter idle threshold than full expiry, or explicitly discarded without formal cancellation | Terminal |

### 10.2 No State Implies Authority

Consistent with CHGR-REQ-080/090–097 applied one layer earlier: reaching
`Confirmed` is evidence a human performed the Confirmation act inside
*this* session — it is not, by itself, proof the human held eligible
authority under the bound template (that check belongs to Publication and
any future runtime consumer, per CHGR-001 §9 and §17, neither of which
this phase implements or accelerates).

### 10.3 Distinctness from `Expired`/`Abandoned`

`Expired` is a template/system-defined maximum-lifetime timeout;
`Abandoned` is a shorter idle-inactivity threshold or an explicit discard
short of formal `Cancelled`. Both are terminal, both produce no CHGR, and
neither differs in effect — the distinction exists only so a future audit
can tell "this ran out of allotted time" from "this was quietly walked
away from," which is diagnostically useful without being safety-critical.

---

## 11. Failure Recovery

| Scenario | Recovery design |
|---|---|
| Interruption (process crash, connection loss) | Session state persisted after every stage transition (§14); resuming re-enters the exact last-persisted state, never a reconstructed guess |
| Timeout | Governed by `Expired` (§10); no silent extension, no auto-confirmation on timeout (CHGR-REQ-063) |
| Stale template | If the bound template version is amended after session creation, the session's own bound version remains authoritative for that session (§5); the session surfaces "a newer template version now exists" as an informational note, never auto-migrates mid-session content to the new version |
| Stale evidence | Detected at preview-(re)generation time (§9.2); triggers a fresh evidence re-assembly (§6.3) and a fresh preview, never a silent reuse of outdated evidence |
| Validation failure | A required-field or closed-set violation blocks advancement past `AwaitingDecision`/`DecisionSelected`; the failure is surfaced to the human, never silently defaulted or auto-corrected |
| Abandoned session | Reachable from any non-terminal state via inactivity past the abandonment threshold (§10.3); produces no CHGR |
| Partial progress | Preserved verbatim across a resume (§2.3); nothing is lost, but nothing already reviewed is silently re-presented as still-current without the staleness checks above |
| Resumed session | Re-enters at the exact stage left; a resume can never fast-forward past Confirmation, and can never resume directly into `Confirmed` — Confirmation must always be freshly performed against a freshly-validated preview (§9.3) |

Recovery preserves determinism throughout: given the same persisted
session state and the same current evidence/template state, resuming
twice produces the same next-presented content both times (extending
CHGR-REQ-023's determinism principle to session-level recovery).

---

## 12. Security Architecture

| Threat | Mitigation |
|---|---|
| Replay (reusing an old confirmation against new content) | §9.2/9.3 digest binding |
| Prompt injection (evidence or subject content attempting to instruct the AI to auto-select or auto-confirm) | §3.2's absolute prohibitions are structural, not instruction-following — no evidence content, however phrased, can cause the AI to perform an act (selection, confirmation) the architecture assigns exclusively to the human; a future implementation must treat all assembled evidence and clarification input as untrusted data, never as executable instruction, mirroring how `governance/verification.py` already treats artifact content as data to validate, never as code to run |
| Hidden defaults | §4/§5: no field in this architecture has a default value path; `Confirmation readiness` (§8.1) is computed strictly from presence, never from a fallback value |
| Accidental confirmation | §9.1's distinct, deliberate, non-defaultable act requirement; no "Enter accepts" path exists anywhere in the state model (§10) |
| Stale previews | §9.2 |
| Altered evidence (evidence tampered with between assembly and confirmation) | §6.3/§9.2's re-validation-at-confirmation-time requirement |
| Altered templates (mid-session tampering) | §5's version-binding; a session's bound template version is immutable for that session's life |
| UI ambiguity (a transport rendering the preview in a way that could mislead) | §15's transport-independence requirement: interaction *semantics* (what must be shown, in what order, with what acknowledgement) are transport-independent and testable independent of any specific UI, so a future CLI/TUI/web implementation cannot satisfy this architecture with an ambiguous rendering, even if its own tests pass in isolation |
| Session hijacking (a different actor resuming someone else's session) | §2.3's ownership-binding requirement: resumption is permitted only to the identity bound at creation; a future implementation must reject a resume attempt from a different identity, fail-closed |
| Forged confirmation | §9.3's digest-and-identity binding: a confirming action must carry both the correct preview digest and evidence of the bound identity (§10.1's assurance-level mechanism), never accepted from identity evidence alone or digest evidence alone |

For every scenario above, this architecture's default response to
ambiguity or a verification gap is to refuse advancement (fail-closed),
never a best-effort or benefit-of-the-doubt default — restating CHGR-REQ-030
one layer earlier than the record-verification layer 143E already
implements it at.

---

## 13. Audit Architecture

### 13.1 Auditable Boundaries

| Boundary | What it separates |
|---|---|
| AI conversation | Free-form exchange during clarification (§7); logged verbatim, never summarized, precisely so the explanation/persuasion boundary (§7.2) remains independently checkable |
| Clarification | A subset of AI conversation, structurally tagged as clarification exchanges distinct from evidence presentation |
| Proposal | The template-rendered scaffolding + option set as presented (§1.3 stage 4) — an AI/system artifact, never itself evidence of a decision |
| Evidence | The assembled context (§6), separately logged from the conversation that discusses it |
| Preview | The exact confirmable content (§9) — a distinct, digest-bound artifact |
| Human decision | The captured selection/rationale/conditions (§8) — tagged as human-authored content, structurally separate from proposal/evidence per §3.3 |
| Confirmation | The distinct act and its evidence (§9), tagged separately from decision capture even though they occur in sequence |
| Resulting CHGR | Produced by Publication (§18), outside this phase's scope; the audit trail up to `Confirmed` is handed to Publication as an input, never merged into it silently |

### 13.2 Canonical vs. Non-Canonical

Only the resulting, published CHGR (once a future implementation phase
builds Publication) becomes canonical per CHGR-001's own discipline. Every
artifact in §13.1's list up through `Confirmed` is **session audit
evidence** — retained per §14's privacy architecture, citable by a future
verifier reconstructing "what led to this decision," but never itself a
CHGR, never itself published, and never itself carrying independent
authority (mirrors CHGR-REQ-004's proposal/record separation, applied
across the entire pre-publication trail, not just to the final proposal
stage).

---

## 14. Privacy Architecture

| State class | Nature | Retention posture |
|---|---|---|
| Temporary interaction state (in-progress session fields, not yet Confirmed) | Ephemeral, mutable | Retained only for the session's own resumability window (§2.3, §11); a future implementation should define a bounded retention period for `Cancelled`/`Expired`/`Abandoned` sessions rather than retaining them indefinitely by default |
| Canonical governance state | The eventual published CHGR (future Publication) | Governed entirely by CHGR-001's own immutability/retention discipline — outside this phase's scope to alter |
| Transient AI conversation (clarification exchanges) | Logged for audit (§13.1) | Retained alongside the session's audit trail, not indefinitely by default; a future implementation determines a concrete retention window as an implementation decision, bounded by this architecture's requirement that retention never be unbounded-by-default |
| Retained audit evidence (post-Confirmation trail handed to Publication) | Becomes part of the CHGR's own provenance per CHGR-001 §10/§12.1 (`what was presented, what was selected, when, exact preview content`) | Governed by CHGR-001's provenance retention discipline once Publication exists |

This architecture avoids unnecessary retention by design: nothing in §1–13
requires retaining full conversational transcripts beyond what CHGR-001
§10's provenance requirements already demand (options presented, exact
preview content, confirmation evidence) — a future implementation MAY
retain more for audit richness, but this architecture does not require it,
and any additional retention is itself a privacy decision a future
implementation phase must make explicitly, not one this document mandates.

---

## 15. Accessibility and Transport Independence

### 15.1 Principle

Everything in §1–14 is specified in terms of **stages, states, and
required acts**, never in terms of keystrokes, screens, HTTP verbs, or
widget types. A CLI prompt sequence, a TUI form, a web wizard, an IDE
panel, a REST API exchange, and a mobile flow are all equally valid
transports for the same underlying session architecture, provided each:

- Presents the Decision Subject before any option (§1.3 stage 1).
- Presents the full, un-editorialized option set with no visual emphasis
  implying a preferred choice (§3.2, §5).
- Requires the same distinct, non-defaultable Confirmation act bound to
  the same exact-preview-digest discipline (§9).
- Exposes cancellation at every non-terminal stage (§2.3).
- Cannot silently skip disclosure acknowledgement (§6.4) or clarification
  logging (§13.1) merely because a given transport makes it easy to omit.

### 15.2 What Is Deliberately Left Open

Concrete flag syntax, screen layouts, HTTP routes, and API payload shapes
are implementation concerns for the phase(s) that eventually build a
specific transport (mirroring 143A §13.1's identical stance toward CLI
syntax). This phase defines the semantics a transport must satisfy, not
the transport itself.

---

## 16. Multi-Participant Architecture

### 16.1 Deferred Capability, Clearly Distinguished

The following are explicitly **out of scope for implementation** and are
named here only to establish where a future extension would attach
without redesigning §1–15:

| Future capability | Attachment point |
|---|---|
| Multiple reviewers | A template could declare more than one eligible-authority slot; the session model would need a `participants` concept this architecture does not define |
| Delegated authority | Would extend §9's identity-binding to a delegation record — itself a candidate future CHGR type, not something this phase invents |
| Sequential approvals | Would chain multiple sessions, each producing its own Confirmed decision, linked via CHGR-001 §13's existing supersession/predecessor-successor mechanics — no new state-model concept required, only a linking convention |
| Quorum | Requires the L5 "multi-party confirmation" assurance level CHGR-001 §12 already reserves as an open extension point; this phase's single-participant session model is the L0–L1 case that quorum would extend, not replace |
| Committee decisions | Same as quorum; a committee decision is architecturally a quorum-bound multi-session aggregation, not a new session state |

### 16.2 Why Deferred

None of the above is required to satisfy CHGR-001's frozen text for a
single-authority decision (the only kind the existing GPC6-REQ-075(b)
election, and every Decision Template CHGR-001 §6 currently anticipates,
actually is). Building multi-participant machinery now would be
architecture speculatively extending beyond what any frozen contract
requires — this phase names the attachment points precisely so a future,
separately scoped and separately authorized phase can add them without
disturbing §1–15's single-participant design.

---

## 17. Extensibility

| Future capability | How §1–16 accommodate it without redesign |
|---|---|
| Signatures | An additional confirmation-evidence class at §9, extending CHGR-001 §12's already-open L0–L5 assurance model; §9.3's digest-binding is signature-algorithm-agnostic |
| Enterprise identity | An additional identity-evidence source at §2.3/§10.1's ownership-binding, again within the existing L0–L5 extension point |
| Policy engines | Could evaluate template eligibility (§5) or evidence sufficiency (§6) as an additional gate before `AwaitingConfirmation`; the session state model (§10) already has a natural insertion point (an additional check within `EvidenceReady`/`AwaitingDecision`) without adding a new state |
| Workflow automation | Could drive session creation and context acquisition (§1.3 stages 1–3) programmatically; it can never drive decision selection or Confirmation (§3.2, §9) without becoming a prohibited AI-selection or AI-confirmation path — automation is bounded to the same scaffolding role any AI tooling already has |
| Delegated authority | §16.1 |
| External governance systems | Could supply evidence (§6) or identity assertions (§10.1, an L4 assurance level already reserved) as additional inputs; they cannot supply a selection or a confirmation without violating §3.2/§9 regardless of how "external" or "authoritative" the system claims to be |

No item in this table requires altering the state model (§10), the
confirmation binding (§9), or the human/AI responsibility boundary
(§3–4) — each is a new input source or evidence class layered onto the
existing architecture, consistent with CHGR-001 §12's stated design
principle that assurance levels are "an open extension point, not a closed
enumeration."

---

## 18. Relationship to CHGR Foundation

| Concept | Exists when | Distinct from |
|---|---|---|
| Session exists | From `Created` (§10.1) | Never itself a CHGR (§1.4) |
| Decision exists | From `DecisionSelected` (§10.1) — captured (§8), not yet confirmed | A decision without Confirmation has no evidentiary weight beyond "a human, at this point, had selected this" — it can be changed or abandoned freely |
| Confirmation exists | At session `Confirmed` (§10.1, §9) | Session-Confirmed is the input to record-Confirmation; a future implementation must not conflate the session reaching `Confirmed` with the future `HumanGovernanceRecord`'s own `lifecycle_state` reaching `confirmed` — they are related one-to-one for a successful session, but they are not the same field, the same timestamp, or the same artifact. Session-Confirmed evidence becomes the record's `confirmation_evidence_ref` payload once Publication (§18.2) runs; it does not retroactively become the record's own state before that. |
| CHGR exists | Only after a future Publication implementation runs (§18.2) — outside this phase | Every earlier row |
| Publication exists | Not built by this phase; CHGR-001 §8 already defines what it must do (atomic, immediately following Confirmation, assigns identity, captures provenance/integrity) | This phase supplies Publication's *input* (a session that reached `Confirmed`) but implements none of Publication itself |

### 18.1 Why These Remain Distinct Concepts

Collapsing "session Confirmed" and "record published" into one concept
would violate CHGR-001 §13.2's explicit requirement that Confirmation and
Publication remain two distinct states and two distinct acts (restated at
the session layer: session-Confirmed and CHGR-published must remain
separable so a future audit can distinguish "the human confirmed this
content in this session" from "this content was atomically committed to
canonical storage," exactly the same audit capability CHGR-001 §13.2
protects at the record layer).

### 18.2 The Publication Handoff (Described, Not Implemented)

A future implementation phase that builds Publication takes, as its sole
input, a session in state `Confirmed`: its bound template reference, its
captured decision content (§8.1), its exact preview and preview digest
(§9.2), and its confirmation evidence (§9.3). Publication then performs
exactly what CHGR-001 §8 already requires — atomically, immediately, with
no discretionary step — and the session's own lifecycle ends at
`Confirmed`; it has no further responsibility once handoff occurs. This
phase does not build the handoff mechanism, only names its exact
boundary.

---

## 19. Relationship to Runtime

Restating CHGR-001 §17 (CHGR-REQ-fixed future boundary) at the session
layer, with no addition to what that section already authorizes:

- **Runtime never observes an unconfirmed decision.** No session state
  before `Confirmed` is visible to, or consumable by, any runtime
  component — there is no code path today, and this phase creates none,
  by which runtime could even attempt this.
- **Runtime never consumes a session.** A session is not a `record_type`
  in CHGR-001's schema family and never will be, per §1.2/§1.4 above; a
  session is not eligible for the `record` identity namespace (§2), the
  manifest (§3), or any future runtime-consumption check CHGR-001 §17.1
  describes.
- **Runtime consumes only published CHGR artifacts, in future phases.**
  Exactly as CHGR-001 §17.2 already states: no runtime code path reads
  `.pcae/governance-records/` today, and this phase does not create one.

No runtime capability is introduced by this phase. `pcae runtime inspect`
before and after this phase's own completion shows Runtime state Observed,
execution capability unavailable, maximum plugin capability observe —
unchanged.

---

## 20. State Separation

| State class | Owned by | Never substitutes for |
|---|---|---|
| Session state (§10) | This architecture, once implemented | CHGR record lifecycle state — a session reaching `Confirmed` is not the same fact as a record's `lifecycle_state` field reaching `confirmed` (§18) |
| Confirmation state (§9's digest-bound evidence) | This architecture | Publication — Confirmation evidence is an *input* to Publication, never Publication itself (CHGR-001 §7 vs. §8) |
| CHGR lifecycle state | CHGR-001 §13.1 (already frozen, already implemented as a schema enum in `human_governance_record.schema.json`) | Session state or PCAE phase/task lifecycle |
| Runtime state | `pcae runtime inspect` (existing, unrelated machinery) | Any of the above — CHGR-001 §17/INV-13 already establishes runtime neutrality; this phase adds nothing that could create coupling |
| Project/phase lifecycle | `PROJECT_STATUS.md`, `.pcae/phase-completion-*`, `pcae phase complete` (existing, unrelated machinery, per CHGR-001 §15) | Any of the above — a governed phase producing this architecture document does not advance, and is not advanced by, any session or CHGR state |

No architectural element in this document allows one of these five state
classes to be read, written, or inferred as if it were another. This is
the same discipline CHGR-001 §15 already enforces between phase reports
and CHGR records, generalized here to cover session state and Confirmation
state as two additional, newly-named classes that did not exist before
this phase.

---

## Deliverables

- **Interaction architecture** — §1, §3, §4, §7.
- **Workflow architecture** — §1.3, §5, §6, §8.
- **State architecture** — §10, §20.
- **Responsibility matrix** — §3.1/§3.2 (AI) and §4 (human), consolidated.
- **Trust-boundary model** — §3.3, §12 (prompt-injection boundary), §18
  (session/record boundary).
- **Confirmation architecture** — §9.
- **Evidence architecture** — §6.
- **Audit architecture** — §13.
- **Security architecture** — §12.
- **Failure architecture** — §11.
- **Extensibility architecture** — §16, §17.
- **Implementation roadmap** — 143H (Contract Freeze) → a future
  Implementation Planning phase → a future Session/Engine Implementation
  phase → a future Publication Implementation phase (only once separately
  scoped) → independent verification at each stage, mirroring the
  143A→143B→143C→143D→143E→143F pattern this track has followed
  throughout. Named for planning purposes only; naming it here authorizes
  none of it (GAC-REQ-023).
- **Architectural risks** — the security table (§12) plus: (a) the
  explanation/persuasion boundary (§7.2) is judgment-dependent and will
  require concrete test scenarios, not just principle, before a future
  implementation can claim compliance; (b) session persistence (§14)
  needs a concrete retention-window decision a future phase must make
  explicitly, since this architecture deliberately leaves it open; (c)
  the Publication handoff (§18.2) is described but unimplemented — a
  future phase could under-specify the exact atomic operation and
  silently reintroduce the collapsed-Confirmation/Publication risk
  CHGR-001 §13.2 exists to prevent.
- **Deferred capability list** — §16 (multi-participant), the concrete
  transport implementations of §15, the Publication implementation of
  §18.2, all six items of §17's extensibility table, and Legacy Import
  (CHGR-001 §14, still not performed by any phase through 143G).

---

## Architecture Validation

| Governing artifact | Consistency check | Result |
|---|---|---|
| CHGR-001 | Every SHALL/SHALL NOT this document restates is quoted or paraphrased without narrowing (§3–9, §18–19 cite specific `CHGR-REQ-###` identifiers throughout) | No contradiction found |
| Typed Authority Model (TAMC-001/TAMPC-001) | This architecture introduces no reuse of, composition with, or dependency on `HumanAuthorization` or any Stage 3 companion schema; session identity (§2) is structurally distinct from `cltr_cutover` identifiers | No contradiction found |
| Advisory Governance contracts (AGOC-001) | This architecture introduces no new advisory artifact class beyond what §16.1 of CHGR-001 already anticipates ("AI proposal" = §1.3 stage 4's proposal) | No contradiction found |
| Canonical artifact architecture (Phase 114A `ArtifactState`, Phase 134E.1 `CanonicalEngineeringEvidence`) | Consulted as non-binding precedent only, exactly as 143A/143C/143D/143E already treat them; this phase composes with neither, consistent with 143D §16 and 143E §0's confirmed non-composition | No contradiction found |
| Lifecycle architecture (`src/pcae/lifecycle.py`, Phase 80A) | Unrelated domain (backend-output-adoption lifecycle); §20 explicitly separates session state from this and from PCAE phase/task lifecycle | No contradiction found |
| Runtime architecture | §19 restates CHGR-001 §17's frozen future boundary without extension; `pcae runtime inspect` unchanged | No contradiction found |

---

## Required No-Go Confirmations

This phase did **not**:

- Modify CHGR-001. (`git diff docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` — empty.)
- Modify Typed Authority Model contracts. (`git diff docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md` — empty.)
- Modify runtime architecture. (No file under `src/pcae/` touched; `pcae runtime inspect` unchanged.)
- Implement sessions. (No `src/pcae/governance/session.py` or equivalent created.)
- Implement persistence. (No file or directory created under `.pcae/`.)
- Implement publication. (No code path writes a CHGR anywhere; `.pcae/governance-records/` remains absent.)
- Implement confirmation capture. (No CLI command added; `pcae governance-record` surface unchanged — still exactly `inspect`, `verify`, `template inspect`.)
- Implement storage. (Same as persistence, above.)
- Implement signatures. (§17 names signatures only as a future extension point; none implemented.)
- Implement identity providers. (§17 names external identity only as a future extension point; none implemented.)
- Implement runtime consumption. (§19 restates the existing frozen non-implementation boundary.)
- Implement authority resolution. (§9.3/§18.1 explicitly defer eligibility/authority checking to Publication and future runtime consumers, neither built here.)
- Implement execution capability. (Runtime remains Observed / observe / unavailable throughout.)
- Perform any human governance decision. (This document is architecture prose; it selects no option, confirms nothing, and publishes nothing.)
- Simulate a GPC6-REQ-075(b) election. (Not referenced as an example beyond citation; not re-run, re-imported, or reinterpreted — `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` is unmodified.)
- Simulate a GAC-001 Stage 6 decision. (No such decision is made or simulated anywhere in this document.)

Runtime remained: **State: Observed. Maximum Capability: observe.
Execution Availability: unavailable.** Confirmed unchanged before and
after this phase via `pcae runtime inspect`.

---

## Exit Criteria

1. Human and AI responsibilities are completely separated — §3, §4.
2. Session architecture is defined — §1, §2, §10.
3. Decision workflow is deterministic — §1.3, §6.1, §9.2, §11 (recovery
   preserves determinism).
4. Confirmation architecture is complete — §9.
5. Session state model is complete — §10.
6. Failure recovery is defined — §11.
7. Security model is complete — §12.
8. Audit model is complete — §13.
9. Privacy boundaries are defined — §14.
10. Future publication integrates cleanly with CHGR — §18.
11. Runtime interaction remains future-only — §19.
12. No implementation has occurred — Required No-Go Confirmations, above;
    confirmed by `git status --short` showing no change under `src/pcae/`,
    `.pcae/governance-records/`, or `docs/contracts/`.
13. No execution capability has been introduced — same evidence.

---

## Phase-Level Validation Evidence

- `git status --short` at phase start: clean.
- No file under `docs/contracts/` modified by this phase.
- No file under `src/pcae/` modified by this phase.
- `.pcae/governance-records/`: confirmed absent before this phase; still
  absent after this phase.
- `pcae governance-record` CLI surface: unchanged (`inspect`, `verify`,
  `template inspect` only).
- `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`: unmodified.
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe — unchanged before and
  after this phase.
- `pcae check`: passed against the active task's allowed-files/allowed-
  zones scope (`docs`, `tasks`, `config`).
- Full `fast_green` test tier: not affected by this phase (no source
  change); re-run for regression confirmation as part of phase close.

---

## Expected Outcome

This document is the approved architecture for the **interactive
human-decision-workflow layer** that sits on top of the already-verified
CHGR schema/artifact foundation. It defines a session model that is
deterministic, explicit, interruption-safe, resumable, provenance-complete,
authority-neutral, lifecycle-neutral, runtime-independent,
transport-independent, and UI-independent, while preserving PCAE's central
governance invariant: humans decide, AI assists, CHGR records, runtime
consumes only after governed publication.

This document does not itself create any of the above — it is a design
for a future contract-freeze phase to convert into falsifiable
obligations, mirroring exactly how Phase 143A preceded Phase 143B.

**Recommended next phase: 143H — Canonical Human Governance Record
Interactive Decision Workflow Contract Freeze.** This recommendation does
not authorize 143H, does not freeze any schema or contract, and does not
itself constitute governance approval of anything described in this
document (GAC-REQ-023).
