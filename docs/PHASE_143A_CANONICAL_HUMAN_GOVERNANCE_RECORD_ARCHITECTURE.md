# Phase 143A — Canonical Human Governance Record Architecture

**Status:** Complete (architecture-stage design document only; no schema
frozen, no CLI implemented, no storage created, no signing implemented, no
runtime enforcement introduced, no authority-resolution behavior changed)
**Mode:** A dedicated Architecture-stage design (GLP-001 §6.1 Stage 1
pattern) applied to a new, repository-wide artifact class — **Canonical
Human Governance Records** — not a GLP-designated pilot, not a redesign of
any existing pilot track, and not itself a decision, election, or
authorization act.
**Governing authority:** GLP-001 v1.0, GAC-001 v1.0, PGP-001 v1.1, PPA-001
v1.0, AGOC-001 v1.0, GPC6-001 v1.0, GPC6R-001 v1.0, GPC6C-001 v1.0,
GPC6-REQ-040 (responsibility ownership), GPC6-REQ-075(b) (human-authority
reservation), Phase 142I certification evidence, the completed
`docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` election record,
`PROJECT_STATUS.md`, existing canonical-artifact/provenance/lifecycle/
trust-gate/typed-authority architecture (Phases 114A, 134E.1, Track 136).
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Deliverable:** This design document only. No contract was numbered, no
schema file, CLI command, storage path, or signing mechanism was created or
modified. No file under `src/pcae/` was touched by this phase.

---

## 0. Framing and Relationship to Prior State

Phase 142I formally certified `GLP-PILOT-C6` Stage 3 Readiness. The only
subsequent act was the human-authority election required by
GPC6-REQ-075(b), performed by Atila Madai as a **plain, non-PCAE, human-only
governance act** and recorded in `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`
(commit `4e24e66d`, 2026-07-23). `PROJECT_STATUS.md` records that election
under "GPC6-REQ-075(b) Human-Authority Election Recorded" and states
explicitly that the record "is a plain human governance artifact, not a
PCAE phase — it was not generated, inferred, simulated, or made on the
human authority's behalf by PCAE or any AI system."

That election record is the first real-world instance of a class of
artifact this repository has never architecturally defined: a durable,
canonical record of a **substantive decision made by a human**, distinct
from the phase-completion narrative PCAE itself authors. Today that class
exists only as freeform Markdown, hand-authored, with no schema, no
identity namespace, no state model, no storage boundary, and no
machine-verifiable provenance beyond git history.

This phase's sole activity is to **architect** that artifact class — a
**Canonical Human Governance Record (CHGR)** — so that GPC6-REQ-075(b)'s
election, and future acts like it (approvals, revocations, exceptions,
refusals, deferrals), can eventually be captured, referenced, and verified
with the same discipline PCAE already applies to phase reports, without
ever letting PCAE originate, infer, or broaden the decision itself.

This phase does **not** re-open, restate, reinterpret, or migrate the
existing election. §14 below designs how a future phase could import it;
this phase performs no import. Per this repository's standing rule, the
phase prompt is authoritative over scope; `PROJECT_STATUS.md`'s "recommended
next phase: none" statement refers to the GLP-PILOT-C6 pilot lifecycle
specifically (Stage 3 entry, GAC-001 §9), not to architecture work on
PCAE's own governance-record tooling, which is orthogonal to pilot
advancement and introduces no lifecycle, authority, or runtime change.

---

## 1. Purpose and Scope

### 1.1 Purpose

A **Canonical Human Governance Record (CHGR)** is the durable, canonical
representation of a single bounded act of human governance authority,
captured with enough structure to be identified, referenced, verified, and
reasoned about by later governed activity — without PCAE ever selecting,
inferring, or broadening what was decided.

CHGRs exist to solve a specific, already-demonstrated problem: this
repository's only precedent for such a decision
(`docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`) is freeform prose. It is
faithful and complete, but it has no canonical identity, no queryable
state, no structural distinction between machine-presented scaffolding and
human-selected substance, and no way for a future phase to verify — other
than by reading English — that it remains current, unsuperseded, and
unrevoked.

### 1.2 In-Scope Human Acts

The architecture shall support recording (not making) bounded human acts
including:

| Act | Example |
|---|---|
| Authority election | GPC6-REQ-075(b) |
| Governance approval | GAC-001 §9 Stage 6 "Adopt" decision |
| Authorization decision | permitting a specific governed activity to proceed |
| Risk acceptance | accepting a disclosed Observation without repair |
| Exception approval | one-time deviation from a contract requirement |
| Suspension | temporarily halting reliance on a prior record |
| Revocation | permanently withdrawing a prior record's effect |
| Emergency override | GAC-001 §10-class rollback authorization |
| Scope limitation | narrowing an election's applicability |
| Explicit refusal | "Reject," per GAC-REQ-042(e) |
| Deferral | "Continue pilot" / "defer pending more evidence" |
| Interpretation decision | GAC-001 §9 applicability determination, as GPC6-REQ-075(b)'s own record already performed |

All of these share the structural shape GPC6-REQ-075(b)'s record already
exhibits: a named decision-maker, a bounded option set, a selection, an
optional rationale, and explicit non-effect statements.

### 1.3 Out-of-Scope (Remains Outside PCAE)

- The human's *reasoning process* prior to selection — PCAE never observes,
  models, or infers deliberation.
- Any act that is not attributable to a specific named human authority
  (anonymous, aggregate, or crowd input is out of scope).
- Any act whose validity depends on real-world legal, contractual, or
  organizational authority outside this repository (this architecture
  records that a decision was made and by whom; it never adjudicates
  whether that person actually held the authority they claimed — see §9).
- Any act that is itself the *output* of an AI/agent process (an AI
  proposal is not a governance act until a human confirms it — see §16).
- Ordinary phase-completion narrative — already served by canonical phase
  reports (§15).

---

## 2. Core Invariants

These invariants are architectural constraints, not implementation
choices. Any future contract, schema, or implementation phase (143B+) must
satisfy all of them; none may be waived by convenience.

| # | Invariant | Statement |
|---|---|---|
| INV-1 | Human authorship of substantive decisions | Every decision selection, rationale, and condition in a CHGR is authored by the named human, never generated, inferred, or completed by PCAE or any AI system. |
| INV-2 | No AI selection or inference | No PCAE component may choose, default, pre-select, or infer a decision option on a human's behalf. |
| INV-3 | No silent default selection | Absence of input is never interpreted as a selection. There is no such thing as an "unselected default option" in a CHGR template (§4). |
| INV-4 | Explicit human confirmation | Publication requires a distinct, explicit confirmation act (§10) that is never implied by earlier steps. |
| INV-5 | Exact preservation of selected meaning | Once confirmed, the record's substantive content (selections, rationale, conditions) is never altered in a way that changes its meaning (§11). |
| INV-6 | Canonical identity | Every published CHGR has exactly one canonical identifier, stable for its lifetime (§6). |
| INV-7 | Provenance completeness | Every published CHGR carries enough evidence to reconstruct what was presented, what was selected, and when (§12). |
| INV-8 | Deterministic rendering | The human-readable rendering of a CHGR's machine-readable content is a pure, reproducible function of that content — no rendering-time randomness or environment-dependence. |
| INV-9 | Immutable publication | A published CHGR's substantive fields are never edited in place (§11). |
| INV-10 | Amendment only through supersession or revocation | Substantive change requires a new, linked CHGR (§11). |
| INV-11 | Authority neutrality during recording | The act of recording a CHGR confers no authority; a CHGR is evidence that a decision was made, not proof that the decision-maker held the authority to make it (§9). |
| INV-12 | Lifecycle neutrality unless separately governed | A CHGR affects PCAE phase lifecycle, task lifecycle, or runtime state only if some other, separately governed contract explicitly says so (§17). By default, recording a CHGR changes nothing else. |
| INV-13 | No automatic execution | No CHGR, by existing, triggers any execution, runtime activation, or capability change (§17). |
| INV-14 | Fail-closed ambiguity handling | Any ambiguity in subject, authority, scope, or state resolves to "not authoritative here" / "not applicable," never to an assumed favorable reading (§9, §18). |
| INV-15 | Separation from phase lifecycle | A CHGR is never a phase, never advances phase state, and is never regenerated or overwritten by phase-completion machinery (§15). |
| INV-16 | Separation between proposal and decision | An AI-authored proposal is a distinct artifact class from a human decision; a proposal can never itself become a decision through storage, indexing, or reference alone (§16). |
| INV-17 | Separation between recording and enforcement | Recording a CHGR is distinct from, and does not itself perform, any runtime check that consumes it (§17). |

---

## 3. Interactive Human Decision Architecture

### 3.1 Goal

The existing election record required the human to compose full prose by
hand. That is faithful but not required by GPC6-REQ-075(b), and it does
not scale to routine governance acts (exceptions, suspensions). The
architecture instead defines an **interactive, bounded-choice workflow**
so essay-writing is optional, while preserving every invariant in §2.

### 3.2 Workflow Stages

1. **Presentation of the decision subject** — machine-generated, neutral:
   what artifact, contract, or election this record concerns (e.g., "GAC-001
   §9 Stage 6 governance decision for GLP-PILOT-C6").
2. **Presentation of authoritative context** — machine-assembled citations
   to governing contracts and prior evidence (mirrors §"Evidence
   Considered" in the existing election), never argued or weighted by
   PCAE.
3. **Bounded selectable options** — an exhaustive, mutually exclusive set
   drawn from the governing template (§4), with **no option pre-selected**
   (INV-3).
4. **Explanation of consequences and non-effects** — machine-generated
   boundary language stating what each option does and, critically, does
   *not* do (mirrors "This election does not itself begin Stage 3...").
5. **Optional custom rationale** — free text, entirely human-authored,
   never suggested, drafted, or completed by PCAE.
6. **Optional conditions and limitations** — free text, same rule as (5).
7. **Exact decision preview** — the literal content that will be published,
   shown verbatim before confirmation, with no paraphrase.
8. **Explicit human confirmation** — a distinct act, described in §10,
   never inferable from steps 1–7 alone.
9. **Canonical record publication** — atomic write of the confirmed record
   into canonical storage (§7).

### 3.3 Content-Class Separation

| Content class | Who authors it | Example |
|---|---|---|
| Machine-generated neutral scaffolding | PCAE (template engine) | "Decision subject: ..." |
| Machine-generated boundary language | PCAE, drawn verbatim from the governing template's mandatory non-effect statements | "does not itself begin Stage 3" |
| Human-selected substantive choice | Human, from a bounded set | "Option A — Proceed" |
| Optional human-authored rationale | Human, free text | "Stage 3 Readiness has been independently verified..." |
| Optional human-authored conditions | Human, free text | "This election does not authorize..." |
| Final human confirmation | Human, a distinct confirmation act | "I confirm this is my human governance decision..." |

The published record must make this separation structurally visible (not
merely stylistically) — e.g., distinct fields/sections per §5 — so a
verifier can mechanically tell which text is PCAE's boundary language and
which is the human's own words, without relying on prose tone.

### 3.4 What the System May and May Not Do

The system **may**: assemble citations, render templates, enforce that a
selection exists among the bounded set, validate that required fields are
present, format the preview, and write the confirmed record.

The system **may not**: choose an option, suggest a "recommended" or
"default" option, complete or edit human-authored rationale text, treat
silence/timeout/inactivity as a selection, or publish without the distinct
confirmation act of step 8.

---

## 4. Decision Template Architecture

### 4.1 Purpose

A **decision template** is the governed definition of one class of
recordable act (e.g., "GAC-001 §9 Stage 6 governance decision," "GPC6-001
Stage-3-prerequisite election"). Templates are what make bounded choice
possible without hand-authoring prose each time.

### 4.2 Required Template Fields

| Field | Description |
|---|---|
| Decision type | Stable identifier for the class of act (e.g., `gac001-sec9-stage6`) |
| Authoritative basis | Governing contract clause(s) that define this decision (e.g., GAC-REQ-042) |
| Eligible human authority | Who may make this decision (a role or named authority per GPC6-REQ-040-style ownership, never "any user") |
| Subject | What entity/pilot/contract this instance concerns, bound at creation time |
| Allowed choices | The exhaustive, closed option set — no open-ended "other" that silently expands scope |
| Required fields | Fields that must be present before confirmation is possible |
| Optional fields | Fields (rationale, conditions) that may be left blank |
| Consequence statements | Machine-rendered text describing what each choice causes |
| Mandatory non-effect statements | Machine-rendered text describing what the decision does **not** cause — required, not optional, per GAC-REQ-043's "automatic adoption is forbidden" pattern |
| Confirmation method | Which confirmation mechanism(s) this decision class requires (§10) |
| Expiry rules | Whether/how this decision class expires (e.g., time-boxed authorizations vs. standing elections) |
| Supersession and revocation rules | Who may supersede/revoke an instance of this template and under what conditions |

### 4.3 Template Governance Constraints

- A template SHALL NOT embed a preferred, recommended, or default choice.
- A template SHALL NOT order options in a way that implies a preference
  (e.g., templates render options in a fixed, arbitrary, or
  alphabetical/source-document order, never a "most likely" order).
- A template's option set is authored and approved through governed change
  (a future contract-freeze phase, §20), never invented ad hoc by an
  interactive session.
- A template SHALL enumerate every option actually present in its
  governing contract text (e.g., GAC-REQ-042's five outcomes) — templates
  may not silently drop or merge options.

---

## 5. Canonical Record Model

### 5.1 Conceptual Fields (Non-Binding — No Schema Frozen)

| Field group | Fields |
|---|---|
| Identity | canonical record ID (§6), schema/template version, record type |
| Subject | subject identity (pilot/contract/artifact this record concerns) |
| Decision-maker | decision-maker identity, assurance level (§10) |
| Authority basis | citation(s) to the governing contract clause(s) invoked |
| Decision content | decision selections (from the template's bounded set), human rationale (optional), conditions and limitations (optional) |
| Evidence | governing artifact references, evidence references considered |
| Timing | decision timestamp, confirmation evidence, publication timestamp |
| Provenance | provenance record (§12) |
| Integrity | integrity digest (§12) |
| Lifecycle | record state (§8), predecessor/successor relationships, supersession status, suspension status, revocation status |
| Compatibility | schema/template version, compatibility notes, known limitations |
| Representations | canonical machine-readable representation, deterministic human-readable rendering |

### 5.2 Why No Schema Is Frozen Here

Per this phase's Non-Goals (§23), an executable schema is explicitly
deferred to 143B (Contract Freeze), mirroring how Phase 142C (architecture)
preceded Phase 142D/GPC6R-001 (contract freeze) rather than freezing
requirements itself. This section defines the conceptual shape a future
schema must cover; it does not enumerate types, required-ness, or
validation rules with contract force.

---

## 6. Record Identity and Namespace

### 6.1 Chosen Form

**`HGR-<sequence>`** (e.g., `HGR-000001`), independently justified below.

### 6.2 Rejected Alternative

`CHR-000001` was considered and rejected: `CHR` collides in this
repository's own vocabulary with "Canonical [phase] Report"-adjacent
abbreviations already in use informally in commit messages and risks being
misread as a phase-report identifier. `HGR` ("Human Governance Record") is
unambiguous and does not collide with any existing identifier prefix found
in this repository (phase IDs are numeric/alphanumeric like `142I`,
`137ZA`; contract IDs use full names like `GAC-001`; CLTR uses
`AuthorityEpoch`/`AuthorityState`, not an `HGR`-shaped prefix).

### 6.3 Identity Requirements

| Requirement | Design |
|---|---|
| Uniqueness | Monotonic integer sequence, zero-padded, assigned only at confirmed publication (never at draft creation, so abandoned drafts never consume or gap the sequence in an observable way) |
| Monotonicity / collision resistance | Sequence numbers are assigned by a single canonical allocator (mirrors phase-ID allocation discipline referenced in `docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md`); a future contract phase must define the allocator's concurrency behavior — this phase only requires that it be collision-resistant, not that it be a bare filesystem `ls`-and-increment |
| Repository portability | The ID is self-contained text, independent of file path, branch, or remote — a record's identity does not change if the repository is cloned, forked, or renamed |
| Subject binding | The ID identifies the *record*, not the *subject*; a subject (e.g., `GLP-PILOT-C6`) may have many records referencing it, each with its own independent `HGR-######` |
| Version independence | The ID never encodes a template/schema version — versioning lives in the record content (§5), not the identifier, so template evolution never forces identifier churn |
| Stable referencing | Once assigned, an ID is never reused, reassigned, or reclaimed, even if the record is later revoked |
| Prevention of filename-based authority | The ID is a logical identifier, not a trust claim — see §9: a record's existence under a canonical-looking ID never itself establishes authority |

---

## 7. Storage Architecture

### 7.1 Boundary Principle

Storage for CHGRs must be structurally separate from
`.pcae/phase-completion-report.md` / `.pcae/phase-completion-metadata.json`
and from `.pcae/phase-reports/` — those are phase-completion machinery
(§15), single-instance-per-phase, and governed by different trust gates
(`_check_canonical_metadata_consistency()`, quarantine-on-mismatch). CHGRs
are a different artifact class with their own multiplicity (many per
subject) and lifecycle (§8).

### 7.2 Candidate Structure

```
.pcae/governance-records/
  <record-id>/
    record.json        # canonical machine-readable representation
    record.md           # deterministic human-readable rendering
    provenance.json      # what was presented, selected, confirmed, when
    integrity.json        # digest of record.json at publication time
  index.json            # registry: id -> subject, type, state, timestamps
```

This mirrors the existing repo pattern of pairing a machine-readable JSON
artifact with a human-readable Markdown rendering (as phase-completion
metadata/report already do) and an explicit provenance/integrity split (as
`CanonicalEngineeringEvidence`'s `EvidenceProvenanceRecord` already does),
rather than inventing an unprecedented shape. A future contract-freeze
phase determines the final structure; this is evaluated, not adopted.

### 7.3 Design Requirements

| Concern | Requirement |
|---|---|
| Canonical machine-readable representation | One canonical JSON per record, the authoritative content; the Markdown rendering is derived from it, never the reverse (mirrors the report/metadata directional-sync discipline in `commands/phase.py`'s `run_phase_metadata_repair()`, applied in the opposite, correct direction here: JSON → Markdown, never Markdown → JSON) |
| Deterministic human-readable rendering | Rendering is a pure function of `record.json`; regenerating it must always produce byte-identical output for unchanged input (INV-8) |
| Index/registry | A single `index.json` enumerating all records by ID, subject, type, and current state, so lookups never require directory scanning as the sole mechanism |
| Provenance evidence | `provenance.json` per record (§12) |
| Integrity evidence | `integrity.json` per record: a digest of `record.json` at publication time, so any later on-disk modification is mechanically detectable (does not itself prevent modification — see §11) |
| Attachments | Out of scope for this phase; if a future template requires attachments, they must be content-addressed and referenced, never embedded ambiguously |
| Archived/superseded records | Superseded/revoked records remain in place (never deleted, never moved to a separate "archive" location that could be mistaken for deletion); state (§8) is a field, not a location |
| Repository portability | Storage lives under `.pcae/`, versioned in git like all other governance artifacts, so it travels with the repository |
| Atomic publication | Publication of a confirmed record must write all of `record.json`, `record.md`, `provenance.json`, `integrity.json`, and the index update as a single atomic unit (write-temp-then-rename or equivalent) — a partial write must never leave a record in an ID-assigned-but-unpublished, ambiguous state |

---

## 8. Record State Model

| State | Who may cause entry | Required evidence | Permitted transitions | Prohibited transitions | Authority effect | Lifecycle effect | Runtime effect |
|---|---|---|---|---|---|---|---|
| **draft** | The human, via the interactive workflow (§3), before confirmation | None yet | → awaiting-human-confirmation, → discarded (not stored canonically) | → published (must pass through confirmed first) | None | None | None |
| **awaiting-human-confirmation** | System, after all required template fields are populated | Complete preview rendered (§3.2 step 7) | → confirmed, → draft (human backs out) | → published directly | None | None | None |
| **confirmed** | The human, via the distinct confirmation act (§10) | Confirmation evidence (§12) | → published | → any state skipping publication | None (confirmation is not yet publication) | None | None |
| **published** | System, immediately following confirmation, as an atomic act (§7.3) | Confirmed record + complete provenance/integrity artifacts | → suspended, → superseded, → revoked | → draft, → confirmed (no un-publishing) | Established per the record's own content, subject to §9's boundary | Only as a separately governed contract explicitly says (INV-12) | None (INV-13) |
| **suspended** | Only a human authority eligible under the record's own template rules, or a separately governed process the template names | A new, linked CHGR recording the suspension act | → published (restoration, if the template permits it), → revoked | → draft, → confirmed | Temporarily inert; the underlying published record's text is unchanged, but its current applicability is marked inert | As separately governed | None |
| **superseded** | A new, later, published CHGR that explicitly supersedes this one (§11) | The superseding record's own publication | (terminal for this record; the successor record has its own state) | any transition back to published/confirmed | The superseded record remains valid historical evidence of what was decided *then*; it is no longer the current word on the subject | As separately governed | None |
| **revoked** | Only a human authority eligible under the record's own template rules | A new, linked CHGR recording the revocation act, or a governed revocation record type | (terminal) | any transition back to published | The record's authority effect is permanently withdrawn; it remains as historical evidence, never as current authority | As separately governed | None |
| **invalidated** | System or human, only on discovery of a structural defect (corrupted integrity digest, missing required field discovered after the fact) | An audit finding | (terminal; a corrected record must be a *new* published record, never an edit) | any transition implying the invalid content is still usable | The record can no longer be cited as authoritative for anything, including its own historical-evidence value, until independently re-verified | As separately governed | None |

Human confirmation (entry to `confirmed`) and governed publication (entry
to `published`) are kept as **two distinct acts** so that a future audit
can distinguish "the human confirmed this text" from "this text was
committed to canonical storage" — collapsing them would make it impossible
to detect a publication-time corruption between what was confirmed and
what was stored.

---

## 9. Authority Boundary

### 9.1 The Core Distinction

This architecture draws a hard line between **record existence** and
**authority**. A CHGR's presence in canonical storage, under a
well-formed ID, with valid integrity evidence, is proof that a decision
*was recorded* — never proof that the decision-maker *held the authority*
to make it, that the decision is *currently applicable*, or that any
later action is *authorized* by it.

### 9.2 What Never Establishes Authority, By Itself

| Non-authoritative fact | Why it is insufficient alone |
|---|---|
| Record existence in the repository | Existence proves recording occurred, not that the recorded decision is valid or current |
| A canonical-looking filename or ID (`HGR-000001`) | An identifier is a reference, not a credential (§6.3) |
| An AI generated the scaffolding | Scaffolding generation is explicitly non-substantive (§3.3); it never contributes authority |
| The record was committed to git | Commit history proves the record was stored at a point in time, not that its content is currently authoritative |
| The record appears in the index | The index is a lookup aid, not an authority ledger |
| A phase report references the record | A reference is a citation, not a re-grant of authority — see §16's proposal/decision separation |

### 9.3 What Does Establish Authority

Authority derives from the conjunction of: (a) **valid human action** — a
record whose decision-maker identity, confirmation evidence, and content
are all present and internally consistent (§10, §12); and (b) **the
applicable governing authority model** — the eligible-authority rule
defined by the record's own template (§4.2) and, ultimately, by the
governing contract that template was derived from (e.g., GPC6-REQ-040's
role table). A record satisfying (a) but not named as eligible under (b)
is recorded evidence of an act, not a valid exercise of governance
authority — the architecture requires this distinction be surfaced, never
silently resolved in the record's favor (INV-14).

### 9.4 Layered Verification (Conceptual, Not Implemented Here)

A future consumer verifying whether a CHGR is currently authoritative for
some action must check, in order, and fail closed at any gap: record
exists → integrity digest matches → decision-maker identity is present and
consistent with confirmation evidence → decision-maker is eligible under
the applicable governing authority model *at the time relied upon* →
record state is `published` (not draft/suspended/superseded/revoked/
invalidated) → record scope actually covers the action in question → no
newer record supersedes it. This phase defines the check list
conceptually (§17); it implements none of it.

---

## 10. Human Identity and Confirmation Architecture

### 10.1 Assurance Levels

| Level | Mechanism | Assurance provided |
|---|---|---|
| L0 — Explicit typed confirmation | The human types an exact confirmation phrase (as the existing election record already does: "I confirm this is my human governance decision under GPC6-REQ-075(b)") | Evidence of deliberate intent; no identity binding beyond whoever operates the terminal/session |
| L1 — Authenticated local-user confirmation | Bound to an OS-level or locally authenticated user identity at confirmation time | Adds session/user-identity binding |
| L2 — Signed confirmation | A cryptographic signature over the exact preview content | Adds tamper-evidence and non-repudiation, contingent on key custody |
| L3 — Hardware-backed confirmation | Signature backed by a hardware security module or platform authenticator | Adds key-extraction resistance |
| L4 — External identity-provider confirmation | Confirmation routed through and attested by an external IdP | Adds independently verifiable identity assertion |
| L5 — Multi-party confirmation | Two or more eligible authorities must independently confirm | Adds collusion/error resistance for decisions the template marks as requiring it |

### 10.2 Rule: No Overclaiming

The architecture SHALL NOT claim an assurance level higher than what
actually occurred. GPC6-REQ-075(b)'s existing election is **L0** — typed
confirmation with no cryptographic binding — and any future canonical
representation of it must say so explicitly (§14), not silently upgrade it
by virtue of being stored in a more structured format.

### 10.3 Representing Assurance Without Invalidating Legacy Records

Every CHGR carries an explicit `assurance_level` field. A record's
validity as a *human governance act* does not depend on reaching any
particular assurance level — L0 records remain fully valid evidence of
what was decided; assurance level affects only how strongly a future
consumer may rely on the *identity binding*, not whether the decision
itself is honored. This lets legacy L0 imports (§14) coexist honestly with
future L2+ records without a forced re-confirmation.

---

## 11. Immutability, Correction, and Supersession

### 11.1 Publication Immutability

Once a CHGR enters `published` state, its substantive fields (decision
selections, rationale, conditions, decision-maker identity, timestamps,
authority basis) are never edited in place (INV-9). This mirrors
`CanonicalEngineeringEvidence.finalize()`'s existing pattern in this
repository of returning a new frozen instance rather than mutating, and
`ArtifactState`'s existing rule that `CANONICAL` has no outbound
transition in `ALLOWED_STATE_TRANSITIONS`.

### 11.2 Correction of Non-Substantive Errors

A narrow, explicitly bounded correction path exists only for rendering or
metadata defects that do not change meaning: e.g., a Markdown rendering
bug that mis-escapes a character, or an index entry pointing at the wrong
relative path. Any such correction must be logged with a before/after diff
(mirroring `phase-metadata-repairs.log`'s existing discipline) and must
never touch `record.json`'s decision-content fields. If there is any doubt
whether a fix is substantive, it is treated as substantive (fail-closed,
INV-14) and requires supersession instead.

### 11.3 Substantive Amendment Prohibition

Any change to what was decided, by whom, under what conditions, requires a
**new** CHGR, never an edit to the existing one.

### 11.4 Supersession

A new, published CHGR may explicitly name a prior record as superseded.
Supersession is itself a governed act requiring the same template/
confirmation discipline as any other decision (it is not a bare CLI flag
flip) — see §13. The prior record's state moves to `superseded`; its
content is untouched.

### 11.5 Suspension, Revocation, Withdrawal, Invalidation

- **Suspension**: temporary inertness, reversible, per §8.
- **Revocation**: permanent withdrawal of effect, per §8, terminal.
- **Withdrawal**: applies only to an unpublished draft/confirmed record —
  the human abandons it before publication; nothing canonical exists to
  preserve.
- **Invalidation**: a structural-integrity finding (§8), distinct from a
  human's substantive change of mind — invalidation is a fact-finding act,
  not a decision act, and does not require a new CHGR of the same
  decision-type template, though it must itself be recorded as an audit
  event.

### 11.6 Restoration

Restoration from `suspended` back to `published` is permitted only if the
governing template explicitly allows it and only through a new, linked
governance act (never a silent timer expiry or automatic reversal).
Restoration from `superseded`, `revoked`, or `invalidated` is not
permitted — those are terminal by design (INV-10); a genuine change of
mind after revocation requires an entirely new decision, not a resurrected
old one.

---

## 12. Provenance and Integrity Architecture

### 12.1 Provenance Evidence (What Must Be Captured)

| Question | Evidence field |
|---|---|
| Who provided the decision? | `decision_maker` identity, bound at confirmation |
| How was it provided? | `confirmation_method` (§10 assurance level) and interaction trace reference |
| What options were presented? | Verbatim copy of the bounded option set and boundary language shown at preview time |
| What was selected? | The selection field(s), unambiguous, matched against the template's closed set |
| What text was displayed at confirmation? | The exact preview content (§3.2 step 7), stored verbatim — this is what the human actually confirmed, not a reconstruction |
| When did confirmation occur? | `decision_timestamp` / `confirmation_timestamp` |
| What artifact was published? | `record.json`'s content hash at publication |
| Whether the artifact changed afterward | `integrity.json`'s digest, re-checkable at any later time |
| Repository and commit provenance | The git commit(s) that introduced the record files, mirroring how the existing election is anchored to commit `4e24e66d` |
| Schema/template provenance | Which template version (§4) and, transitively, which governing contract version was in force at confirmation time |

### 12.2 Provenance Is Not Authority

Provenance answers "what happened and how do we know" (§12.1). Authority
answers "does this decision currently govern anything" (§9). A
provenance-complete record can still be non-authoritative (wrong
decision-maker for the template, superseded, revoked); provenance
completeness is a necessary evidentiary property, never a sufficient
authority claim (INV-11, restated here for the provenance layer
specifically since this is the most common place the two get conflated).

---

## 13. Interactive CLI/API Boundary

### 13.1 Conceptual Command Surface

| Command (conceptual) | Effect | Confirmation-safe? |
|---|---|---|
| create from a governed template | Opens a new draft against a named template and subject | Yes — produces `draft` only |
| resume an unconfirmed record | Re-enters an in-progress `draft`/`awaiting-human-confirmation` session | Yes |
| preview | Renders the exact-decision-preview (§3.2 step 7) without confirming | Yes — read-only |
| confirm | Performs the distinct confirmation act (§10), moving `awaiting-human-confirmation` → `confirmed` | Requires explicit, non-defaultable human input; never scriptable to "confirm whatever is pending" without displaying the exact content first |
| publish | Atomically writes the confirmed record to canonical storage (§7.3), `confirmed` → `published` | System-performed immediately after confirm, but logically distinct |
| inspect | Read-only display of a record's content and state | Yes |
| verify | Re-checks integrity digest and provenance completeness | Yes — read-only |
| list | Enumerates records by subject/type/state | Yes — read-only |
| reference | Emits a citable pointer (ID + digest) for use in a later phase or document | Yes — read-only |
| suspend | Records a suspension act against a published record | Requires its own confirmation, same discipline as `confirm` |
| supersede | Creates a new record explicitly linked as superseding a prior one | Requires its own full decision workflow (§3), not a flag |
| revoke | Records a revocation act | Requires its own confirmation, same discipline as `confirm` |
| import a legacy human record | Wraps an existing freeform record per §14 | Requires explicit acknowledgment that no new election is being made |

### 13.2 Mandatory Prohibition

**No command in this surface may silently create a `published` (or even
`confirmed`) record without the distinct confirmation act displaying the
exact content first.** There is no "create and auto-confirm" variant, no
`--yes`/`--force` path that skips preview-then-confirm for a governance
decision. This applies to every command that can reach `confirmed` or
`published`, including `supersede` and `revoke`.

This section deliberately stops short of flag syntax, argument shapes, or
exit-code contracts — those are 143E's (Implementation) concern, not
architecture's.

---

## 14. Legacy Record Import Architecture

### 14.1 Goal

Design how `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` will later be
represented as a canonical HGR **without** re-electing anything. This
section is a design; no import is performed by this phase.

### 14.2 Import Principles

| Requirement | Design |
|---|---|
| Preserve the original Markdown verbatim | The source file's exact bytes are retained, either embedded as an evidence attachment or referenced by path + content digest — never rewritten, reformatted, or "cleaned up" as part of import |
| Preserve original commit provenance | The import records the source commit (`4e24e66d`) as part of `provenance.json`; it does not claim the import commit as the decision's origin |
| Identify as a legacy human-authored source | The resulting HGR's `assurance_level` is explicitly L0 (§10.3) and a dedicated field marks it `imported: true, source: legacy-markdown` |
| Avoid retroactively claiming stronger assurance | Import must not add a signature, authenticated-identity binding, or any assurance marker the original act never had |
| Generate a canonical wrapper or derived representation | `record.json` is a structured re-expression of the original's content (decision type, selections, rationale, conditions, decision-maker, timestamp) sufficient to satisfy §5's conceptual model, with the original Markdown as the authoritative textual evidence it is derived from |
| Retain a digest of the source | `integrity.json` includes a digest of the original Markdown file as it existed at import time |
| Preserve original decision timestamp and confirmation wording | `decision_timestamp` = 2026-07-23 (the original's own "Decision date"); the confirmation field carries the original's exact confirmation sentence, not a paraphrase |
| Require no new substantive election | The import workflow contains no step that presents options or accepts a new selection — it is a read-and-wrap operation over already-decided content |
| Disclose any unavailable metadata | If some conceptual field (§5) cannot be populated from the source (e.g., no machine-readable assurance-level marker existed at authoring time), the import record explicitly says so rather than guessing or leaving it silently blank |
| Prevent import logic from altering meaning | The importer performs no interpretation, summarization, or normalization of the decision content beyond mechanical field extraction that a human reviewer can verify field-by-field against the source text |

### 14.3 What Import Explicitly Does Not Do

Import does not re-run GPC6-REQ-075(b)'s election, does not ask Atila
Madai to re-confirm anything, does not change `PROJECT_STATUS.md`'s
existing narrative about the election, and does not alter the source
Markdown file. The import produces an *additional*, structured,
canonically identified representation *alongside* the untouched original —
never a replacement for it.

---

## 15. Phase Report Separation

| | Canonical Phase Reports | Canonical Human Governance Records |
|---|---|---|
| Describes | Governed PCAE phase execution (what engineering work happened) | A human's exercise of governance authority (what was decided) |
| Machinery | `.pcae/phase-completion-report.md` + `-metadata.json`, `write_canonical_report()`, `_check_canonical_metadata_consistency()` | A distinct storage boundary (§7), a distinct state model (§8) |
| Authored by | The agent performing the phase (subject to human review) | The human decision-maker exclusively, for substantive content (§3.3) |
| Cardinality | Exactly one per phase | Many per subject, as decisions accumulate |
| Updates phase metadata? | Yes — that is its purpose | Never |
| Advances phase status? | Yes | Never — a CHGR is not a phase and has no phase-lifecycle effect of its own (INV-15) |
| May reference the other? | May cite a CHGR as evidence a prerequisite decision was made (as this document cites the existing election) | May cite a phase report as evidence considered (as the existing election already cites Phases 139F–142I) |
| Regenerated/overwritten by the other's machinery? | No | No — `pcae phase complete` never writes to `.pcae/governance-records/`, and no CHGR workflow ever writes to `.pcae/phase-completion-*` |

A human governance record may affect later lifecycle eligibility **only**
through explicit governing contracts (e.g., a future contract could say
"Stage 3 entry requires citing HGR-000001") — never by implicit inference
from a phase report mentioning it.

---

## 16. Proposal-to-Decision Separation

### 16.1 Distinct Artifact Classes

| Class | Origin | Authority |
|---|---|---|
| AI or agent proposal | An AI/agent, e.g. a phase's "Recommended Next Phase" text | None — advisory only, exactly as `HANDOFF_ADVISORY` and existing recommendation language already establish repository-wide |
| Neutral decision template | Governed template authorship (§4, §20) | Structural only — defines the bounded shape, contributes no decision |
| Human draft | A human, in-progress, unconfirmed | None yet — a draft is not evidence of a completed decision |
| Confirmed human decision | A human, via the distinct confirmation act (§10) | Evidence of a completed act, pending publication |
| Published canonical record | System, atomically, immediately after confirmation | As bounded by §9 |

### 16.2 Prevention Rules

- An AI-authored proposal (e.g., this document's own §24 roadmap
  suggestion) can never be stored as, indexed as, or mistaken for a
  `confirmed`/`published` CHGR — proposals have no path into the state
  model of §8 at all; they live in ordinary phase-report prose.
- **Silence, inactivity, timeout, or default selection never constitutes
  acceptance.** There is no state transition in §8 that a proposal can
  reach through the mere passage of time or the absence of a human
  response — this directly implements GAC-REQ-043's "automatic adoption is
  forbidden" principle at the record-architecture layer, generalized
  beyond GAC-001 §9 to every decision class.

---

## 17. Runtime Enforcement Relationship

### 17.1 Future Relationship (Described, Not Implemented)

A future, separately architected and separately authorized enforcement
layer might consume CHGRs to check, before permitting some governed
action: record identity verification (does the cited `HGR-######` exist
and match its integrity digest) → authority-scope verification (is this
record's decision-maker eligible and is its subject the one in question) →
current-state verification (`published`, not suspended/superseded/
revoked/invalidated) → expiry verification (if the template defines
expiry) → supersession/revocation verification (no newer linked record
overrides it) → action-to-authority matching (does the specific action
fall within what this record's selection actually authorizes, per §9.3).

### 17.2 Explicit Non-Implementation

This phase does **not** implement any of §17.1. No runtime code path
reads `.pcae/governance-records/`. No CLI command in §13 gates any other
command's behavior. This architecture document is not, and does not
purport to be, an authority grant for anything (INV-13, INV-17) — it
describes a future possibility for a future, separately governed phase to
build and separately authorize.

### 17.3 Self-Authorization Prohibition

No agent — including the one producing this document — may treat this
architecture, or any future implementation of it, as authorizing itself to
mint, confirm, or publish a CHGR on a human's behalf. Publication requires
the distinct human confirmation act of §10 in every case, with no
architectural exception for "the system is confident this is what the
human would want."

---

## 18. Security and Threat Model

| # | Scenario | Architectural mitigation |
|---|---|---|
| T1 | AI-generated fake human decision | INV-1/INV-2: substantive fields are never AI-authored; §3.3's content-class separation makes AI-authored text structurally confined to scaffolding/boundary language, never to selections or confirmation |
| T2 | Preselected options | §4.3: templates SHALL NOT embed a default; §3.2 step 3 requires explicit selection every time |
| T3 | Coercive option wording | §4.3: template governance (§20) reviews wording; §3.4 forbids the interactive session from editorializing beyond the governed template text |
| T4 | Silent defaults | INV-3; §16.2: no state transition occurs from silence |
| T5 | Fabricated identity | §9.4 layered verification requires decision-maker eligibility per the applicable governing authority model, not mere presence of a name field; §10 assurance levels make identity-binding strength explicit so weak bindings (L0) are never mistaken for strong ones |
| T6 | Replayed obsolete decisions | §8's state model: consumers must check current state (not `superseded`/`revoked`/`suspended`) before relying on a record (§17.1) |
| T7 | Modified published records | §7.3 integrity.json digest + §11.1 immutability make any post-publication edit both prohibited and mechanically detectable |
| T8 | Record substitution | §6.3: identifiers are never reused or reassigned; §12.1 anchors provenance to specific commit(s), preventing a different record from being swapped in under the same ID undetected |
| T9 | Scope broadening | §9.3: authority is bounded by the record's own content and template scope; §17.1's "action-to-authority matching" step exists precisely to prevent a record authorizing something it never named |
| T10 | Stale authorization | §4.2 template expiry rules; §17.1 expiry verification step |
| T11 | Revoked-record reuse | §8: `revoked` is terminal with no restoration path (§11.6); §17.1 explicitly checks revocation state |
| T12 | Decision-template tampering | §4.3/§20: template authorship and approval are governed acts, not ad hoc session-time edits; a future implementation must version templates and bind each record to the specific template version in force (§12.1) |
| T13 | Proposal/decision confusion | §16: distinct artifact classes with no shared state-model path from proposal to published |
| T14 | Phase-report/decision confusion | §15: structurally separate storage, machinery, and cardinality |
| T15 | Import-time semantic alteration | §14.2: verbatim preservation, field-by-field extraction, no interpretation/summarization |
| T16 | Compromised local user session | §10's tiered assurance model: L0 provides no session-compromise resistance and the architecture requires this be disclosed, not hidden — a future phase choosing stronger assurance (L1+) for high-stakes decision types is anticipated, not precluded |
| T17 | Unauthorized supersession or revocation | §8: suspension/revocation require eligibility under the record's own template rules (§9.3), and are themselves full governed decision acts (§11.4, §13.1), not bare state flips |

### 18.1 Fail-Closed Default

For every scenario above, the architecture's default response to any
detected ambiguity or verification gap is to treat the record as
**not currently authoritative** for the action in question (INV-14) —
never to proceed on a best-effort or benefit-of-the-doubt basis.

---

## 19. Compatibility Architecture

| Existing subsystem | Relationship |
|---|---|
| PCAE phase lifecycle | Unaffected; CHGRs are lifecycle-neutral by default (INV-12, §15) |
| Canonical phase reports (`phase_reports.py`) | Structurally separate machinery (§15); CHGRs may be *cited by* phase reports, never generated by the same write path |
| Phase-completion metadata (`phase-completion-metadata.json`) | Unaffected; no shared fields, no shared file |
| PGP-001 evidence requirements | A CHGR is itself a form of evidence artifact and should satisfy PGP-001's general evidence-citation discipline once referenced by a phase, but PGP-001 is not modified by this phase |
| Existing typed-authority / `HumanAuthorization` (Track 136 CLTR) | **Not reused — deliberately kept separate.** Per grounding research, CLTR's `HumanAuthorization` is a token-scoped, 24-hour-expiring, single-use execution-permission record for a specific technical cutover attempt, explicitly disclaiming "never itself proves a real human actually made that decision" and forbidding `authority_role: "authoritative"`. A CHGR is the opposite: a durable, non-expiring-by-default (unless the template says otherwise), narratively rich record of a governance decision that *is* the human's authoritative act by construction (subject to §9's eligibility layer). Composing CHGR on top of `HumanAuthorization`'s schema would import inapplicable fields (`replay_binding`, `risk_acknowledgement` framed as cutover-specific) and, worse, would inherit CLTR's explicit "never proof of authority" framing, which is precisely wrong for CHGR's purpose. They remain separate artifact families. |
| `ArtifactState` promotion machine (Phase 114A, `canonical_artifact_promotion.py`) | **Reuse candidate for future implementation, not adopted here.** Its generic `DRAFT → VALIDATED → CERTIFIED → CANONICAL` (+ `REJECTED`/`QUARANTINED`) shape is structurally close to §8's early states, and the module's own docstring anticipates "future artifact classes." However, it has no `SUPERSEDED`/`SUSPENDED`/`REVOKED` states, which §8 requires as first-class outcomes — a future implementation phase should evaluate whether to extend `ArtifactState` with these states (risking effect on the existing phase-report caller) or define a CHGR-specific, structurally similar but independent state enum. This phase does not decide between them; §20 names it a future contract question. |
| `CanonicalEngineeringEvidence` (Phase 134E.1) | **Closest existing precedent for immutability-after-finalization + supersession**, but itself dormant/unwired and governed by frozen Track 133/134 contracts outside this phase's authority to modify. §8 and §11 deliberately mirror its `DRAFT → FINALIZED → SUPERSEDED` pattern (frozen-dataclass-style immutability, `superseded()` only from a finalized state) as *inspiration*, not as a shared class — CHGR is a new artifact family with its own governing contract, to avoid entangling GPC6-REQ-075(b)-class decisions with Track 133/134's engineering-evidence-specific `CorrectionMetadata` semantics. |
| Lifecycle authority boundaries (`lifecycle.py`) | Unrelated domain (backend-output-adoption lifecycle detection); no overlap, no reuse needed |
| Runtime enforcement architecture | Related only through §17's described future relationship; no current coupling |
| Repository status reporting (`PROJECT_STATUS.md`) | A published CHGR may be *narratively summarized* in `PROJECT_STATUS.md` (as the existing election already is), but `PROJECT_STATUS.md` is never the canonical store — the CHGR files are |
| Historical memory (this repository's own memory/provenance conventions) | Unaffected; CHGRs are a repository artifact, not a memory-system artifact |
| Future external signing systems | §10's L2–L4 assurance levels are designed as an open extension point, not a closed enumeration, so a future signing integration adds a new assurance level rather than redesigning the model |

### 19.1 Stage 3 Companion Schema Reuse — Explicit Analysis

Track 136's Stage 3 Companion Executable Schema family (`AuthorityEpoch`,
`AuthorityState`, `HumanAuthorization`, `CutoverCandidate`,
`Certification`) is, per its own governing contracts and module
docstrings, (a) scoped exclusively to the CLTR legacy-to-typed-record
migration domain, (b) explicitly non-authoritative by design, and (c)
closed/dormant as of Track 136's own final review ("no Group 12"). Reusing
it for CHGR would require either (i) stripping its CLTR-specific
non-authority disclaimers, which would silently weaken a safeguard another
track relies on, or (ii) subclassing/wrapping it, which would create a
confusing dependency from a general-purpose governance-decision artifact
onto a narrow, dormant migration-tooling schema. Neither is appropriate.
**Conclusion: Stage 3 companion schemas must remain separate from CHGR.**
Only the *generic* `ArtifactState` promotion machine (114A) is a plausible
composition/extension target, per the row above, and only as a future
143B+ decision.

---

## 20. Governance and Responsibility Model

Following GPC6-REQ-040's "one owner per responsibility" discipline, mapped
onto existing role concepts wherever one already exists:

| Responsibility | Owner | Basis |
|---|---|---|
| Template authorship | An Implementer role performing governed template-authoring work (not a new role — analogous to how GPC6-REQ-040 already names Implementer-class roles for build/packaging concerns) | §4, §20 |
| Template approval | Independent Contract Verifier (existing role) reviewing the template against its governing contract before it enters use | §4.3 |
| Interactive presentation | PCAE tooling (system), strictly bounded to scaffolding/boundary language per §3.3 | §3 |
| Human selection | The eligible Human Authority named by the template (§4.2) — never a new role; uses the same "Human Authority" concept GPC6-REQ-040 already defines | §3, §9 |
| Confirmation | The same Human Authority, via the distinct confirmation act | §10 |
| Publication | System, atomically and immediately following confirmation, performing no discretionary act | §7.3 |
| Custody | Repository/version-control custody — no new custodial role; the repository's existing commit/push governance already covers this | §7 |
| Verification | Independent Contract Verifier or Independent Implementation Verifier (existing roles), depending on what is being verified | §9.4 |
| Supersession | Only a human authority eligible under the record's own template | §11.4 |
| Suspension | Same as supersession | §11.5 |
| Revocation | Same as supersession | §11.5 |
| Runtime consumption | **Not yet assigned — explicitly a future contract question (§17), not silently assigned to any role by this phase** | §17 |

No new role or authority is introduced by this phase. Where an
operational responsibility (runtime consumption, template-approval
tooling ownership) does not yet map cleanly onto an existing role, this
document names it as an open question for 143B, rather than assigning it
by default.

---

## 21. Audit and Inspection Architecture

A future consumer or auditor must be able to determine, from the record
alone (never from conversational or session history):

- **What** decision was made — the selection field(s), verbatim (§5, §12).
- **By whom** — decision-maker identity (§5, §9).
- **Under what authority** — authority basis citation (§5) plus the
  template's eligible-authority rule (§4.2), checked against §9.3.
- **Using which template** — template ID and version (§5, §12.1).
- **Against which evidence** — governing artifact/evidence references
  (§5), mirroring the existing election's "Evidence Considered" section.
- **With what conditions** — conditions/limitations field (§5).
- **At what assurance level** — explicit `assurance_level` (§10).
- **Whether it remains current** — record state (§8), checked, not
  assumed.
- **Whether it was superseded, suspended, or revoked** — predecessor/
  successor linkage and state (§8, §11).
- **Which later actions relied upon it** — this direction (record →
  dependent actions) is not stored on the record itself, to avoid an
  unbounded back-reference list; instead, any later action that relies on
  a CHGR must itself cite the CHGR's ID (forward reference, from the
  dependent artifact to the record), the same pattern this very document
  uses to cite the GPC6-REQ-075(b) election. A future audit tool can
  build the reverse index by scanning citations, without the record
  itself needing to track its own dependents.

---

## 22. Success Criteria

The architecture is successful if a future 143B+ implementation
satisfying it can demonstrate:

1. Human choices can be made interactively, without hand-authored prose
   required.
2. Essay writing (rationale, conditions) is optional in every template.
3. No substantive option is ever selected, defaulted, or completed by an
   AI system (INV-1–INV-3).
4. No default, timeout, or silence creates consent (§16.2).
5. Records are structurally and operationally separate from phase reports
   (§15) — no shared write path, no shared file.
6. Records are canonically identifiable via a stable, collision-resistant
   namespace independent of phase IDs (§6).
7. Published meaning is immutable; correction is possible only for
   non-substantive rendering/metadata defects (§11).
8. Provenance and assurance level are explicit and never overstated
   (§10, §12).
9. The existing GPC6-REQ-075(b) election can be imported without
   repeating the human decision (§14).
10. Later governed phases can reference a CHGR deterministically by ID +
    integrity digest (§6, §21).
11. Authority and enforcement remain conceptually and operationally
    separate from recording (§9, §17).
12. Runtime remains Observed / observe / unavailable, unchanged by this
    architecture or by any future implementation of it until a separate,
    explicit runtime-activation phase says otherwise.

---

## 23. Non-Goals

Explicitly excluded from this phase:

- Executable schema freeze (deferred to 143B).
- Production implementation of any kind.
- CLI implementation (§13 is conceptual only).
- Cryptographic signing implementation (§10 describes levels, implements
  none).
- Identity-provider integration.
- Runtime enforcement (§17 describes a future relationship, implements
  none).
- Authority-resolver changes.
- Lifecycle-transition automation.
- Migration of the existing GPC6-REQ-075(b) election (§14 designs the
  migration only).
- GLP-PILOT-C6 Stage 3 entry.
- Pilot authorization.
- Pilot execution.

---

## 24. Future Phase Roadmap

The likely governed sequence after this architecture, **named for planning
purposes only — none of the following is authorized or pre-approved by
naming it here**:

- **143B** — Canonical Human Governance Record Contract Freeze (convert
  this architecture into a numbered, falsifiable contract, mirroring how
  142A converted 139F into GPC6-001).
- **143C** — Contract Independent Verification (mirrors 142B/142E/142H's
  role-separated re-derivation discipline).
- **143D** — Implementation Planning.
- **143E** — Canonical Record and Interactive CLI Implementation.
- **143F** — Implementation Independent Verification.
- Later runtime-consumption and enforcement phases only after separate
  architecture and separate, explicit authorization (§17.2).

Each of these remains subject to independent scoping, contract freeze, and
verification at the time it is actually undertaken; this roadmap is
advisory, not binding (GAC-REQ-023's no-phase-recommendation-binds-the-
next-phase principle, restated here for this new track).

---

## Required Adversarial Analysis

| # | Scenario | Mitigation |
|---|---|---|
| A1 | AI selects "Proceed" for the human | §3.4 forbids the system from choosing; §16.2 forbids any state transition without explicit human selection; INV-2 |
| A2 | An option is preselected | §4.3 forbids templates from embedding a default; §3.2 step 3 explicit; INV-3 |
| A3 | Pressing Enter accepts a dangerous default | §16.2: there is no default to accept — the confirm command (§13.1) requires displaying exact content and an explicit, non-defaultable input; no bare-Enter path reaches `confirmed` |
| A4 | No response is treated as approval | §16.2, INV-3: silence never causes a state transition |
| A5 | An AI-written rationale changes the human choice | §3.3: rationale is a distinct content class, human-authored only; the selection field is separate from and unaffected by rationale text |
| A6 | A Markdown file is treated as authoritative solely because it exists | §9.2: existence never establishes authority; this is the precise failure mode §9 as a whole is designed to prevent, and is exactly why the existing election record, while faithful, is not itself treated as "the architecture" (§0) |
| A7 | A phase report is mistaken for a human decision | §15's table; phase reports have no decision-maker-confirmation field and no state model overlap with §8 |
| A8 | A human decision is mistaken for a completed phase | §15: a CHGR has no phase ID, is never written by `pcae phase complete`, and never appears in `.pcae/phase-completion-*` |
| A9 | A published decision is edited in place | §11.1 immutability + §7.3 integrity digest makes this both prohibited and detectable |
| A10 | An expired or revoked record is replayed | §17.1's verification sequence explicitly checks state and expiry before any reliance; §8's `revoked` is terminal |
| A11 | A legacy import claims stronger assurance than existed | §14.2's explicit L0 marking rule; §10.2's no-overclaiming rule |
| A12 | An imported record changes the original wording | §14.2's verbatim-preservation and field-by-field-extraction requirements |
| A13 | Record custody creates authority | §7.3/§9.2: custody (git, filesystem) is storage, not a §9.3 authority component |
| A14 | A record authorizes action outside its scope | §9.3's scope-bound authority definition; §17.1's action-to-authority matching step; T9 in §18 |
| A15 | An agent creates and confirms its own authority record | §17.3's explicit self-authorization prohibition; §10's confirmation act is defined as a human act — an agent has no path to satisfy it; §9.3 requires eligibility under the *applicable governing authority model*, which never names an AI system as an eligible Human Authority |
| A16 | Runtime executes merely because a record ID was supplied | §17.2: no runtime code path exists yet; even in the future-described relationship of §17.1, a record ID alone satisfies only the first of six required checks, all of which must pass, and even full verification triggers a *permission check*, never execution itself (INV-13) |

---

## Validation Requirements

| Requirement | Demonstration |
|---|---|
| The current election remains unchanged | `git status --short` shows no modification to `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`; this phase's allowed-files list (task contract) does not include it |
| No repeated election is required | §14 designs import as a read-and-wrap operation with no new-selection step (§14.3) |
| No phase-report metadata is modified by the architecture | `.pcae/phase-completion-metadata.json` and `-report.md` are updated only with this phase's own 143A completion content, never with GPC6-REQ-075(b) content; §15 defines the permanent boundary |
| No governance contract is modified | No file under `docs/contracts/` is touched by this phase (verified below) |
| All human substantive decisions remain human | §2 (INV-1–INV-4), §3.3, §3.4 |
| Interactive bounded choice is the default design | §3, §4 |
| Free-form rationale is optional unless a governing contract requires it | §3.2 step 5–6, §4.2 |
| No dangerous default is allowed | §4.3, A2, A3 |
| No automatic confirmation is possible | §10, §13.2, A3, A4 |
| Canonical identity does not itself create authority | §6.3, §9.2, A6 |
| Provenance does not itself create authority | §12.2 |
| Legacy import preserves original assurance honestly | §10.3, §14.2 |
| Runtime remains unchanged | Confirmed via `pcae runtime inspect` below |
| No implementation or execution capability is introduced | No file under `src/pcae/` is touched by this phase (verified below) |

---

## Phase-Level Validation Evidence

- `git status --short` at phase start: clean (confirmed prior to any edit
  in this phase; only this phase's own new task-contract and idle-task
  closure files were pending, per the task-transition workflow used to
  begin this phase).
- `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`: not modified by this
  phase (not in this phase's allowed-files list; confirmed unchanged).
- `docs/contracts/**`: no file modified by this phase.
- `src/pcae/**`: no file modified by this phase — this is a documentation-
  only architecture phase.
- `pcae runtime inspect`: Runtime state Observed, Execution capability
  unavailable, Maximum plugin capability observe — unchanged before and
  after this phase.
- `pcae check`: passed against the active task's allowed-files/allowed-
  zones scope (`docs`, `tasks`, `config`).
- Full `fast_green` test tier: not affected by this phase (no source
  change), re-run for regression confirmation as part of phase close.

---

## Expected Outcome

This document is the approved architecture for **Canonical Human
Governance Records**. It makes human governance decisions interactive,
bounded, explicit, canonical, immutable after publication, provenance-
complete, independently verifiable, referenceable by later governed
activity, structurally distinct from PCAE phase reports, and incapable of
being authored or confirmed by an AI agent.

This document does not itself create any of the above — it is a design
for a future contract-freeze phase to convert into falsifiable
obligations, per §24.

**Recommended next phase: 143B — Canonical Human Governance Record
Contract Freeze.** This recommendation does not authorize 143B, does not
freeze any schema, and does not itself constitute governance approval of
anything described in this document (GAC-REQ-023).
