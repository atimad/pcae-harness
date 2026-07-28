# CHGR-001 v1.0 — Canonical Human Governance Record Contract

## Contract identity and status

**Contract:** CHGR-001
**Version:** 1.1
**Status:** FROZEN
**Frozen by:** Phase 143B — Canonical Human Governance Record Contract
Freeze
**Revised by:** Phase 146B — CHGR-001 Schema-Envelope Contract Freeze (§26
below; additively specifies schema-envelope/canonical-identity
construction for the `human_governance_record` and its three named
sub-artifacts against the already-frozen `human_governance_record.schema.json`
family, per this contract's own §22 Amendment Contract discipline; no
semantic narrowing of any existing provision)
**Architecture basis:** Phase 143A — Canonical Human Governance Record
Architecture, GLP-001 §6.1 Stage 1 — Architecture, applied to a new,
repository-wide artifact class
(`docs/PHASE_143A_CANONICAL_HUMAN_GOVERNANCE_RECORD_ARCHITECTURE.md`)
**Governed subject:** **Canonical Human Governance Records (CHGR)** — the
durable, canonical representation of a bounded act of human governance
authority: their purpose, definitions, invariants, human-authorship
boundary, interactive-decision workflow, decision-template discipline,
confirmation mechanics, publication mechanics, canonical identity,
provenance, authority boundary, assurance representation, lifecycle,
legacy-import discipline, separation from phase reports and from AI
proposals, future runtime-consumption boundary, security posture,
compatibility with existing PCAE governance, governance responsibility,
audit properties, and amendment discipline.

CHGR-001 v1.0 is the sole normative authority governing **the Canonical
Human Governance Record artifact class**. It does not govern
`GLP-PILOT-C6` or any other GLP-designated initiative's own substantive
content, does not redefine GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001
(collectively, "the framework contracts"), does not redefine or narrow the
Typed Authority Model Consumption Contract (TAMC-001) or the Typed
Authority Model Production Consumption Contract (TAMPC-001), does not
modify GPC6-001, GPC6R-001, or GPC6C-001, and does not modify or
reinterpret the existing `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`
record. Where this contract cites a framework-contract, GPC6-family, or
Typed-Authority-family provision, the citation illustrates an obligation
this contract itself imposes on the CHGR artifact class specifically; it
does not redefine the underlying provision (mirrors GPC6C-001 §1's
identical illustrative-citation discipline, itself mirroring GPC6R-001 §1,
GPC6-001 §1, and AGOC-001 §1 AGOC-REQ-002).

Phase 143A's Architecture stage is the approved design basis for every
section below. This contract independently re-derives every requirement
directly from `docs/PHASE_143A_CANONICAL_HUMAN_GOVERNANCE_RECORD_ARCHITECTURE.md`,
treated as evidence of architectural intent, never as contractual
authority; from `docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
`docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`,
`docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
`docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md`, and
`docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md`, each treated
as independent normative authority a CHGR must remain compatible with, not
merely as cited background; and from
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` and
`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`,
read directly for §19's compatibility analysis rather than assumed from
143A's own summary of them. Where this contract and Phase 143A differ in
force, this contract is normative for CHGR compliance-evaluation purposes
only, and any such difference is itself a defect to be resolved by a
governed contract revision, not by silently preferring one document over
another in practice. Where Phase 143A left a design question genuinely
open, this contract resolves it explicitly and discloses the resolution as
a judgment call, rather than silently picking one reading (see §13.4 and
§20.5 below).

This is contract text only. It does not implement any schema, does not
implement any CLI, does not implement any storage mechanism, does not
implement any migration, does not implement any cryptographic signing,
does not implement any runtime enforcement, does not implement any
authority-resolution behavior, does not modify the existing
GPC6-REQ-075(b) election record, and does not create any new human
governance decision. It preserves every provision of GLP-001, GAC-001,
PGP-001, PPA-001, AGOC-001, TAMC-001, TAMPC-001, GPC6-001, GPC6R-001, and
GPC6C-001, unchanged. Runtime remains Observed / observe / unavailable
throughout every operation this contract governs.

## 0. Normative Language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**,
**SHOULD**, **SHOULD NOT**, and **MAY** are normative, with the meanings
given in GLP-001 §0, which this contract adopts unchanged.

This contract does not itself perform, and is not evidence of, any act of
creating, confirming, publishing, superseding, suspending, revoking, or
importing a CHGR. No provision below authorizes a future implementation
phase to begin merely by this contract's own freeze; §17 and the Non-Goals
below state this explicitly.

Every mandatory obligation below is stated in §23 as a single, atomic,
independently identified `CHGR-REQ-###` requirement. Sections 1–22 state
the normative rules in narrative form; §23 is the authoritative,
falsifiable enumeration of those rules. Where narrative prose in §1–§22
and a requirement in §23 differ in force, §23 is normative.

---

## 1. Purpose

A **Canonical Human Governance Record (CHGR)** is the durable, canonical
representation of a single bounded act of human governance authority,
captured with enough structure to be identified, referenced, verified, and
reasoned about by later governed activity, without PCAE ever selecting,
inferring, or broadening what was decided (143A §1.1).

This contract exists to convert Phase 143A's evidence-derived architecture
(143A §1–§22) into binding, falsifiable `SHALL`/`SHALL NOT` obligations,
per GLP-001 §6.1 Stage 2's own definition ("convert the approved
architecture into a small number of binding, falsifiable obligations...
required outputs: a numbered contract document"), applied here to a new
artifact class rather than to a pilot's own readiness gate — mirroring
exactly how Phase 142A converted Phase 139F into GPC6-001 and Phase 142D
converted Phase 142C into GPC6R-001.

A CHGR is formally distinct from every other artifact class this
repository already governs:

- It is distinct from a **canonical phase report** (`.pcae/phase-completion-report.md`
  / `-metadata.json`), which narrates governed PCAE phase *execution* —
  engineering work performed by an agent, subject to human review — never
  a human's own exercise of governance authority (§15 below).
- It is distinct from a **contract** (`docs/contracts/*.md`), which
  freezes binding obligations governing future conduct, authored through a
  governed Contract Freeze stage — never a record of a single bounded
  decision act.
- It is distinct from a **certification** (e.g., Phase 142I's Stage 3
  Readiness Certification), which is itself a governed evaluation
  procedure's own output — a verdict about whether obligations are
  satisfied — never itself the human decision that a certification's
  existence may later inform.
- It is distinct from a **schema** (e.g., the Stage 3 Typed Authority
  Model's executable schemas), which defines structural shape and
  validation rules for machine data — never a record of what a human
  actually decided.
- It is distinct from an **advisory artifact** (e.g., a `HANDOFF_ADVISORY`
  or a phase's "Recommended Next Phase" text), which carries no authority
  and binds nothing — a CHGR, once published, is evidence that a bounded
  human act occurred, which an advisory artifact by definition is not.
- It is distinct from an **AI proposal**, which originates from an AI or
  agent process and has no authority until a human confirms it — a CHGR's
  substantive content is never AI-authored (§4, §16 below).
- It is distinct from a **runtime observation** (e.g., `pcae runtime
  inspect` output), which reports current system state — a CHGR reports a
  human decision, never a system state, and creates no system state change
  of its own (§17 below).

## 2. Definitions

The following terms are normative and SHALL be used with exactly the
meaning given here by every document, phase, or future implementation that
invokes this contract, in addition to the terms GLP-001 §4, GAC-001 §3,
PGP-001 §3, PPA-001 §3, and AGOC-001's own terminology already define,
which this contract adopts unchanged where applicable.

- **Human Governance Act** — a bounded, attributable exercise of
  governance authority by a named human, expressed as a selection among a
  closed option set, optionally accompanied by rationale and conditions
  (143A §1.2). Examples include an authority election, a governance
  approval, an authorization decision, a risk acceptance, an exception
  approval, a suspension, a revocation, an emergency override, a scope
  limitation, an explicit refusal, a deferral, or an interpretation
  decision.
- **Canonical Human Governance Record (CHGR)** — the durable, canonically
  identified, structured representation of one Human Governance Act,
  captured per this contract's discipline (§1 above).
- **Decision Template** — the governed definition of one class of
  recordable Human Governance Act, specifying eligible authority, subject
  binding, the closed option set, required and optional fields, mandatory
  consequence and non-effect statements, confirmation method, expiry
  rules, and supersession/revocation rules (143A §4).
- **Decision Subject** — the specific entity, pilot, contract, or artifact
  a given CHGR instance concerns, bound to the record at creation time
  from the governing template's own subject definition.
- **Human Decision** — the substantive selection, from a Decision
  Template's closed option set, made by an eligible human authority; the
  core content a CHGR exists to preserve.
- **Confirmation** — the distinct, explicit act by which a human authority
  affirms a rendered decision preview as final, immediately preceding
  publication (§7 below); never inferable from earlier interactive steps
  alone.
- **Publication** — the atomic, system-performed act of writing a
  confirmed Human Decision into canonical, immutable storage, assigning it
  canonical identity (§8 below).
- **Supersession** — the act by which a new, later, published CHGR
  explicitly names a prior CHGR as no longer the current word on its
  subject, without altering the prior record's own content (§13 below).
- **Revocation** — the act by which an eligible human authority
  permanently withdraws a published CHGR's governance effect, terminal and
  irreversible (§13 below).
- **Suspension** — the act by which an eligible human authority
  temporarily marks a published CHGR inert, reversible only through a new,
  linked governance act the record's own template permits (§13 below).
- **Assurance Level** — the explicit, honestly-disclosed strength of
  identity-binding evidence behind a CHGR's Confirmation, drawn from the
  six-level model L0–L5 this contract adopts unchanged from 143A §10.1
  (§12 below).
- **Legacy Governance Record** — a pre-existing, freeform record of a
  Human Governance Act that predates this contract's discipline (the sole
  current instance being `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`),
  eligible for wrapping as a CHGR through the Legacy Import discipline
  without re-electing anything (§14 below).
- **Interactive Decision Session** — the bounded, staged workflow (§5
  below) through which a human authority reviews a Decision Subject and
  authoritative context, selects among a Decision Template's closed
  options, optionally supplies rationale and conditions, previews the
  exact content to be published, and performs Confirmation.

## 3. Core Invariants

The following properties are frozen as mandatory, non-negotiable, and
immutable for every act performed under, or in furtherance of, the CHGR
artifact class. Each is independently re-derived from 143A §2's identical
seventeen-invariant set, condensed here into twelve contractually
falsifiable core invariants; none is invented by this contract, and none
may be waived by convenience or by a future implementation's own
discretion.

1. **Human authorship of substantive decisions.** Every selection,
   rationale, and condition in a CHGR is authored by the named human
   authority, never generated, inferred, or completed by PCAE or any AI
   system (143A INV-1).
2. **AI non-authorship.** No PCAE component or AI system may choose,
   default, pre-select, infer, complete, reinterpret, broaden, narrow,
   negotiate, or confirm a Human Decision on a human's behalf (143A INV-2;
   §4 below).
3. **No inferred consent, no silent defaults.** Absence of input is never
   interpreted as a selection; there is no unselected default option in
   any Decision Template (143A INV-3).
4. **Deterministic rendering.** The human-readable rendering of a CHGR's
   machine-readable content is a pure, reproducible function of that
   content, with no rendering-time randomness or environment-dependence
   (143A INV-8).
5. **Canonical identity.** Every published CHGR has exactly one canonical
   identifier, stable for its lifetime, that never itself establishes
   authority (143A INV-6; §9 below).
6. **Immutable publication.** A published CHGR's substantive fields are
   never edited in place; substantive change requires a new, linked CHGR
   through supersession or revocation (143A INV-9, INV-10; §13 below).
7. **Provenance completeness.** Every published CHGR carries enough
   evidence to reconstruct what was presented, what was selected, and
   when, without ever letting that evidence alone establish authority
   (143A INV-7; §10 below).
8. **Authority neutrality during recording.** The act of recording a CHGR
   confers no authority; a CHGR is evidence that a decision was made,
   never proof that the decision-maker held the authority to make it
   (143A INV-11; §11 below).
9. **Lifecycle neutrality unless separately governed.** A CHGR affects
   PCAE phase lifecycle, task lifecycle, or runtime state only if some
   other, separately governed contract explicitly says so; by default,
   recording a CHGR changes nothing else (143A INV-12, INV-15).
10. **Execution neutrality.** No CHGR, by existing, triggers any
    execution, runtime activation, or capability change (143A INV-13,
    INV-17; §17 below).
11. **Separation from proposals.** An AI-authored proposal is a distinct
    artifact class from a Human Decision; a proposal can never itself
    become a decision through storage, indexing, or reference alone (143A
    INV-16; §16 below).
12. **Fail-closed ambiguity handling.** Any ambiguity in subject,
    authority, scope, or state resolves to "not authoritative here" / "not
    applicable," never to an assumed favorable reading (143A INV-14).

## 4. Human Authorship Contract

Every substantive selection, rationale, and condition recorded in a CHGR
SHALL originate from the named human authority. PCAE tooling MAY explain a
Decision Subject, assemble authoritative context, render a Decision
Template's fixed scaffolding, format a preview, and validate that a
selection exists among a closed set and that required fields are present.
PCAE tooling SHALL NOT choose an option on a human's behalf, infer a
selection from partial input, optimize a selection toward any outcome,
complete a human-authored rationale or condition field, reinterpret a
human's stated selection, broaden or narrow the scope of what was
selected, negotiate among options, or perform Confirmation on a human's
behalf under any circumstance, including a circumstance where the system
judges itself confident of what the human would want (143A §3.4, §17.3;
INV-1, INV-2).

This contract adopts, without modification, 143A §3.3's content-class
separation table distinguishing machine-generated neutral scaffolding,
machine-generated mandatory boundary language, human-selected substantive
choice, optional human-authored rationale, optional human-authored
conditions, and final human Confirmation. A published CHGR's structure
SHALL make this separation mechanically visible to a verifier, not merely
stylistically implied by prose tone.

## 5. Interactive Decision Contract

A CHGR's substantive content SHALL be capturable through a bounded,
interactive workflow so that essay-writing is never required to complete a
Human Governance Act, while every invariant of §3 is preserved throughout.
This contract freezes the following UX principle verbatim from 143A §3.1:

> Interactive structured choice is the default human interface; free-form
> prose is optional unless explicitly required by the governing decision
> template.

The workflow SHALL consist of, in order: presentation of the Decision
Subject; presentation of machine-assembled authoritative context, never
argued or weighted by PCAE; presentation of an exhaustive, mutually
exclusive, closed set of selectable options with no option pre-selected;
presentation of machine-rendered consequence and non-effect statements
drawn verbatim from the governing Decision Template; an optional,
entirely human-authored rationale field; an optional, entirely
human-authored conditions/limitations field; an exact, verbatim preview of
the content that will be published, shown before Confirmation is possible;
the distinct Confirmation act (§7 below); and atomic Publication (§8
below). Free-form rationale and conditions SHALL remain optional in every
Decision Template unless that specific template's own text explicitly
requires a free-form justification field as a mandatory input.

## 6. Decision Template Contract

A Decision Template is the governed definition of one class of recordable
Human Governance Act. Each Decision Template SHALL specify: a stable
decision-type identifier; the authoritative basis (the governing contract
clause(s) that define the decision class); the eligible human authority
who may make the decision; the Decision Subject binding rule; the
exhaustive, closed set of allowed choices, with no open-ended "other"
option that could silently expand scope; which fields are required before
Confirmation is possible; which fields are optional; machine-rendered
consequence statements for each choice; mandatory machine-rendered
non-effect statements for each choice; the confirmation method(s) this
decision class requires; expiry rules, if any; and supersession and
revocation rules (143A §4.2).

No Decision Template SHALL embed a preferred, recommended, or default
choice; order its options to imply a preference; be authored or approved
outside a governed change process; or omit or merge any option that its
own governing contract text names as a distinct outcome (143A §4.3).

## 7. Confirmation Contract

Confirmation SHALL be a distinct act, separate from and never implied by
any earlier interactive step, requiring the human authority to have
reviewed the exact preview content, to acknowledge that content, and to
perform a deliberate, non-defaultable confirming action. Confirmation
SHALL NOT be satisfied by a session timeout, by inactivity, by pressing
Enter on a default value, by any implicit acceptance mechanism, or by any
command-line flag that skips displaying the exact preview content before
confirming (143A §3.2 step 8, §13.2; INV-4).

## 8. Publication Contract

Publication SHALL be an atomic, system-performed act, immediately
following Confirmation, that creates an immutable canonical
representation of the confirmed Human Decision, assigns it stable
canonical identity (§9 below), and captures complete provenance and
integrity evidence (§10 below) as part of the same atomic operation.
Publication, by itself, SHALL NOT establish that the decision-maker held
the authority to make the recorded decision, that the decision is
currently applicable, or that any later action is authorized (143A §7.3,
§9.1; INV-9).

## 9. Canonical Identity Contract

Every published CHGR SHALL carry exactly one canonical identifier, stable
for the record's lifetime, assigned only at confirmed Publication, never
reused or reassigned even after revocation, self-contained and
independent of file path, branch, or remote so that it survives cloning,
forking, or renaming the repository, and never encoding a
template/schema version (143A §6.3). A record's identity, standing alone,
SHALL NOT itself create, imply, or contribute to authority (143A §6.3,
§9.2). References to a CHGR from any other artifact SHALL cite both the
record's identifier and its integrity digest where deterministic
referencing is required (143A §21).

## 10. Provenance Contract

Every published CHGR SHALL carry provenance evidence sufficient to
reconstruct: who provided the decision; how it was provided (confirmation
method and assurance level); what options were presented; what was
selected; the exact preview content the human actually confirmed, stored
verbatim; when Confirmation occurred; what artifact was published and its
content hash; whether the artifact changed after publication; the
repository/commit provenance of the record's own files; and which
Decision Template version, and transitively which governing contract
version, was in force at Confirmation time (143A §12.1). Provenance,
integrity, and authority are normatively distinct: provenance and
integrity demonstrate authenticity and custody of what happened, but
neither, alone or together, ever establishes that the recorded decision is
currently authoritative (143A §12.2, restating INV-11 at the provenance
layer).

## 11. Authority Contract

This contract freezes as its governing principle: **authority derives
solely from the valid human governance act performed by the appropriate
authority within scope.** A CHGR's presence in canonical storage, under a
well-formed identifier, with valid integrity evidence, is proof that a
decision was recorded, never proof that the decision-maker held the
authority to make it. Authority SHALL NOT be inferred from: storage
location; filename or identifier form; the record having been committed to
git; git commit or branch history; an integrity digest matching; a
cryptographic signature, where present; canonical formatting or rendering;
mere repository presence; or Publication having occurred, standing alone
(143A §9.2, §9.3). Authority is established only by the conjunction of
valid human action (an internally consistent decision-maker identity,
Confirmation evidence, and content) and the applicable governing authority
model — the eligible-authority rule the record's own Decision Template
names, ultimately traceable to GPC6-REQ-040-style role ownership (143A
§9.3). Any gap between these two conditions SHALL be surfaced, never
silently resolved in the record's favor.

## 12. Assurance Contract

Every CHGR SHALL carry an explicit `assurance_level` field, drawn from the
six-level model this contract adopts unchanged from 143A §10.1: L0
(explicit typed confirmation), L1 (authenticated local-user confirmation),
L2 (signed confirmation), L3 (hardware-backed confirmation), L4 (external
identity-provider confirmation), and L5 (multi-party confirmation). This
model is an open extension point, not a closed enumeration; a future
signing integration adds a new assurance level rather than requiring a
redesign. This contract does not require cryptographic signing of any
CHGR. A CHGR's validity as a record of a Human Governance Act does not
depend on reaching any particular assurance level; assurance level affects
only how strongly a future consumer may rely on identity-binding strength,
never whether the decision itself is honored. No representation of a CHGR
SHALL claim an assurance level higher than what actually occurred; the
existing GPC6-REQ-075(b) election is, and must remain represented as, L0.

## 13. Record Lifecycle Contract

### 13.1 States frozen

This contract freezes the **eight-state model** 143A §8 designed —
`draft`, `awaiting-human-confirmation`, `confirmed`, `published`,
`suspended`, `superseded`, `revoked`, and `invalidated` — as the complete
CHGR record state model. Each state's permitted entry conditions,
required evidence, permitted transitions, prohibited transitions, and
authority/lifecycle/runtime effect are as 143A §8's table specifies,
adopted here unchanged and without narrowing.

### 13.2 Distinctness of Confirmation and Publication

Confirmation (entry to `confirmed`) and Publication (entry to `published`)
SHALL remain two distinct states and two distinct acts, so a future audit
can distinguish "the human confirmed this text" from "this text was
committed to canonical storage" (143A §8's closing paragraph).

### 13.3 Immutability and correction

A published CHGR's substantive fields (decision selections, rationale,
conditions, decision-maker identity, timestamps, authority basis) SHALL
never be edited in place. A narrow correction path exists only for
rendering or metadata defects that provably do not change meaning; any
correction of doubt is treated as substantive and requires supersession
instead (143A §11.1–§11.3; fail-closed per §3 invariant 12 above).
Restoration from `suspended` to `published` is permitted only where the
governing Decision Template explicitly allows it, and only through a new,
linked governance act — never a silent timer expiry or automatic reversal.
Restoration from `superseded`, `revoked`, or `invalidated` is never
permitted; those states are terminal by design (143A §11.6).

### 13.4 Judgment call: adoption of the eight-state model

143A §8 designed eight states including `invalidated`, while this phase's
own governing prompt's abbreviated list of states to freeze in §13
(`Draft, Awaiting Confirmation, Confirmed, Published, Suspended,
Superseded, Revoked`) names only seven, omitting `Invalidated`, and
explicitly directs this contract to "reconcile/decide and be explicit
about which states you freeze and why." This contract resolves that
question by freezing all **eight** states, including `invalidated`,
because `invalidated` serves a structurally distinct purpose from
`revoked`: revocation is a human's substantive change of mind about a
decision that remains structurally sound, while invalidation is a
fact-finding response to a *structural* defect (a corrupted integrity
digest, a required field discovered missing after the fact) discovered
independently of any human's own reconsideration (143A §11.5). Omitting
`invalidated` would leave no state capable of representing "this record's
own integrity cannot be trusted," forcing a structural-defect finding to
be misrepresented as either a still-valid `published` record or an
inapplicable `revoked` record — either misrepresentation would itself
violate §3 invariant 12 (fail-closed ambiguity handling). The seven-item
list in the governing prompt is therefore read as an abbreviated
enumeration for prompt-drafting brevity, not as a deliberate narrowing
instruction, and this contract's own text is normative per §0 above.

## 14. Legacy Import Contract

A Legacy Governance Record MAY be represented as a CHGR through an import
operation that performs semantic preservation, provenance preservation,
assurance-level honesty, and no re-election. Import SHALL preserve the
source document's exact original wording, retained either as an embedded
evidence attachment or referenced by path and content digest, never
rewritten, reformatted, or "cleaned up." Import SHALL record the source
commit as part of provenance, without claiming the import commit as the
decision's origin. The resulting CHGR's `assurance_level` SHALL be
explicitly marked at the level the original act actually achieved (L0 for
the existing GPC6-REQ-075(b) election) and marked `imported: true,
source: legacy-markdown`; import SHALL NOT add a signature,
authenticated-identity binding, or any assurance marker the original act
never had. Import SHALL preserve the original decision timestamp and the
original's exact confirmation wording, never a paraphrase. Import SHALL
contain no step that presents new options or accepts a new selection —
it is a read-and-wrap operation over already-decided content, never a new
Human Governance Act. Where a conceptual CHGR field cannot be populated
from the source, the import record SHALL disclose that gap explicitly
rather than guessing or leaving it silently blank. Import SHALL NOT
re-run the source decision, SHALL NOT ask the original decision-maker to
re-confirm anything, and SHALL NOT alter the source document, `PROJECT_STATUS.md`'s
existing narrative about the source decision, or any other existing file.

## 15. Phase Separation Contract

Canonical Phase Reports and Canonical Human Governance Records SHALL
remain permanently, structurally separate artifact classes, exactly per
143A §15's table: distinct machinery, distinct authorship discipline,
distinct cardinality (exactly one phase report per phase; many CHGRs per
subject), and distinct write paths. A CHGR SHALL NOT be treated as a
phase, SHALL NOT advance any phase's status, and SHALL NOT be regenerated,
overwritten, or otherwise touched by phase-completion machinery (`pcae
phase complete`, `write_canonical_report()`,
`_check_canonical_metadata_consistency()`). No CHGR workflow SHALL write
to `.pcae/phase-completion-report.md`, `.pcae/phase-completion-metadata.json`,
or `.pcae/phase-reports/`. A phase report MAY cite a CHGR as evidence a
prerequisite decision was made, and a CHGR MAY cite a phase report as
evidence considered, but neither reference converts one artifact class
into the other, and no PCAE phase lifecycle advances solely because a CHGR
exists (143A INV-15).

## 16. Proposal Separation Contract

This contract freezes 143A §16's five distinct artifact classes — AI or
agent proposal, neutral Decision Template, human draft, confirmed Human
Decision, and published CHGR — as permanently distinct, with authority
attaching only where §11 above says it does. An AI-authored proposal
SHALL NOT be stored as, indexed as, or otherwise mistaken for a
`confirmed` or `published` CHGR; proposals have no path into the state
model of §13 at all. Silence, inactivity, timeout, or default selection
SHALL NEVER constitute acceptance and SHALL NEVER cause a state transition
in §13's model, generalizing GAC-REQ-043's "automatic adoption is
forbidden" principle to every CHGR decision class (143A §16.2).

## 17. Runtime Consumption Contract

This contract freezes only the **future** boundary a runtime consumer of
CHGRs would eventually have to respect; it authorizes no runtime
implementation. A future, separately architected and separately
authorized runtime layer might eventually check, before permitting some
governed action: that the cited CHGR identifier exists and matches its
integrity digest; that the record's decision-maker is eligible and its
subject matches the action in question; that the record's current state
is `published`, not suspended, superseded, revoked, or invalidated; that
any template-defined expiry has not passed; that no newer linked record
supersedes it; and that the specific action actually falls within what
the record's own selection authorizes (143A §17.1). This contract
authorizes none of that layer: no runtime code path reads
`.pcae/governance-records/` as of this contract's freeze, no command
gates any other command's behavior on a CHGR's presence, and future
runtime consumers, once separately authorized, SHALL validate a CHGR's
current state and scope rather than trust its mere repository presence
(143A §17.2). No agent, including one producing a future implementation of
this contract, may treat this contract or any implementation of it as
self-authorizing that agent to mint, confirm, or publish a CHGR on a
human's behalf (143A §17.3).

## 18. Security Contract

This contract freezes protections, drawn from 143A §18's seventeen-item
threat table, against: an AI system authoring or selecting a fake human
decision; a preselected option; coercive or editorializing option
wording; a silent default being treated as a selection; a fabricated or
unverified decision-maker identity; a replayed or otherwise obsolete
decision being relied upon; a published record being modified after the
fact; one record being substituted for another under the same identifier;
authority being inferred from scope-adjacent facts it does not actually
cover; a stale or expired authorization being reused; a revoked record
being reused after revocation; a Decision Template being tampered with
outside governed change; a proposal being confused with a published
decision; a phase report being confused with a human decision; import-time
semantic alteration of a Legacy Governance Record; an AI-generated
rationale silently changing the meaning of a human's own selection; and an
AI system confirming a decision on a human's behalf. For every one of
these scenarios, this contract's default response to any detected
ambiguity or verification gap is to treat the affected record as **not
currently authoritative** for the action in question — never a
best-effort or benefit-of-the-doubt default (143A §18.1; §3 invariant
12).

## 19. Compatibility Contract

CHGR SHALL remain compatible with, and SHALL NOT redefine, narrow, or
supersede: PCAE phase lifecycle (unaffected; CHGRs are lifecycle-neutral
by default per §3 invariant 9); canonical phase reports (structurally
separate per §15); phase-completion metadata (unaffected, no shared
field or file); PGP-001's evidence-citation discipline (a published CHGR
SHOULD satisfy PGP-001 §8.2's general evidence-citation discipline once
cited by a phase, without PGP-001 itself being modified); the
`ArtifactState` promotion machine (Phase 114A) — a plausible future
extension target for `draft`/`confirmed`/`published`-adjacent states,
never adopted by this contract itself; `CanonicalEngineeringEvidence`
(Phase 134E.1) — an inspirational precedent for immutability-after-
finalization, never a shared implementation class; the lifecycle-authority
boundaries in `lifecycle.py` (unrelated domain, no overlap); the future
runtime-enforcement architecture (related only through §17's described
future relationship); `PROJECT_STATUS.md` (a published CHGR may be
narratively summarized there, exactly as the existing election already
is, but `PROJECT_STATUS.md` is never the canonical store); and this
repository's own memory/provenance conventions (unaffected; CHGRs are a
repository artifact, not a memory-system artifact).

### 19.1 Typed Authority Model reuse — independent re-confirmation

This contract independently re-confirms, from direct re-reading of
`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md` (TAMC-001)
and `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(TAMPC-001), 143A §19's conclusion that the Stage 3 Typed Authority Model
family SHALL remain a wholly separate artifact family from CHGR, never
composed, subclassed, or wrapped. TAMC-REQ-005 enumerates sixteen frozen
record families, including `human_authorization`; TAMC-REQ-036 states that
the existence or validity of any of these records SHALL NEVER imply
authorization, completion, approval, certification, publication,
execution, runtime permission, or any other operative authority state, and
TAMC-REQ-024/TAMC-REQ-025 forbid any consumer from establishing, inferring,
or treating authority as originating from these records at all. TAMPC-001
narrows this further: TAMPC-REQ-002 requires its one production consumer
(`pcae authority inspect`) to conform to every applicable TAMC-001
requirement, and TAMPC-REQ-010/TAMPC-REQ-011 independently forbid that
consumer from inferring authority or lifecycle state from any input. These
two contracts confirm, at the contract-text level and not merely at 143A's
own architectural-summary level, that a `human_authorization`-family
record is a token-scoped, non-authoritative, execution-permission artifact
for a specific technical cutover attempt — the structural opposite of a
CHGR, which *is* the human's authoritative act by construction, subject
only to §11's own eligibility layer. Reusing or composing CHGR on Typed
Authority Model schemas would either require stripping TAMC-001's
explicit "never establishes authority" disclaimer (weakening a safeguard
another track relies on) or would create a confusing dependency from a
general-purpose governance-decision artifact onto a narrow, dormant,
non-authoritative migration-tooling schema family. Neither is acceptable.
**This contract adopts 143A's separation conclusion unchanged, and
independently confirms it from the Typed Authority contracts' own frozen
text.**

## 20. Governance Responsibility Contract

This contract introduces **no new role, responsibility, or authority**
beyond GPC6-REQ-040's existing table, following the "one owner per
responsibility" discipline GPC6R-001 §3 and GPC6C-001 §4 already apply to
the Stage 3 readiness and certification gates. Responsibility mapping,
restated for the CHGR artifact class from 143A §20's own table:

| Responsibility | Owner | Basis |
|---|---|---|
| Decision Template authorship | An Implementer-class role performing governed template-authoring work, analogous to GPC6-REQ-040's existing Implementer-class rows | §6 above |
| Decision Template approval | Independent Contract Verifier (existing role), reviewing a template against its governing contract before use | §6 above |
| Interactive presentation | PCAE tooling, strictly bounded to scaffolding/boundary language per §4 above | §5 above |
| Human selection | The eligible Human Authority the governing template names — never a new role; the same "Human Authority" concept GPC6-REQ-040 already defines | §4, §5, §11 above |
| Confirmation | The same Human Authority, via the distinct act of §7 | §7 above |
| Publication | System, atomically and immediately following Confirmation, performing no discretionary act | §8 above |
| Custody | Repository/version-control custody; no new custodial role — existing commit/push governance already covers this | §8 above |
| Verification | Independent Contract Verifier or Independent Implementation Verifier (existing roles), depending on what is being verified | §11 above |
| Supersession, suspension, revocation | Only a human authority eligible under the record's own template | §13 above |
| Runtime consumption | **Not yet assigned — an explicitly open question, per §20.5 below** | §17 above |

### 20.5 Judgment call: runtime-consumption ownership left open

143A §20 explicitly declined to assign runtime-consumption ownership to
any existing role, naming it "an open question for 143B" rather than
silently defaulting it onto an adjacent role (e.g., the Independent
Contract Verifier, by analogy to its role elsewhere in this contract).
This contract preserves that gap deliberately rather than resolving it,
because assigning ownership of a capability this contract does not
implement, describe operationally, or authorize (§17 above) would itself
be an instance of inventing authority this contract has no basis to
invent — GPC6-REQ-040's existing table names no role positioned to own a
consumption capability that does not yet architecturally exist. Any
apparent gap here is evidence of a defect requiring a future, separately
governed contract revision once runtime consumption is itself separately
architected and authorized, not license to informally assign the
responsibility now (mirrors GPC6R-REQ-020's identical no-informal-
assignment rule).

## 21. Audit Contract

A future verifier or auditor SHALL always be able to determine, from a
CHGR alone, without requiring conversational or session history: what
decision was made (the selection field(s), verbatim); who made it
(decision-maker identity); under what authority (authority-basis citation
plus the template's eligible-authority rule, checked against §11); using
which Decision Template (template identifier and version); against what
evidence (governing artifact/evidence references, mirroring the existing
election's "Evidence Considered" section); with what conditions
(conditions/limitations field); at what assurance level (§12's explicit
`assurance_level` field); whether the record remains current (its §13
state, checked, never assumed); and whether it was superseded, suspended,
or revoked (predecessor/successor linkage and state). A record's own
dependents (later actions relying on it) are not tracked on the record
itself; any later artifact that relies on a CHGR SHALL itself cite that
CHGR's identifier, the same forward-citation pattern this contract's own
identity block uses, so a future audit tool can build the reverse index by
scanning citations rather than requiring the record to track its own
dependents (143A §21).

## 22. Amendment Contract

CHGR-001 MAY evolve only through governed superseding contracts, each
identifying its predecessor, version, changed requirements, migration
effect, and backward-compatibility impact, mirroring GLP-001 §13
(GLP-REQ-041–043), GAC-001 §18 (GAC-REQ-076–080), and TAMC-001 §15
(TAMC-REQ-065–067)'s identical extensibility discipline. A published
Human Governance Record's own substantive meaning SHALL NEVER change
through an amendment to this contract — CHGR-001's own evolution governs
future recording behavior only, never the retroactive reinterpretation of
an already-published record's content (mirrors GLP-REQ-040's
non-retrospective-invalidation guarantee, restated here for the artifact
class this contract governs rather than for a lifecycle pattern).

---

## 23. Requirement Set

Every substantive `SHALL`/`SHALL NOT`/`MUST` statement in §1–§22 above
corresponds to at least one requirement below. Requirement identifiers are
sequential, stable, non-reused, and independently traceable to the section
they freeze.

### 23.1 Purpose Requirements

**CHGR-REQ-001.** A CHGR SHALL be the durable, canonical representation of
a single bounded act of human governance authority, captured so it can be
identified, referenced, verified, and reasoned about without PCAE ever
selecting, inferring, or broadening what was decided.

**CHGR-REQ-002.** A CHGR SHALL NOT be treated as, substituted for, or
conflated with a canonical phase report.

**CHGR-REQ-003.** A CHGR SHALL NOT be treated as, substituted for, or
conflated with a contract, a certification, or a schema.

**CHGR-REQ-004.** A CHGR SHALL NOT be treated as, substituted for, or
conflated with an advisory artifact or an AI proposal.

**CHGR-REQ-005.** A CHGR SHALL NOT be treated as, substituted for, or
conflated with a runtime observation, and SHALL create no runtime state
change of its own.

### 23.2 Definitions Requirements

**CHGR-REQ-006.** The term "Human Governance Act" SHALL be used only with
the meaning §2 defines: a bounded, attributable exercise of governance
authority by a named human, expressed as a selection among a closed option
set.

**CHGR-REQ-007.** The term "Canonical Human Governance Record" SHALL be
used only with the meaning §2 defines.

**CHGR-REQ-008.** The term "Decision Template" SHALL be used only with the
meaning §2 defines, and every Decision Template SHALL satisfy §6's
requirements.

**CHGR-REQ-009.** The term "Decision Subject" SHALL be used only with the
meaning §2 defines, and SHALL be bound to a CHGR instance at creation time.

**CHGR-REQ-010.** The term "Human Decision" SHALL be used only with the
meaning §2 defines: a substantive selection from a Decision Template's
closed option set, made by an eligible human authority.

**CHGR-REQ-011.** The term "Confirmation" SHALL be used only with the
meaning §2 and §7 define: a distinct, explicit, non-defaultable human act.

**CHGR-REQ-012.** The term "Publication" SHALL be used only with the
meaning §2 and §8 define: an atomic, system-performed act creating
immutable canonical representation.

**CHGR-REQ-013.** The term "Supersession" SHALL be used only with the
meaning §2 and §13 define.

**CHGR-REQ-014.** The term "Revocation" SHALL be used only with the
meaning §2 and §13 define: terminal, irreversible withdrawal of effect.

**CHGR-REQ-015.** The term "Suspension" SHALL be used only with the
meaning §2 and §13 define: temporary, reversible inertness.

**CHGR-REQ-016.** The term "Assurance Level" SHALL be used only with the
meaning §2 and §12 define, drawn exclusively from the L0–L5 model.

**CHGR-REQ-017.** The term "Legacy Governance Record" SHALL be used only
with the meaning §2 and §14 define.

**CHGR-REQ-018.** The term "Interactive Decision Session" SHALL be used
only with the meaning §2 and §5 define.

### 23.3 Core Invariants Requirements

**CHGR-REQ-019.** Every selection, rationale, and condition in a CHGR
SHALL be authored by the named human authority, never generated, inferred,
or completed by PCAE or any AI system.

**CHGR-REQ-020.** No PCAE component or AI system SHALL choose, default,
pre-select, infer, complete, reinterpret, broaden, narrow, negotiate, or
confirm a Human Decision on a human's behalf.

**CHGR-REQ-021.** Absence of input SHALL NEVER be interpreted as a
selection.

**CHGR-REQ-022.** No Decision Template SHALL contain an unselected default
option.

**CHGR-REQ-023.** The human-readable rendering of a CHGR's machine-readable
content SHALL be a pure, reproducible function of that content, free of
rendering-time randomness or environment-dependence.

**CHGR-REQ-024.** Every published CHGR SHALL have exactly one canonical
identifier, stable for its lifetime.

**CHGR-REQ-025.** A published CHGR's substantive fields SHALL never be
edited in place.

**CHGR-REQ-026.** Every published CHGR SHALL carry provenance evidence
sufficient to reconstruct what was presented, what was selected, and when.

**CHGR-REQ-027.** The act of recording a CHGR SHALL confer no authority by
itself.

**CHGR-REQ-028.** A CHGR SHALL affect PCAE phase lifecycle, task
lifecycle, or runtime state only where some other, separately governed
contract explicitly says so.

**CHGR-REQ-029.** No CHGR SHALL, by existing, trigger any execution,
runtime activation, or capability change.

**CHGR-REQ-030.** Any ambiguity in a CHGR's subject, authority, scope, or
state SHALL resolve to "not authoritative here" / "not applicable," never
to an assumed favorable reading.

### 23.4 Human Authorship Requirements

**CHGR-REQ-031.** Every substantive selection, rationale, and condition
recorded in a CHGR SHALL originate from the named human authority.

**CHGR-REQ-032.** PCAE tooling MAY explain a Decision Subject, assemble
authoritative context, render fixed scaffolding, format a preview, and
validate presence of required fields and a selection among a closed set.

**CHGR-REQ-033.** PCAE tooling SHALL NOT choose an option on a human's
behalf.

**CHGR-REQ-034.** PCAE tooling SHALL NOT infer a selection from partial
input, or optimize a selection toward any outcome.

**CHGR-REQ-035.** PCAE tooling SHALL NOT complete, reinterpret, broaden,
or narrow a human-authored rationale or condition field.

**CHGR-REQ-036.** PCAE tooling SHALL NOT perform Confirmation on a human's
behalf under any circumstance, including where the system judges itself
confident of the human's intent.

**CHGR-REQ-037.** A published CHGR's structure SHALL make the separation
between machine-authored and human-authored content mechanically visible
to a verifier, not merely stylistically implied.

**CHGR-REQ-038.** The content-class separation of §4 (machine scaffolding,
machine boundary language, human selection, human rationale, human
conditions, human Confirmation) SHALL be preserved unmodified from 143A
§3.3.

### 23.5 Interactive Decision Requirements

**CHGR-REQ-039.** A CHGR's substantive content SHALL be capturable through
a bounded, interactive workflow without requiring essay-writing to
complete a Human Governance Act.

**CHGR-REQ-040.** Free-form rationale SHALL remain optional in every
Decision Template unless that template's own text explicitly requires it.

**CHGR-REQ-041.** The interactive workflow SHALL present the Decision
Subject before presenting any option set.

**CHGR-REQ-042.** The interactive workflow SHALL present machine-assembled
authoritative context that is never argued or weighted by PCAE.

**CHGR-REQ-043.** The interactive workflow SHALL present an exhaustive,
mutually exclusive, closed option set with no option pre-selected.

**CHGR-REQ-044.** The interactive workflow SHALL present machine-rendered
consequence and non-effect statements drawn verbatim from the governing
Decision Template.

**CHGR-REQ-045.** The interactive workflow SHALL provide an optional,
entirely human-authored rationale field.

**CHGR-REQ-046.** The interactive workflow SHALL provide an optional,
entirely human-authored conditions/limitations field.

**CHGR-REQ-047.** The interactive workflow SHALL present an exact,
verbatim preview of the content to be published before Confirmation is
possible.

**CHGR-REQ-048.** The interactive workflow SHALL require the distinct
Confirmation act before atomic Publication occurs.

### 23.6 Decision Template Requirements

**CHGR-REQ-049.** Every Decision Template SHALL specify a stable
decision-type identifier.

**CHGR-REQ-050.** Every Decision Template SHALL specify its authoritative
basis (the governing contract clause(s)).

**CHGR-REQ-051.** Every Decision Template SHALL specify the eligible human
authority.

**CHGR-REQ-052.** Every Decision Template SHALL specify the Decision
Subject binding rule.

**CHGR-REQ-053.** Every Decision Template SHALL specify an exhaustive,
closed set of allowed choices with no open-ended "other" option.

**CHGR-REQ-054.** Every Decision Template SHALL specify which fields are
required and which are optional before Confirmation.

**CHGR-REQ-055.** Every Decision Template SHALL specify machine-rendered
consequence statements and mandatory machine-rendered non-effect
statements for each choice.

**CHGR-REQ-056.** Every Decision Template SHALL specify its confirmation
method(s), expiry rules if any, and supersession/revocation rules.

**CHGR-REQ-057.** No Decision Template SHALL embed a preferred,
recommended, or default choice, or order options to imply a preference.

**CHGR-REQ-058.** No Decision Template SHALL be authored or approved
outside a governed change process, or omit or merge an option its own
governing contract text names as distinct.

### 23.7 Confirmation Requirements

**CHGR-REQ-059.** Confirmation SHALL be a distinct act, separate from and
never implied by any earlier interactive step.

**CHGR-REQ-060.** Confirmation SHALL require the human authority to have
reviewed the exact preview content.

**CHGR-REQ-061.** Confirmation SHALL require an explicit acknowledgement
of the reviewed content.

**CHGR-REQ-062.** Confirmation SHALL require a deliberate, non-defaultable
confirming action.

**CHGR-REQ-063.** Confirmation SHALL NOT be satisfied by a session
timeout or by inactivity.

**CHGR-REQ-064.** Confirmation SHALL NOT be satisfied by pressing Enter on
a default value or by any implicit-acceptance mechanism.

**CHGR-REQ-065.** No command interface SHALL provide a flag or mode that
skips displaying the exact preview content before Confirmation.

**CHGR-REQ-066.** No command in a future CHGR command surface SHALL
silently create a `confirmed` or `published` record without the distinct
Confirmation act displaying exact content first.

### 23.8 Publication Requirements

**CHGR-REQ-067.** Publication SHALL be an atomic act, immediately
following Confirmation.

**CHGR-REQ-068.** Publication SHALL create an immutable canonical
representation of the confirmed Human Decision.

**CHGR-REQ-069.** Publication SHALL assign stable canonical identity as
part of the same atomic operation.

**CHGR-REQ-070.** Publication SHALL capture complete provenance evidence
as part of the same atomic operation.

**CHGR-REQ-071.** Publication SHALL capture complete integrity evidence as
part of the same atomic operation.

**CHGR-REQ-072.** Publication SHALL NOT, by itself, establish that the
decision-maker held the authority to make the recorded decision.

**CHGR-REQ-073.** Publication SHALL NOT, by itself, establish that the
decision is currently applicable.

**CHGR-REQ-074.** Publication SHALL NOT, by itself, authorize any later
action.

### 23.9 Canonical Identity Requirements

**CHGR-REQ-075.** Every published CHGR SHALL carry exactly one canonical
identifier, stable for the record's lifetime.

**CHGR-REQ-076.** A CHGR's canonical identifier SHALL be assigned only at
confirmed Publication.

**CHGR-REQ-077.** A CHGR's canonical identifier SHALL never be reused or
reassigned, even after revocation.

**CHGR-REQ-078.** A CHGR's canonical identifier SHALL be self-contained,
independent of file path, branch, or remote.

**CHGR-REQ-079.** A CHGR's canonical identifier SHALL never encode a
template or schema version.

**CHGR-REQ-080.** A CHGR's identity, standing alone, SHALL NOT itself
create, imply, or contribute to authority.

**CHGR-REQ-081.** A reference to a CHGR from any other artifact SHALL cite
the record's identifier.

**CHGR-REQ-082.** Where deterministic referencing is required, a reference
to a CHGR SHALL also cite the record's integrity digest.

### 23.10 Provenance Requirements

**CHGR-REQ-083.** Every published CHGR SHALL carry provenance evidence of
who provided the decision and how (confirmation method and assurance
level).

**CHGR-REQ-084.** Every published CHGR SHALL carry provenance evidence of
what options were presented and what was selected.

**CHGR-REQ-085.** Every published CHGR SHALL carry, verbatim, the exact
preview content the human actually confirmed.

**CHGR-REQ-086.** Every published CHGR SHALL carry provenance evidence of
when Confirmation occurred and what artifact was published, including its
content hash.

**CHGR-REQ-087.** Every published CHGR SHALL carry provenance evidence of
whether the published artifact changed after publication.

**CHGR-REQ-088.** Every published CHGR SHALL carry provenance evidence of
which Decision Template version and governing contract version were in
force at Confirmation time.

**CHGR-REQ-089.** Provenance and integrity evidence, alone or together,
SHALL NEVER establish that a recorded decision is currently authoritative.

### 23.11 Authority Requirements

**CHGR-REQ-090.** Authority SHALL derive solely from the valid human
governance act performed by the appropriate authority within scope.

**CHGR-REQ-091.** Authority SHALL NOT be inferred from a CHGR's storage
location or filename/identifier form.

**CHGR-REQ-092.** Authority SHALL NOT be inferred from a CHGR having been
committed to git, or from its commit or branch history.

**CHGR-REQ-093.** Authority SHALL NOT be inferred from an integrity digest
matching, or from a cryptographic signature's mere presence.

**CHGR-REQ-094.** Authority SHALL NOT be inferred from canonical
formatting, rendering, or mere repository presence.

**CHGR-REQ-095.** Authority SHALL NOT be inferred from Publication having
occurred, standing alone.

**CHGR-REQ-096.** Authority SHALL be established only by the conjunction
of valid human action and the applicable governing authority model named
by the record's own Decision Template.

**CHGR-REQ-097.** Any gap between valid human action and eligibility under
the applicable governing authority model SHALL be surfaced, never silently
resolved in the record's favor.

### 23.12 Assurance Requirements

**CHGR-REQ-098.** Every CHGR SHALL carry an explicit `assurance_level`
field drawn from the L0–L5 model.

**CHGR-REQ-099.** The L0–L5 assurance model SHALL remain an open extension
point; a future signing integration SHALL add a new level rather than
requiring redesign.

**CHGR-REQ-100.** This contract SHALL NOT require cryptographic signing of
any CHGR.

**CHGR-REQ-101.** A CHGR's validity as a record of a Human Governance Act
SHALL NOT depend on reaching any particular assurance level.

**CHGR-REQ-102.** Assurance level SHALL affect only how strongly a future
consumer may rely on identity-binding strength, never whether the decision
itself is honored.

**CHGR-REQ-103.** No representation of a CHGR SHALL claim an assurance
level higher than what actually occurred.

**CHGR-REQ-104.** The existing GPC6-REQ-075(b) election, if represented as
a CHGR, SHALL be marked assurance level L0.

**CHGR-REQ-105.** A future implementation SHALL NOT silently upgrade a
legacy record's assurance level by virtue of a more structured storage
format.

### 23.13 Record Lifecycle Requirements

**CHGR-REQ-106.** The CHGR record state model SHALL consist of exactly the
eight states: `draft`, `awaiting-human-confirmation`, `confirmed`,
`published`, `suspended`, `superseded`, `revoked`, and `invalidated`.

**CHGR-REQ-107.** Each state's entry conditions, required evidence,
permitted transitions, and prohibited transitions SHALL be as 143A §8's
table specifies, unmodified.

**CHGR-REQ-108.** Confirmation (entry to `confirmed`) and Publication
(entry to `published`) SHALL remain two distinct states, never collapsed
into one.

**CHGR-REQ-109.** A published CHGR's substantive fields SHALL never be
edited in place.

**CHGR-REQ-110.** A correction to a published CHGR SHALL be eligible only
where it provably does not change meaning.

**CHGR-REQ-111.** Any doubt whether a correction changes meaning SHALL be
treated as substantive, requiring supersession rather than correction.

**CHGR-REQ-112.** Restoration from `suspended` to `published` SHALL be
permitted only where the governing Decision Template explicitly allows it.

**CHGR-REQ-113.** Restoration from `suspended` to `published` SHALL occur
only through a new, linked governance act, never a silent timer expiry or
automatic reversal.

**CHGR-REQ-114.** Restoration from `superseded`, `revoked`, or
`invalidated` back to `published` SHALL NEVER be permitted.

**CHGR-REQ-115.** `invalidated` SHALL be reserved for structural-integrity
findings, distinct from a human's substantive change of mind.

**CHGR-REQ-116.** `revoked` SHALL be reserved for a human's substantive,
permanent withdrawal of a structurally sound record's effect.

**CHGR-REQ-117.** A structural-defect finding SHALL NOT be represented as
either a still-valid `published` record or an inapplicable `revoked`
record.

### 23.14 Legacy Import Requirements

**CHGR-REQ-118.** A Legacy Governance Record import SHALL preserve the
source document's exact original wording.

**CHGR-REQ-119.** A Legacy Governance Record import SHALL NOT rewrite,
reformat, or "clean up" the source document's content.

**CHGR-REQ-120.** A Legacy Governance Record import SHALL record the
source commit as provenance without claiming the import commit as the
decision's origin.

**CHGR-REQ-121.** A Legacy Governance Record import SHALL mark the
resulting CHGR's assurance level at the level the original act actually
achieved.

**CHGR-REQ-122.** A Legacy Governance Record import SHALL mark the
resulting CHGR `imported: true, source: legacy-markdown`.

**CHGR-REQ-123.** A Legacy Governance Record import SHALL NOT add a
signature, authenticated-identity binding, or any assurance marker absent
from the original act.

**CHGR-REQ-124.** A Legacy Governance Record import SHALL preserve the
original decision timestamp and exact confirmation wording, never a
paraphrase.

**CHGR-REQ-125.** A Legacy Governance Record import SHALL disclose,
rather than guess or silently omit, any conceptual field it cannot
populate from the source.

**CHGR-REQ-126.** A Legacy Governance Record import SHALL contain no step
that presents new options or accepts a new selection.

**CHGR-REQ-127.** A Legacy Governance Record import SHALL NOT re-run the
source decision, request re-confirmation from the original decision-maker,
or alter the source document or any other existing file.

### 23.15 Phase Separation Requirements

**CHGR-REQ-128.** Canonical Phase Reports and CHGRs SHALL remain
permanently, structurally separate artifact classes.

**CHGR-REQ-129.** A CHGR SHALL NOT be treated as a phase or advance any
phase's status.

**CHGR-REQ-130.** A CHGR SHALL NOT be regenerated, overwritten, or
otherwise touched by phase-completion machinery.

**CHGR-REQ-131.** No CHGR workflow SHALL write to
`.pcae/phase-completion-report.md`, `.pcae/phase-completion-metadata.json`,
or `.pcae/phase-reports/`.

**CHGR-REQ-132.** A phase report MAY cite a CHGR as evidence a
prerequisite decision was made, without that citation converting either
artifact into the other's class.

**CHGR-REQ-133.** A CHGR MAY cite a phase report as evidence considered,
without that citation converting either artifact into the other's class.

**CHGR-REQ-134.** No PCAE phase lifecycle SHALL advance solely because a
CHGR exists.

### 23.16 Proposal Separation Requirements

**CHGR-REQ-135.** AI or agent proposal, neutral Decision Template, human
draft, confirmed Human Decision, and published CHGR SHALL remain five
permanently distinct artifact classes.

**CHGR-REQ-136.** An AI-authored proposal SHALL NOT be stored as, indexed
as, or otherwise mistaken for a `confirmed` or `published` CHGR.

**CHGR-REQ-137.** A proposal SHALL have no path into the §13 state model.

**CHGR-REQ-138.** Silence SHALL NEVER constitute acceptance or cause a
state transition in the §13 model.

**CHGR-REQ-139.** Inactivity SHALL NEVER constitute acceptance or cause a
state transition in the §13 model.

**CHGR-REQ-140.** A timeout SHALL NEVER constitute acceptance or cause a
state transition in the §13 model.

**CHGR-REQ-141.** A default selection SHALL NEVER constitute acceptance or
cause a state transition in the §13 model.

### 23.17 Runtime Consumption Requirements

**CHGR-REQ-142.** This contract SHALL authorize no runtime implementation
consuming CHGRs.

**CHGR-REQ-143.** No runtime code path SHALL read
`.pcae/governance-records/` as of this contract's freeze.

**CHGR-REQ-144.** No command SHALL gate any other command's behavior on a
CHGR's presence as of this contract's freeze.

**CHGR-REQ-145.** A future runtime consumer of CHGRs SHALL be separately
architected and separately authorized before implementation.

**CHGR-REQ-146.** A future runtime consumer SHALL validate a CHGR's
current state and scope rather than trust its mere repository presence.

**CHGR-REQ-147.** A future runtime consumer's verification sequence SHALL
check record existence, integrity, decision-maker eligibility, current
state, expiry, and supersession before relying on a CHGR, in that order,
failing closed at any gap.

**CHGR-REQ-148.** A future runtime consumer SHALL confirm the specific
action in question actually falls within what the record's own selection
authorizes before relying on it.

**CHGR-REQ-149.** No agent SHALL treat this contract, or any future
implementation of it, as self-authorizing that agent to mint, confirm, or
publish a CHGR on a human's behalf.

### 23.18 Security Requirements

**CHGR-REQ-150.** A CHGR implementation SHALL prevent an AI system from
authoring or selecting a decision that is then represented as human-made
(mitigates §18 AI-fabrication scenarios; see also CHGR-REQ-019,
CHGR-REQ-020).

**CHGR-REQ-151.** A CHGR implementation SHALL prevent any option from
being preselected in a Decision Template or an Interactive Decision
Session (see also CHGR-REQ-021, CHGR-REQ-022, CHGR-REQ-043, CHGR-REQ-057).

**CHGR-REQ-152.** A CHGR implementation SHALL prevent coercive or
editorializing wording in a Decision Template beyond its governed,
approved text (see also CHGR-REQ-057, CHGR-REQ-058).

**CHGR-REQ-153.** A CHGR implementation SHALL prevent a silent default
from being treated as a selection (see also CHGR-REQ-021, CHGR-REQ-138
through CHGR-REQ-141).

**CHGR-REQ-154.** A CHGR implementation SHALL prevent a decision-maker
identity from being accepted as valid without eligibility verification
against the applicable governing authority model (see also CHGR-REQ-096,
CHGR-REQ-097, CHGR-REQ-154).

**CHGR-REQ-155.** A CHGR implementation SHALL prevent a superseded,
suspended, or revoked record from being relied upon as if it were
`published` (see also CHGR-REQ-107, CHGR-REQ-147).

**CHGR-REQ-156.** A CHGR implementation SHALL prevent a published record's
substantive fields from being modified after Publication without
detection (see also CHGR-REQ-025, CHGR-REQ-109, CHGR-REQ-071).

**CHGR-REQ-157.** A CHGR implementation SHALL prevent a different record's
content from being substituted under an existing canonical identifier
(see also CHGR-REQ-077, CHGR-REQ-120).

**CHGR-REQ-158.** A CHGR implementation SHALL prevent authority from being
inferred for an action outside a record's own scope (see also
CHGR-REQ-090, CHGR-REQ-148).

**CHGR-REQ-159.** A CHGR implementation SHALL prevent a stale or expired
decision from being treated as currently authoritative without an expiry
check (see also CHGR-REQ-056, CHGR-REQ-147).

**CHGR-REQ-160.** A CHGR implementation SHALL prevent a revoked record
from being reused or restored (see also CHGR-REQ-114, CHGR-REQ-116).

**CHGR-REQ-161.** A CHGR implementation SHALL prevent a Decision Template
from being altered outside a governed change process (see also
CHGR-REQ-058).

**CHGR-REQ-162.** A CHGR implementation SHALL prevent a proposal from
being confused with, or silently promoted to, a published decision, and
SHALL prevent a phase report from being confused with a human decision
(see also CHGR-REQ-002, CHGR-REQ-004, CHGR-REQ-135 through CHGR-REQ-137).

**CHGR-REQ-163.** A CHGR implementation SHALL prevent import-time
alteration of a Legacy Governance Record's meaning, and SHALL prevent an
AI-generated rationale from silently changing the meaning of a human's own
selection (see also CHGR-REQ-118, CHGR-REQ-119, CHGR-REQ-035).

### 23.19 Compatibility Requirements

**CHGR-REQ-164.** This contract SHALL NOT redefine, narrow, or supersede
any requirement of GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001.

**CHGR-REQ-165.** This contract SHALL NOT redefine, narrow, or supersede
any requirement of TAMC-001 or TAMPC-001.

**CHGR-REQ-166.** CHGRs SHALL remain lifecycle-neutral with respect to
PCAE phase lifecycle by default.

**CHGR-REQ-167.** A CHGR SHALL NOT share a write path, file, or storage
location with phase-completion metadata.

**CHGR-REQ-168.** The Typed Authority Model family (TAMC-001, TAMPC-001)
and the CHGR artifact family SHALL remain wholly separate, never composed,
subclassed, or wrapped one within the other.

**CHGR-REQ-169.** `PROJECT_STATUS.md` MAY narratively summarize a
published CHGR, but SHALL NEVER be treated as its canonical store.

**CHGR-REQ-170.** This contract's own compatibility conclusions SHALL be
independently re-derivable from TAMC-001's and TAMPC-001's own frozen
text, not merely assumed from Phase 143A's architectural summary.

**CHGR-REQ-171.** No `docs/contracts/**` file other than this contract's
own new document SHALL be modified by the phase that freezes this
contract.

### 23.20 Governance Responsibility Requirements

**CHGR-REQ-172.** This contract SHALL introduce no new role, responsibility,
or authority beyond GPC6-REQ-040's existing table.

**CHGR-REQ-173.** Decision Template authorship and approval responsibility
SHALL be assigned exactly as §20's table states, with no overlap between
the authoring and approving role.

**CHGR-REQ-174.** Interactive presentation responsibility SHALL belong to
PCAE tooling, strictly bounded per §4.

**CHGR-REQ-175.** Human selection and Confirmation responsibility SHALL
belong exclusively to the eligible Human Authority the governing template
names.

**CHGR-REQ-176.** Publication responsibility SHALL belong to the system,
performing no discretionary act.

**CHGR-REQ-177.** Verification responsibility SHALL belong to the
Independent Contract Verifier or Independent Implementation Verifier,
depending on what is being verified.

**CHGR-REQ-178.** Supersession, suspension, and revocation responsibility
SHALL belong only to a human authority eligible under the record's own
Decision Template.

**CHGR-REQ-179.** Runtime-consumption ownership SHALL remain unassigned
by this contract, named explicitly as an open question for a future,
separately governed phase.

### 23.21 Audit Requirements

**CHGR-REQ-180.** A verifier SHALL be able to determine what decision was
made, verbatim, from a CHGR alone.

**CHGR-REQ-181.** A verifier SHALL be able to determine who made the
decision, from a CHGR alone.

**CHGR-REQ-182.** A verifier SHALL be able to determine under what
authority the decision was made, from a CHGR alone.

**CHGR-REQ-183.** A verifier SHALL be able to determine which Decision
Template and version governed the decision, from a CHGR alone.

**CHGR-REQ-184.** A verifier SHALL be able to determine what evidence was
considered, from a CHGR alone.

**CHGR-REQ-185.** A verifier SHALL be able to determine any conditions or
limitations attached to the decision, from a CHGR alone.

**CHGR-REQ-186.** A verifier SHALL be able to determine the decision's
assurance level, from a CHGR alone.

**CHGR-REQ-187.** A verifier SHALL be able to determine whether a CHGR
remains current, superseded, suspended, or revoked, from the record's own
state field, checked rather than assumed.

**CHGR-REQ-188.** Any artifact relying on a CHGR SHALL itself cite that
CHGR's identifier, so a reverse index can be built by scanning citations
rather than requiring the record to track its own dependents.

### 23.22 Amendment Requirements

**CHGR-REQ-189.** CHGR-001 MAY evolve only through governed superseding
contracts.

**CHGR-REQ-190.** A superseding contract SHALL identify its predecessor,
version, changed requirements, migration effect, and backward-compatibility
impact.

**CHGR-REQ-191.** A published Human Governance Record's substantive
meaning SHALL NEVER change through an amendment to CHGR-001.

**CHGR-REQ-192.** No governed superseding contract SHALL retroactively
reinterpret an already-published record's content.

**CHGR-REQ-193.** Backward compatibility with CHGR-001 v1.0 SHALL be
mandatory for any future revision unless that revision explicitly states
its compatibility impact and supersedes a named requirement.

---

## 24. Adversarial Validation

Each scenario below attempts to invalidate this contract. Every scenario
is mitigated by at least one existing `CHGR-REQ-###`; none required a gap
to be left open in the final text, because each gap discovered during this
pass was closed by adding the corresponding requirement to §23 before this
document was finalized.

| # | Scenario | Mitigating requirement(s) |
|---|---|---|
| V1 | An AI selects "Proceed" on a human's behalf | CHGR-REQ-019, CHGR-REQ-020, CHGR-REQ-033, CHGR-REQ-150 |
| V2 | An option is accepted by default acceptance (no explicit choice) | CHGR-REQ-021, CHGR-REQ-022, CHGR-REQ-043, CHGR-REQ-153 |
| V3 | A Decision Template is authored with biased or coercive wording | CHGR-REQ-057, CHGR-REQ-058, CHGR-REQ-152 |
| V4 | An old, already-relied-upon CHGR is replayed as if newly authoritative | CHGR-REQ-147, CHGR-REQ-155, CHGR-REQ-159 |
| V5 | A revoked or expired CHGR's authority is reused | CHGR-REQ-114, CHGR-REQ-116, CHGR-REQ-159, CHGR-REQ-160 |
| V6 | A decision-maker identity is forged or unverifiable | CHGR-REQ-090, CHGR-REQ-096, CHGR-REQ-097, CHGR-REQ-154 |
| V7 | A CHGR's Markdown rendering is treated as authoritative merely because it exists and reads well | CHGR-REQ-023, CHGR-REQ-080, CHGR-REQ-094 |
| V8 | A CHGR's mere presence in the repository is treated as authority | CHGR-REQ-080, CHGR-REQ-091, CHGR-REQ-092, CHGR-REQ-094, CHGR-REQ-095 |
| V9 | A published record is edited in place after Publication | CHGR-REQ-025, CHGR-REQ-071, CHGR-REQ-109, CHGR-REQ-110, CHGR-REQ-111, CHGR-REQ-156 |
| V10 | A CHGR is mistaken for a phase, or a phase report is mistaken for a human decision | CHGR-REQ-002, CHGR-REQ-128 through CHGR-REQ-134, CHGR-REQ-162 |
| V11 | A Legacy Governance Record import silently drifts from the source's original meaning | CHGR-REQ-118, CHGR-REQ-119, CHGR-REQ-124, CHGR-REQ-125, CHGR-REQ-126, CHGR-REQ-163 |
| V12 | An AI-generated rationale is inserted or edited in a way that changes the apparent meaning of the human's own selection | CHGR-REQ-035, CHGR-REQ-038, CHGR-REQ-163 |
| V13 | An AI system performs Confirmation on a human's behalf, believing it has enough context to do so safely | CHGR-REQ-036, CHGR-REQ-059 through CHGR-REQ-066, CHGR-REQ-149 |

No scenario above required inventing a new mitigation outside the §23
requirement set; each citation above resolves to a requirement already
present in §23.1–§23.22.

---

## 25. Success Criteria

CHGR-001 is contractually demonstrated successful, without requiring any
implementation, when a future implementing phase can show:

1. Human choices can be made interactively, without hand-authored prose
   required, per §5 and CHGR-REQ-039 through CHGR-REQ-048.
2. Free-form rationale and conditions are optional in every Decision
   Template unless that template's own text requires them, per
   CHGR-REQ-040.
3. Explicit Confirmation is required before Publication, and no default,
   timeout, or silence can substitute for it, per §7, §16.2, CHGR-REQ-059
   through CHGR-REQ-066, CHGR-REQ-138 through CHGR-REQ-141.
4. Publication is atomic and immutable, and correction is possible only
   for non-substantive rendering or metadata defects, per §8, §13.3,
   CHGR-REQ-067 through CHGR-REQ-074, CHGR-REQ-109 through CHGR-REQ-111.
5. Authority and provenance remain conceptually and evidentially separate
   from mere record existence, per §10, §11, CHGR-REQ-089 through
   CHGR-REQ-097.
6. CHGRs remain structurally and operationally separate from phase
   reports, with no shared write path or file, per §15, CHGR-REQ-128
   through CHGR-REQ-134.
7. A published CHGR can be deterministically referenced by identifier and
   integrity digest, per §9, CHGR-REQ-075 through CHGR-REQ-082.
8. The existing GPC6-REQ-075(b) election can be imported without
   repeating the human decision and without semantic drift, per §14,
   CHGR-REQ-118 through CHGR-REQ-127.
9. Runtime remains conceptually and operationally neutral with respect to
   CHGRs until a separate, explicit runtime-consumption phase says
   otherwise, per §17, CHGR-REQ-142 through CHGR-REQ-149.
10. Every adversarial scenario in §24 remains mitigated by a citable
    requirement, not by narrative assurance alone.

---

## Non-Goals

This contract does not authorize, perform, or imply any of the following:

- **Schema freeze.** No executable schema for a CHGR's machine-readable
  representation is frozen by this contract; §5.1's "Conceptual Fields"
  table from 143A remains conceptual, non-binding guidance for a future
  Implementation-stage phase.
- **CLI implementation.** No command, flag, or exit-code contract is
  created or implemented.
- **Storage implementation.** No file, directory, or persistence mechanism
  under `.pcae/governance-records/` or elsewhere is created.
- **Signing implementation.** No cryptographic signing mechanism is
  implemented; §12's L2–L5 assurance levels remain descriptive only.
- **Identity-provider integration.** No external identity-provider
  integration is implemented or authorized.
- **Runtime enforcement.** No runtime code path is added that reads,
  gates on, or enforces anything against a CHGR; §17 describes a future
  relationship only.
- **Migration of the existing election.** `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`
  is not imported, rewrapped, or modified by this contract; §14 freezes
  only the discipline a future import phase must follow.
- **Any Stage 3/pilot authorization.** This contract does not advance,
  authorize, or evaluate `GLP-PILOT-C6` or any other GLP-designated
  initiative; it does not perform or presume the GPC6-REQ-075(b) election,
  and it does not perform, authorize, or imply any GAC-001 §9 Stage 6
  governance decision.
- **New human governance decision.** This contract's own freeze is not
  itself a Human Governance Act and creates no new one.

---

## 26. Phase 146B contract revision — schema-envelope/canonical-identity construction

**Version:** 1.1
**Predecessor:** CHGR-001 v1.0 (Phase 143B)
**Revised by:** Phase 146B — CHGR-001 Schema-Envelope Contract Freeze

### 26.1 Reason

Phase 144G independently found, and Phase 146A independently re-confirmed
from direct inspection of `src/pcae/governance/publication/record.py`,
that the `human_governance_record` sub-object `build_publication_record`
constructs is missing 14 of the 19 fields
`human_governance_record.schema.json`'s own `required` array names. This
is disclosed, not hidden — `record.py`'s own `_KNOWN_LIMITATIONS` names it
explicitly — but it means the Publication Coordinator's output, while
CHGR-001 §10-content-complete (PEC-REQ-112), is not yet the schema-
conformant artifact §9 describes as a whole. Phase 146A's architecture
(§4.5) identified four areas a Contract Freeze phase must resolve before
an implementation phase can close this gap: top-level envelope fields,
sub-structure identity, the `authority_basis_claimed`/`assurance_level`
disposition, and the conformance-verification mechanism. This section
resolves all four as binding, versioned, additive contract text, per §22's
Amendment Contract discipline and mirroring PEC-001 §20's identical
precedent for widening the Coordinator's own input handling without
narrowing any existing provision.

This section is grounded in direct, independent re-reading of
`src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`,
its three sibling schemas (`human_confirmation_evidence`,
`governance_record_provenance`, `governance_record_integrity`), the four
files' shared `$defs` (`envelope.schema.json`, `identity.schema.json`,
`digest.schema.json`, `enums.schema.json`, `references.schema.json`,
`limitations.schema.json`), `src/pcae/schema_resources/chgr/manifest.json`,
and the current implementation
(`src/pcae/governance/publication/record.py`,
`src/pcae/governance/publication/coordinator.py`,
`src/pcae/interactive_workflow/publication_handoff/handoff.py`,
`src/pcae/interactive_workflow/models/session.py`) — not merely from Phase
146A's own architectural summary of them, per the same "evidence of
architectural intent, never contractual authority" discipline this
contract's own preamble already applies to Phase 143A.

### 26.2 Changed requirements

**CHGR-REQ-194.** `schema_id` and `schema_version`, on every one of the
four artifacts this section names, SHALL be taken verbatim from
`src/pcae/schema_resources/chgr/manifest.json`'s entry for the applicable
`record_family`, never hardcoded independently elsewhere and never
invented at construction time. `contract_version` SHALL remain the literal
string `"CHGR-001/1.0"` on every artifact, unchanged by this revision (see
§26.3(c) below for why this string is not bumped to reflect v1.1).

**CHGR-REQ-195.** A schema-conformant `human_governance_record` SHALL be
accompanied by exactly three sibling artifacts — `human_confirmation_evidence`,
`governance_record_provenance`, and `governance_record_integrity` — each
independently identified and independently schema-validated, each carrying
its own complete envelope (`schema_id`, `schema_version`,
`contract_version`, `record_type`, `record_id`, `record_digest`,
`created_at`). None of the three SHALL share the top-level record's own
`record_id` or `record_digest` (resolves 146A §4.5(2); reasoning at
§26.3(a) below).

**CHGR-REQ-196.** Each of the four artifacts' `record_id` SHALL follow the
family-specific prefix convention `identity.schema.json` already documents
(`chgr-`, `chgrconf-`, `chgrprov-`, `chgrintg-`, each followed by a
32-hex-digit UUID4), assigned only during the same atomic Publication
operation that assigns the top-level record's own identity (restates
CHGR-REQ-076 for all four artifacts, never pre-assigned, never reused).

**CHGR-REQ-197.** Each of the four artifacts' `record_digest` SHALL be a
bare, lowercase, 64-character hexadecimal SHA-256 digest computed over
that artifact's own canonical JSON payload (object keys sorted
lexicographically; `,`/`:` separators with no surrounding whitespace;
UTF-8 encoding), with the `record_digest` field itself excluded from the
hashed payload — the exact algorithm `compute_record_digest`
(`src/pcae/governance/publication/record.py`) already implements for
today's pre-conformance record, extended unchanged to all four artifacts.
Each artifact's digest is computed independently over its own payload
only; no artifact's digest hashes a sibling's payload bytes directly — a
sibling relationship is expressed only through an explicit reference field
citing the sibling's own already-computed `record_id`/`record_digest`
(restates CHGR-REQ-082).

**CHGR-REQ-198.** `human_governance_record.lifecycle_state` SHALL be
assigned the literal value `"published"` at construction, unconditionally.
No other value of the eight-state model (§13.1) SHALL ever be assigned by
this construction path, because the Package the Coordinator receives
already reflects an already-Confirmed session (Confirmation occurred
inside `interactive_workflow` before the Package ever reaches the
Coordinator), and `PublicationCoordinator.execute()` performs exactly the
Confirmation→Publication transition atomically, with no other
lifecycle-state-assigning capability implemented anywhere in this
repository. Assigning this value is a statement about the record's own
state, never an authority determination (restates CHGR-001 §11 per 146A
§4.4's identical caution).

**CHGR-REQ-199.** `authority_basis_claimed` remains correctly and
permanently absent — never fabricated — for as long as no Decision
Template `eligible_authority` citation exists anywhere in this repository
to construct it from (restates PEC-REQ-115 unchanged, one layer later).
Its absence SHALL be named in the record's own `limitations` array, never
silently omitted without disclosure.

**CHGR-REQ-200.** `assurance_level` SHALL be derived deterministically and
exclusively from the Package's own `decision_maker_identity_evidence.evidence_kind`
field (already populated, verbatim, by `PublicationHandoff.build_package`):
`"typed_confirmation_only"` maps to `L0`; `"os_authenticated_user"` maps to
`L1`. No value higher than `L1` SHALL ever be assigned by this
construction path, because no evidence shape supporting `L2`–`L5` exists
anywhere in this repository (restates the shared schema's own
ASSURANCE_OVERCLAIM discipline, CHGR-REQ-103). This derivation requires no
`eligible_authority` citation and therefore does not depend on, or expand,
the IWPC-001 §31 C-1 deferral (reasoning at §26.3(b) below).

**CHGR-REQ-201.** The `human_confirmation_evidence` sibling artifact
SHALL populate `confirmed_content_digest`/`preview_rendering_digest` from
the Package's own `preview_digest` (verbatim), `confirmation_statement`/
`confirmation_timestamp` from the Package's own verbatim fields,
`confirmer_identity_evidence` from the Package's own
`decision_maker_identity_evidence` (verbatim), and `achieved_assurance_level`
per CHGR-REQ-200.

**CHGR-REQ-202.** The `governance_record_provenance` sibling artifact
SHALL populate `template_used_ref`, `options_presented`,
`selected_option_id`, `rationale_given`, and `preview_content_digest` from
the Package's own verbatim fields; `confirmation_event_ref` as an
artifact reference citing the `human_confirmation_evidence` sibling's own
`record_id`/`record_digest`; and `repository_provenance` with
`available: false`, for as long as this construction path remains a pure
function of `(package, event, record_id, created_at)` with no repository
or git read (restates PEC-REQ-113's pure-function/placement discipline). A
`false` value here is a disclosed limitation, never a defect, and SHALL be
named in the record's own `limitations` array.

**CHGR-REQ-203.** The `governance_record_integrity` sibling artifact
SHALL populate `payload_digest` with the top-level `human_governance_record`'s
own `record_digest` value, `rendering_digest` with a digest of that
record's deterministic human-readable rendering (§3 invariant 4; the
rendering function's own construction is left to the implementation phase
this section authorizes no part of), and `digest_algorithm` with the
literal string `"sha256"`.

**CHGR-REQ-204.** Conformance verification SHALL be fail-closed: a
Publication attempt whose constructed four-artifact set does not validate
against `human_governance_record.schema.json` and its three sibling
schemas SHALL be refused before the atomic write occurs, creating no CHGR
of any kind (restates PEC-REQ-052/PEC-REQ-075's "no CHGR created on any
failure"), consistent with `docs/ROADMAP.md`'s "Fail closed" principle and
146A §4.5(4)'s own default recommendation.

**CHGR-REQ-205.** The conformance-verification check SHALL run as part
of, or immediately following, the same construction step that builds the
four artifacts, before any store write occurs — never deferred to a
separate, optional, post-hoc check as the sole gate. A separate check MAY
additionally exist for external-audit convenience, but SHALL NOT be relied
upon as the only enforcement point.

**CHGR-REQ-206.** No requirement in §1–§25 (CHGR-REQ-001 through
CHGR-REQ-193) is narrowed, superseded, or reworded by this revision.
CHGR-REQ-194 through CHGR-REQ-205 are additive; §25's Success Criteria and
§24's Adversarial Validation table remain fully satisfied by an
implementation that additionally satisfies CHGR-REQ-194–206.

### 26.3 Judgment calls

**(a) Sub-structure identity — resolving 146A §4.5(2).** 146A's own
architecture left open whether the three named sub-structures need
independent identity or may rely on the top-level record's single
identity when always published together. This section resolves the
question in favor of independent identity, because the schema layer
Phase 143E already froze (`human_confirmation_evidence.schema.json`,
`governance_record_provenance.schema.json`,
`governance_record_integrity.schema.json`) already requires each to carry
its own complete envelope, including its own `record_id` and
`record_digest`, as a condition of schema validity — this is a structural
fact about an already-frozen schema, not a new design choice this
contract invents. Treating the three as identity-sharing with the
top-level record would require either contradicting the already-frozen
schemas (out of scope; §3.5 of 146A) or leaving the "always published
together" assumption undocumented and untested. Independent identity is
therefore adopted as the only reading compatible with the schema family
as it already exists.

**(b) `assurance_level` split from `authority_basis_claimed` — a
disclosed, reasoned narrowing of 146A §3.2(2)'s grouping.** Phase 146A's
architecture grouped `authority_basis_claimed` and `assurance_level`
together as a single deferred sub-problem, reasoning that both require an
`eligible_authority` citation from a Decision Template model that does not
exist. Independent re-reading of CHGR-001 §12 (this contract's own
Assurance Contract — "assurance level affects only how strongly a future
consumer may rely on identity-binding strength, never whether the
decision itself is honored") and of
`src/pcae/schema_resources/chgr/shared/identity.schema.json`'s
`decision_maker_identity_evidence.evidence_kind` enum (`L0`:
`typed_confirmation_only`; `L1`: `os_authenticated_user` — already the
exact two values `src/pcae/interactive_workflow/models/session.py`'s
`Session.decision_maker_evidence_kind` field restricts itself to, and
already carried verbatim into
`PublicationReadinessPackage.decision_maker_identity_evidence` by
`PublicationHandoff.build_package`) shows that `assurance_level` is, in
fact, mechanically derivable today from evidence already flowing through
the existing Package, with no `eligible_authority` citation of any kind
involved. `authority_basis_claimed` genuinely does require that citation
and remains deferred (CHGR-REQ-199); `assurance_level` does not, and this
section accordingly gives it its own, non-deferred construction rule
(CHGR-REQ-200). This is a considered, disclosed narrowing of 146A's own
grouping — not a silent reinterpretation — made because direct
re-derivation from primary contract and schema text, rather than restating
146A's own architectural summary, found the two fields' actual dependency
graphs are not identical. It does not touch, expand, or resolve the
IWPC-001 §31 C-1 deferral in any way: `authority_basis_claimed` remains
exactly as deferred as 146A found it.

**(c) `contract_version` left at `"CHGR-001/1.0"`, not bumped to `1.1`.**
`human_governance_record.schema.json` and its three siblings each fix
`contract_version` as the JSON Schema const `"CHGR-001/1.0"`. This
revision does not redefine that schema (out of scope; 146A §3.4), and the
const identifies which version of CHGR-001 the *schema files themselves*
were generated against (Phase 143E), not which version of CHGR-001 text is
currently in force. Since this revision is additive-only (CHGR-REQ-206)
and does not require the schema family to change, an artifact correctly
tagged `"CHGR-001/1.0"` remains fully accurate: it was built to satisfy a
contract whose text has since gained CHGR-REQ-194–206 without any of
CHGR-REQ-001–193 changing underneath it. A future schema regeneration that
bumps this const is a distinct, not-yet-authorized undertaking.

### 26.4 Regression review

Independently reconfirmed unchanged: the Purpose statement (§1),
Definitions (§2), Core Invariants (§3), the Human Authorship Contract
(§4), the Interactive Decision Contract (§5), the Decision Template
Contract (§6), the Confirmation Contract (§7), the Publication Contract
(§8, including atomicity — this revision changes only which fields the
same already-atomic write carries, never the ordering, atomicity, or
determinism discipline itself), the Canonical Identity Contract (§9,
CHGR-REQ-075–082 restated unweakened and extended to three additional
artifacts by CHGR-REQ-195–196), the Provenance Contract (§10, restated and
concretized, never narrowed, by CHGR-REQ-201–202), the Authority Contract
(§11, restated unweakened by CHGR-REQ-198's explicit non-authority
caution), the Assurance Contract (§12, restated and given its first
concrete derivation rule by CHGR-REQ-200, without redefining the six-level
model itself), the Record Lifecycle Contract (§13, the eight-state model
and Confirmation/Publication distinctness both unmodified — CHGR-REQ-198
assigns a value from the existing enum, it does not add, remove, or
reorder a state), the Legacy Import Contract (§14), the Phase Separation
Contract (§15), the Proposal Separation Contract (§16), the Runtime
Consumption Contract (§17, unaffected — no runtime code path is added or
authorized by this revision), the Security Contract (§18, strengthened in
actual verifiable coverage by CHGR-REQ-204's fail-closed conformance gate,
never weakened), the Compatibility Contract (§19, including §19.1's Typed
Authority Model separation, unaffected), the Governance Responsibility
Contract (§20, no row reassigned — Publication remains the System's
atomic, non-discretionary act per §20's own table, unaffected by which
fields that atomic act now populates), the Audit Contract (§21), and the
Amendment Contract (§22, this section is itself a correct instance of the
discipline it describes).

### 26.5 Compatibility review

Independently confirmed compatible with: PEC-001 v1.1 (unmodified by this
revision; PEC-REQ-054's existing "provenance/integrity capture ... in the
same atomic operation" obligation is what this section's construction
rules describe how to satisfy in full, exactly as PEC-001 §20 already did
for CHGR-001 §10's substantive-content half); IWC-001 v1.2 and IWPC-001
v1.4 (unmodified; no field this section names originates anywhere outside
the Package IWC-001 v1.2/PEC-REQ-111 already widened, and the C-1 deferral
IWPC-001 §31 states is re-cited, not re-litigated, at CHGR-REQ-199 and
§26.3(b)); TAMC-001/TAMPC-001 (unmodified, independently reconfirmed
structurally disjoint per §19.1, unaffected by this revision's purely
CHGR-internal scope); and `human_governance_record.schema.json` and its
three sibling schemas together with `manifest.json` (unmodified — this
revision specifies how to construct artifacts that already satisfy these
already-frozen schemas, never proposing a schema change of its own).

### 26.6 Migration strategy

The Phase 144C implementation
(`src/pcae/governance/publication/record.py`,
`src/pcae/governance/publication/coordinator.py`) is unmodified by this
revision (Forbidden Files for this phase); it remains exactly as Phase
146A found it: PEC-001/CHGR-001-§10-content-complete, schema-envelope-
incomplete (14 of 19 top-level fields missing, zero sibling artifacts
constructed). Migrating that implementation to satisfy
CHGR-REQ-194–CHGR-206 requires, in a future, separately governed
implementation phase (146E or equivalent, not authorized here):

1. Widening `build_publication_record` (or a successor function) to
   additionally construct the three sibling artifacts and the ten missing
   top-level fields this section names, from the Package's own
   already-verbatim content plus the newly-assigned `record_id`s/digests
   this section specifies — no new import of `interactive_workflow`
   internals beyond what `record.py` already imports (144G's
   forbidden-import boundary, restated unweakened by this section).
2. Introducing the fail-closed schema-validation gate CHGR-REQ-204/205
   specify, inside the construction step, before
   `PublicationCoordinator._store.write_record` is ever called.
3. Adding a deterministic human-readable rendering function for
   `rendering_digest` (CHGR-REQ-203), if one does not already exist for
   this record shape.

No CLI, storage-format, or runtime change is required by any of the three
steps; all are pure-function content and validation changes to an
already-existing, already-atomic write path. Until that future phase runs,
no CHGR produced by `PublicationCoordinator` validates against
`human_governance_record.schema.json`, exactly as Phase 146A found.

### 26.7 Backward-compatibility impact

None beyond the additive widening itself. Every CHGR-REQ-001–193
requirement remains textually and positionally unchanged. A hypothetical
future implementation satisfying only CHGR-REQ-001–193 (the pre-revision
text) without also satisfying CHGR-REQ-194–206 would remain
CHGR-001-v1.0-literal-compliant but would not close the schema-conformance
gap — exactly today's status, unaffected by this revision.
`src/pcae/governance/publication/**`, `src/pcae/interactive_workflow/**`,
and every file under `src/pcae/schema_resources/chgr/**` are unmodified by
this revision (verified: zero files under any of these paths appear in
this phase's diff). Runtime remains `Observed` / `observe` /
`unavailable`, unchanged before and after this revision.

## 27. Post-revision next phase

The expected next phase is **146C — Contract Independent Verification**,
which independently re-derives CHGR-REQ-194–206 from this contract's own
frozen text and the schema/implementation files cited above, without
trusting this section's own self-report, checking for ambiguity, internal
consistency, and conflict with every already-frozen invariant this §26.4
regression review names — mirroring Phase 137I's role for TAMPC-001. This
is a recommendation, consistent with 146A §5's own sequence and §9's own
"a recommendation, not an authorization" discipline; it does not itself
authorize Phase 146C.
