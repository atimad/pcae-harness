# Phase 141D — Advisory Governance Operations Handbook

**Status:** Complete (operational guidance document only — no governance,
lifecycle, runtime, or authority changes)
**Mode:** Operations handbook translating AGOC-001 v1.0's normative
obligations into day-to-day operator guidance for the certified Advisory
Governance Framework (GLP-001 v1.0, GAC-001 v1.0, PGP-001 v1.1, PPA-001
v1.0)
**Governing authority:** AGOC-001, GLP-001, GAC-001, PGP-001, PPA-001
(normative — this document restates none of their obligations as a
parallel authority); Phase 141C (independent verification of AGOC-001,
context only); Phase 141B, Phase 141A, Phase 140B (context only, not
trusted as authority for any specific wording below)
**Runtime:** Observed / observe / unavailable (unchanged by this phase)

## 0. Purpose and Boundary

This document is the practitioner-facing operations handbook for day-to-day
use of the certified and independently verified Advisory Governance
Framework. It explains **how** a participant applies AGOC-001, GLP-001,
GAC-001, PGP-001, and PPA-001 during normal PCAE operation. It creates,
modifies, or interprets no governance authority beyond what those five
contracts already establish (AGOC-REQ-002, AGOC-REQ-005, AGOC-REQ-006).
Every requirement cited below was independently re-derived by direct re-read
of `docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md` (808 lines,
AGOC-001 v1.0) and, where AGOC-001 itself cites a base contract, cross-
checked against that base contract's own text
(`docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
`docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`,
`docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
`docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md`) and against Phase
141C's independent verification of AGOC-001
(`docs/PHASE_141C_ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT_INDEPENDENT_VERIFICATION.md`).
This is an operational-guidance phase only: no architecture is redesigned,
no governance/lifecycle/runtime/authority behavior is modified, no
implementation is performed, and `GLP-PILOT-C6` is not advanced beyond
Stage 1 of 4.

This handbook is **subordinate to every authoritative governance contract**
it describes. Where any sentence below appears to conflict with AGOC-001,
GLP-001, GAC-001, PGP-001, or PPA-001, the contract governs and the
handbook sentence is a defect in this document, correctable through §11
below — never the reverse.

---

## 1. Purpose

### 1.1 Handbook purpose

This handbook exists to answer one practical question for a working PCAE
participant: *given the certified Advisory Governance Framework, what do I
actually do?* AGOC-001 freezes **obligations** (what SHALL, SHALL NOT, or
MAY happen); this handbook translates those obligations into an
operator-usable sequence of actions, without adding to or subtracting from
what AGOC-001 already requires (AGOC-REQ-002).

### 1.2 Intended audience

Any human authority or agent acting under human authority who performs an
"operational act" as AGOC-001 defines it — citing GLP-001 advisorily,
proposing or evaluating a pilot candidate under PPA-001, collecting or
assessing evidence under PGP-001, or acting under GAC-001's adoption-stage
model (AGOC-001 Contract identity and status, "operational act"
definition). Concretely, this includes every role named in §3 below and any
future reader auditing a past operational act's compliance (AGOC-REQ-004).

### 1.3 Relationship to authoritative governance contracts

This handbook is strictly **informative**. It:

- Restates no AGOC-001/GLP-001/GAC-001/PGP-001/PPA-001 requirement as a
  parallel or competing authority (AGOC-REQ-002, mirrored here for this
  handbook's own text).
- Introduces no new obligation, invariant, boundary, role, or evidence
  category beyond what those five contracts already define.
- Cites the exact contract section behind every piece of guidance it gives,
  so a reader can verify the guidance against the source directly rather
  than trusting this document's paraphrase.

### 1.4 Handbook limitations

- This handbook is not itself a governance contract; it cannot be violated
  in the sense a contract requirement can be violated, only followed more
  or less faithfully.
- This handbook does not resolve any of the non-blocking findings Phase
  141C recorded against AGOC-001 (§10 below); those remain open evidence
  for a future AGOC-001 revision, not something this document silently
  patches over.
- This handbook does not, and cannot, expand any role's authority, change
  runtime capability, or advance `GLP-PILOT-C6` beyond Stage 1 of 4.
- **This handbook is informative rather than authoritative.** Every
  procedural recommendation below is a recommendation, not a binding
  obligation, unless it directly restates a SHALL/SHALL NOT/MUST/MUST NOT
  requirement already present in AGOC-001 or a base contract — in which
  case the obligation's binding force comes from that contract, not from
  this handbook.

---

## 2. Operational Overview

### 2.1 Advisory Governance lifecycle (as it exists today)

The framework currently occupies **GAC-001 §5 Stage 3 — Advisory use**
(AGOC-001 Contract identity and status; independently reconfirmed by Phase
141A §0 and unchanged through 141B/141C). Advisory use is a legitimate,
indefinite steady state, not a waiting room for pilot progression
(AGOC-REQ-021). The full possible escalation path, for reference, is:

```
advisory citation → proposed pilot (PPA-001 §4)
  → eligibility & authorization review (PPA-001 §5–§7)
  → designation (GAC-001 §6)
  → the pilot's own GLP-001 lifecycle (Architecture → Contract Freeze →
    Implementation → Independent Verification, plus conditional stages)
  → independent assessment (GAC-001 §8)
  → a Stage 6 governance decision (GAC-001 §9)
```

(AGOC-REQ-024). No step in this chain is skippable, and no step may be
initiated by anything other than an explicit human-authority election at
each transition (AGOC-REQ-024, citing GLP-REQ-003, GAC-REQ-023,
PPA-REQ-020). `GLP-PILOT-C6` currently sits at GLP-001 §6.1 Stage 1 of 4 —
this is an external operational fact this handbook does not re-derive or
advance (AGOC-REQ-027 item 5).

### 2.2 Where operational governance fits within PCAE

AGOC-001 governs **how** the four already-frozen contracts are used
operationally day to day: invocation conditions, evidence obligations,
improvement-initiation rules, role responsibilities, operational
boundaries, compliance obligations, and compatibility guarantees (AGOC-001
Contract identity and status). It does not govern the substantive content
those four contracts already freeze — lifecycle sequencing (GLP-001),
adoption staging (GAC-001), evidence-protocol mechanics (PGP-001), or
proposal/authorization mechanics (PPA-001) remain each contract's exclusive
domain (AGOC-REQ-002). This handbook sits one further layer out: it governs
nothing itself, and only explains AGOC-001's already-frozen operational
layer in operator-usable form.

### 2.3 Interaction with existing lifecycle governance

Every operational act integrates into PCAE's existing phase-report/
lifecycle discipline exactly as already required — no new phase type,
lifecycle stage, or parallel reporting mechanism is added anywhere in this
framework (AGOC-REQ-026, citing GAC-REQ-052/GAC-REQ-054/GAC-REQ-006). A
phase citing GLP-001 advisorily still produces an ordinary PFR-001-
conformant phase report; nothing about that report's format changes because
GLP-001 was cited.

### 2.4 Expected operational flow

For the common case (advisory citation, the zero-ceremony default under
Stage 3):

1. A human authority or delegated agent, in the ordinary course of
   scoping a multi-phase initiative, judges whether GLP-001 is a useful
   structuring lens (AGOC-REQ-021).
2. The citing phase names, in its own governing-authority or method
   section, the specific GLP-001 §5.1/§5.2 criterion consulted — this
   handbook's own recommendation, not a GAC-001-imposed documentation
   artifact (AGOC-REQ-022, as corrected by Phase 141C Finding 1; see §10
   below).
3. The citation is recorded exactly as any other prior-phase or contract
   citation would be documented — no special template (AGOC-REQ-026).
4. Nothing further happens unless a human authority separately elects to
   propose a pilot candidate (§4 below).

For the escalated case (a pilot candidate is proposed), the flow instead
follows PPA-001's own multi-step sequence, described operationally in §4
below.

---

## 3. Roles and Responsibilities

This section gives practical operational guidance for each role AGOC-001
§3 names. It redefines no authority: every responsibility below already has
exactly one owning role under AGOC-001 (AGOC-REQ-018), and this handbook
changes none of those assignments.

### 3.1 Human Sponsor

- **Responsibility:** Names and accepts a specific initiative as a pilot
  candidate; accepts the disclosed ceremony cost as a deliberate tradeoff
  before any proposal proceeds to review (PPA-001 §5.2 item 4; PGP-001
  §4.1; AGOC-001 §3).
- **Expected input:** A concrete initiative that plausibly meets GLP-001
  §5.1's applicability criteria and does not fall under §5.2's exclusions.
- **Expected output:** An explicit, attributable statement of sponsorship
  — not silence, not inferred authorship (PPA-REQ-017's standard,
  independently reconfirmed by Phase 139C.1/139D's practice).
- **Coordination:** Sponsorship is a precondition for the Advisory
  Evaluator's proposal review (§3.2); it does not itself constitute review
  or authorization.

### 3.2 Advisory Evaluator

- **Responsibility:** Applies PPA-001 §5–§6 (eligibility fast check,
  mandatory review questions, Authorization Review sequence) to a specific
  pilot proposal, as a party distinct from the proposer (PPA-REQ-008,
  PPA-REQ-018–020). Separately, during ordinary advisory use, this is the
  role that judges whether a specific GLP-001 §5.1/§5.2 criterion genuinely
  applies before citing it — an act GAC-REQ-012 assigns to whoever performs
  the citation itself, not a separate reviewer distinct from the citing
  party (a distinction Phase 141C's Finding 3 flagged as imprecisely
  cited in AGOC-001's own table; operators should read these as two
  related but textually distinct duties, sourced to PPA-001 §5–§6 for the
  first and GAC-001 §5 for the second, not to one shared citation).
- **Expected input:** A complete PPA-001 §4 proposal package (all nine
  required components) for the formal-review duty; the citing phase's own
  draft governing-authority text for the advisory-use duty.
- **Expected output:** One of PPA-001 §7.1's outcomes (Authorize planning /
  Defer / Reject / Request additional evidence / Suspend consideration)
  for a formal proposal; a documented judgment (not a formal artifact) for
  ordinary advisory citation.
- **Coordination:** Must not be the same party as the proposal's Human
  Sponsor or its Implementation Owner (PPA-REQ-038–039).

### 3.3 Governance Maintainer

- **Responsibility:** Authors any future contract-text revision under
  GLP-001 §13 or the equivalent extensibility sections of GAC-001/PGP-001/
  PPA-001/AGOC-001 (AGOC-001 §11), invoked only when a future
  evidence-gated improvement (§6 below) is actually proposed.
- **Expected input:** A qualifying improvement trigger meeting AGOC-REQ-038
  through AGOC-REQ-041 — cited evidence of a real operational gap, not
  speculation or preference (AGOC-REQ-039).
- **Expected output:** Either a fresh Architecture-stage document (GLP-001
  §6.1 Stage 1) for a genuine architectural question, or a dedicated
  contract-repair phase for a citation/wording-only fix (the same graded
  exception PGP-001's own v1.0→v1.1 self-repair used, and the one Phase
  141C itself invoked for AGOC-REQ-022).
- **Coordination:** Does not act absent a qualifying trigger; a Governance
  Maintainer acting without cited evidence is itself a non-compliant
  operational act (AGOC-REQ-037, AGOC-REQ-042).

### 3.4 Independent Verifier

- **Responsibility:** Performs Scope A (subsystem verification) and, where
  separately commissioned, Scope B (governance execution) checking
  (GLP-REQ-029–034); performs the Stage 5 Independent Assessment of GAC-001
  §8, explicitly barred from being any of the pilot's own participants
  (GAC-REQ-035).
- **Expected input:** A completed pilot stage's evidence, or a frozen
  contract revision awaiting independent re-verification.
- **Expected output:** A verification report using the re-derive/
  do-not-trust discipline this framework's own history has repeatedly
  demonstrated (Phases 138C.2, 139D, 140A, 141C) — independently re-reading
  the underlying source before comparing it against the document under
  verification, not trusting that document's own narrative.
- **Coordination:** Distinct from Future Reviewers (§3.6) in practice, but
  AGOC-001's own text leaves the exact temporal boundary between the two
  roles ambiguous (Phase 141C Finding 2, non-blocking) — operators
  encountering genuine confusion about which row applies should treat that
  confusion as the qualifying evidence AGOC-REQ-019 anticipates for a
  future clarifying revision, not as license to informally merge the two
  roles.

### 3.5 Implementation Owner

- **Responsibility:** Satisfies a frozen contract's obligations for a
  specific stage of a specific designated pilot's own lifecycle; is not
  itself evidence of correctness, only of an attempt (GLP-001 §8).
- **Expected input:** A designated pilot's frozen Contract-Freeze-stage
  requirements for the stage being implemented.
- **Expected output:** Implementation artifacts plus the ordinary evidence
  a completed stage produces under PGP-001 §8.2's categories.
- **Coordination:** Remains the sole owner of implementation content; no
  operational act under AGOC-001 transfers that ownership to any
  governance role (AGOC-REQ-013, AGOC-REQ-046).

### 3.6 Future Reviewers

- **Responsibility:** Conducts any later Independent Verification,
  Certification, or Stage 5 Independent Assessment pass against evidence
  accumulated under AGOC-001's operational period.
- **Expected input:** The full accumulated evidentiary record for the
  scope under review (advisory citations, pilot stage evidence, prior
  verification reports).
- **Expected output:** A fresh, independently re-derived judgment — bound
  by the same re-derive/do-not-trust discipline already proven across this
  framework's own history, not a restatement of a prior reviewer's
  conclusion.
- **Coordination:** See §3.4's note on the unresolved role-table overlap
  with Independent Verifier — the same non-blocking ambiguity applies here.

### 3.7 Human Authority (context, not a redefinition)

AGOC-001's role table also names **Human Authority** as the sole authority
for every election no other role may make: GLP designation, stage-to-stage
progression, authorization decisions, and any GAC-001 §9 Stage 6 governance
decision (AGOC-001 §3; GLP-001 §8; PPA-001 §7.1; GAC-001 §9). No automated
mechanism, heuristic, or default may substitute for this role
(GAC-REQ-023). This handbook records this role for operator context only;
it neither reassigns nor narrows this authority in any way.

### 3.8 Non-overlap and no new role

Every responsibility above has exactly one owning role (AGOC-REQ-018); this
handbook introduces no new role beyond those AGOC-001 §3 already names, and
no new compliance-checking role, tool, or apparatus (AGOC-REQ-020,
AGOC-REQ-050). A future phase encountering genuine ambiguity about which
role owns a specific action has identified evidence admissible as a §6-
qualifying improvement trigger (AGOC-REQ-019) — this handbook resolves no
such ambiguity on its own authority.

---

## 4. Normal Operational Workflow

This section documents the standard sequence for both the zero-ceremony
advisory case and the escalated pilot case, remaining contract-neutral
(describing what already happens under the contracts, not adding new
steps).

### 4.1 Preparation

- Confirm which stage the framework currently occupies (Stage 3 — Advisory
  use, as of this handbook's writing) via `docs/contracts/
  GOVERNANCE_ADOPTION_CONTRACT.md` §5 or a fresh `pcae session bootstrap`.
- Confirm `GLP-PILOT-C6`'s current stage independently rather than
  assuming it has advanced (AGOC-REQ-027 item 5).
- For a pilot candidate specifically: apply PGP-001 §4.2's excluded-class
  fast check before §4.1's suitability checklist (PPA-REQ-014 ordering) —
  eliminate localized-fix/isolated-repair candidates and already-mid-flight
  work before spending review effort on them.

### 4.2 Invocation

- **Advisory citation:** available at any time, for any initiative, at
  zero ceremony, on a human authority's or delegated agent's own judgment
  (AGOC-REQ-021). Name the specific GLP-001 §5.1/§5.2 criterion consulted
  in the citing phase's own governing-authority or method section
  (AGOC-REQ-022, this handbook's own recommendation).
- **Pilot proposal:** progression from advisory citation to pilot
  designation is available only through PPA-001's full proposal (§4, nine
  required components), eligibility review (§5), and Authorization Review
  sequence (§6, five ordered steps) — no step is skippable and no step
  yields automatic approval from a favorable prior step (AGOC-REQ-023).

### 4.3 Evidence collection

- For a designated pilot, collect only PGP-001 §8.2's seven evidence
  categories: architectural, contract, verification, governance
  observations, participant observations, metrics, lessons learned
  (AGOC-REQ-028).
- For advisory use, the acceptable evidence is narrower: citation records
  meeting AGOC-REQ-022, and, where disclosed, whether the citation changed
  a sequencing decision (AGOC-REQ-028).
- Every evidence item states its provenance and cites a specific, checkable
  source — file path, phase ID, or requirement ID (AGOC-REQ-029). An
  unattributed narrative claim is not admissible evidence.
- Tag every item objective, subjective, or hypothesis per PGP-001 §7.2
  (AGOC-REQ-033).

### 4.4 Review

- Compare only against PGP-001 §8.4's four named baselines: the historical
  PCAE corpus, concurrent non-cited initiatives (where any exist), the
  pre-GLP-001 repair/incident corpus, and historical Independent
  Verification defect/verdict trends (AGOC-REQ-030).
- Report every comparison's result as found, including a null or
  unfavorable result — reporting only favorable comparisons is
  non-compliant evidence (AGOC-REQ-031).
- Ensure any Independent Assessment or Authorization Review discloses any
  of PGP-001 §11's six bias classes not affirmatively ruled out
  (confirmation, novelty, author, reviewer, survivorship, selective
  evidence) and any of PPA-001 §8's five pre-authorization risk categories
  (governance, operational, evidence, bias, scope) (AGOC-REQ-067).

### 4.5 Recommendations

- Distinguish an observation (what the evidence shows) from a
  recommendation (what a reviewer suggests doing about it) — see §5 below.
- A recommendation for governance-text evolution must meet §6's
  improvement-contract discipline before proceeding past initial review
  (AGOC-REQ-037, AGOC-REQ-038–041).
- No recommendation, however evidenced, authorizes anything by itself — a
  human-authority election is always required (AGOC-REQ-042).

### 4.6 Closure

- An operational act terminates, without escalating further, at any of:
  advisory citation concluding with no proposal filed (the default
  terminus, no consequence); a PPA-001 §7 Reject/Defer/Suspend outcome; a
  GAC-001 §10/PPA-001 §10 rollback/suspension/withdrawal/cancellation
  (documented trigger, evidence preserved); or a GAC-001 §9 Stage 6
  "Reject" or "Continue advisory use" outcome — both legitimate terminal
  states, not defects requiring further escalation (AGOC-REQ-025).

### 4.7 Documentation

- Record any compliance-relevant operational act in a PFR-001-conformant
  phase report or equivalent governed document — no adoption-specific
  template is introduced beyond what GAC-001 §5–§9 already require
  (AGOC-REQ-052).
- Record every citation, proposal, evidence item, or decision in a
  location and form a future reader can locate and inspect directly, never
  only from memory or an informal channel (AGOC-REQ-069).

---

## 5. Operational Decision Guidance

### 5.1 Evaluating evidence

Apply §4.3–4.4's evidence and comparison discipline before treating any
claim as established. An operator should be able to answer, for any cited
evidence item: what is its provenance, what category does it belong to
(PGP-001 §8.2 or, for advisory use, AGOC-REQ-028's narrower set), and is it
independently checkable without relying on the submitting party's own
restatement (AGOC-REQ-034).

### 5.2 Distinguishing observations from recommendations

An **observation** states what the evidence shows (e.g., "this citation
reduced a duplicated sequencing decision," AGOC-REQ-035). A
**recommendation** proposes an action in response (e.g., "propose a §6
improvement to clarify AGOC-001 §3's role-table overlap"). Conflating the
two — treating an observation as if it already carries the weight of an
authorized recommendation, or a recommendation as if it were itself
established fact — is the single most common operational-decision error
this handbook anticipates. Keep them in separate, separately labeled
statements in every phase report or review record.

### 5.3 Identifying insufficient evidence

Evidence is insufficient when it lacks provenance (AGOC-REQ-029), is not
independently checkable (AGOC-REQ-034), falls outside PGP-001 §8.2's seven
categories or AGOC-REQ-028's advisory-use subset, or compares against a
baseline other than PGP-001 §8.4's four named ones (AGOC-REQ-030). Absence
of evidence is itself evidence for retaining the current design, not a
gap to be filled by inference or narrative confidence (AGOC-REQ-037).

### 5.4 Deferring decisions

Where evidence is insufficient, the correct operational act is to defer —
PPA-001 §7.1 names "Request additional evidence" and "Suspend
consideration" as legitimate, non-penalizing outcomes, not failures
(AGOC-REQ-025 item (b)). A Governance Maintainer or Advisory Evaluator
facing genuine ambiguity should record that ambiguity as candidate §6
evidence (AGOC-REQ-019, AGOC-REQ-057) rather than resolve it informally.

### 5.5 Documenting conclusions

Every conclusion — observation, recommendation, or deferral — should name
the specific evidence it rests on and the specific contract provision it
was evaluated against, so a future Independent Verifier or auditor can
reconstruct the reasoning without relying on the acting party's own
narrative alone (AGOC-REQ-016).

---

## 6. Operational Scenarios

The following examples are **illustrative only** — non-normative
walkthroughs of how §4–§5's guidance applies. None of them is itself a
governance decision, and none should be cited as precedent in place of the
underlying contract text.

### 6.1 Normal operation (advisory citation)

A phase's Architecture stage names GLP-001 as a useful lens for a
five-phase initiative, cites GLP-001 §5.1 criterion 2 ("touches
cross-cutting or global concerns") in its own governing-authority section,
and proceeds. No proposal is filed; no further escalation occurs. This is
the default terminus (§4.6) and requires no special handling.

### 6.2 Incomplete evidence

A proposed pilot's evidence plan cites only favorable comparisons against
one baseline, omitting the other three PGP-001 §8.4 baselines and any
unfavorable result. The correct operational response is not to accept the
proposal as-is, but for the Advisory Evaluator to identify the gap under
§5.3 above and request additional evidence (PPA-001 §7.1) before
proceeding.

### 6.3 Conflicting observations

Two participant observations about the same pilot stage disagree (one
reports the stage reduced ceremony, another reports it added it). Per
§5.2, both are recorded as distinct, tagged observations (objective/
subjective/hypothesis per PGP-001 §7.2); the disagreement itself is not
resolved by this handbook or by informal averaging — it is recorded as-is
for the Independent Assessor to weigh under GAC-001 §8.

### 6.4 Governance uncertainty

A future reader is unsure whether the "Advisory Evaluator" or "Independent
Verifier" row in AGOC-001 §3 owns a specific action. Per §3.4/§3.6 above,
this uncertainty is itself the qualifying evidence AGOC-REQ-019
anticipates — the reader records it as a candidate future §6 trigger
(Phase 141C Finding 2) rather than picking one interpretation and treating
it as settled.

### 6.5 Future improvement proposals

An operator notices, across three separate advisory citations, that the
same GLP-001 §5.1 criterion is consistently miscited in the same way. This
is a recurring-defect-class trigger meeting AGOC-REQ-038's acceptable-
improvement standard; the operator drafts a proposal citing the three
specific phases, per AGOC-REQ-040, for a future Governance Maintainer to
carry forward — this handbook itself does not carry it forward.

### 6.6 Escalation

A pilot candidate's Human Sponsor and proposed Implementation Owner turn
out to be the same person. Per AGOC-REQ-065/066 and PPA-REQ-038–041, this
is a disqualifying conflict, not a waivable convenience — the Advisory
Evaluator escalates to Human Authority for resolution (a different
Implementation Owner, or the proposal does not proceed) rather than
granting an informal exception.

---

## 7. Recordkeeping Guidance

### 7.1 Documentation

Every compliance-relevant operational act is recorded in a PFR-001-
conformant phase report or equivalent governed document (AGOC-REQ-052).
No adoption-specific template exists beyond what GAC-001 §5–§9 already
require — do not invent one.

### 7.2 Evidence preservation

No new retention mechanism exists or is needed: evidence persists under
existing PCAE version control and phase-report conventions (AGOC-REQ-032).
Evidence is preserved even after a rollback, suspension, or withdrawal —
never deleted as part of closing out a terminated pilot (AGOC-REQ-032,
citing GAC-REQ-048/PPA-REQ-036).

### 7.3 Traceability

Every evidence item names the specific pilot stage, advisory citation,
phase report, or artifact it is drawn from, tagged per PGP-001 §7.2
(AGOC-REQ-033, AGOC-REQ-034). Note that AGOC-001 itself has no dedicated
Traceability Matrix section comparable to the other four contracts' own
(GLP-001 §16, GAC-001 §20, PGP-001 §15, PPA-001 §13) — a structural gap
Phase 141C flagged as non-blocking (Finding 5). Operators should not expect
one; inline citation, as AGOC-001 itself uses, is the current pattern.

### 7.4 Review records

Any operational act that escalates beyond advisory citation undergoes the
specific review the corresponding contract already requires (PPA-001
§5–§7; GLP-001 §10; GAC-001 §8) — record that review's outcome using the
existing mechanism, not a new one (AGOC-REQ-054).

### 7.5 Audit preparation

Every operational act should remain independently auditable without
reliance on the acting party's own summary (AGOC-REQ-068). Before treating
any operational record as audit-ready, confirm it independently states
what evidence was cited, which contract provision it was evaluated
against, and what outcome resulted (AGOC-REQ-016).

---

## 8. Frequently Encountered Situations

None of the guidance below introduces a new governance rule; each restates
how the existing contracts already handle the situation.

- **Uncertainty about applicability.** GLP-001 §5.1/§5.2 criteria are
  judged by whoever performs the citation (GAC-REQ-012); genuine
  uncertainty is resolved by declining to cite, not by citing
  speculatively (AGOC-REQ-039 item 1's prohibition on speculative
  anticipation extends by analogy here).
- **Disagreement between reviewers.** Record both positions with their
  respective evidence (§5.2, §6.3); do not average or silently pick one —
  unresolved disagreement is itself admissible §6 evidence (AGOC-REQ-057).
- **Incomplete reviews.** Use PPA-001 §7.1's "Request additional evidence"
  or "Suspend consideration" outcomes; an incomplete review is not a
  license to proceed with a partial one (§5.4).
- **Repeated findings.** A finding that recurs across multiple advisory
  citations or pilot stages is exactly the kind of evidence AGOC-REQ-038
  treats as an acceptable improvement trigger — log it, do not
  individually re-litigate it each time it recurs.
- **Operational delays.** No fixed calendar cadence governs review;
  review is event-driven (AGOC-REQ-036) — a delay before the next
  triggering event (a completed pilot stage, a surfaced improvement
  trigger, a commissioned Independent Assessment) is not itself a defect.
- **Clarification requests.** Where this handbook's own text is unclear,
  treat the source contract as authoritative (§0 above) and, if the
  contract itself is genuinely ambiguous, apply AGOC-REQ-057's
  interpretation rule: the reading imposing the narrower operational
  obligation and preserving the greater number of existing invariants and
  boundaries governs, pending a future contract repair.

---

## 9. Operational Risks

Each risk below is restated from AGOC-001's own invariants/boundaries with
an operator-focused mitigation; none is a new governance rule.

| Risk | Description | Mitigation |
|---|---|---|
| **Governance drift** | Silent reinterpretation of a contract provision during an unrelated phase, rather than through a governed revision. | Prohibited outright (AGOC-REQ-027 item 3, AGOC-REQ-039 item 5); any perceived need for reinterpretation is itself §6-qualifying evidence, not license to act informally. |
| **Overuse** | Treating advisory citation as if it created an ongoing obligation, or citing GLP-001 where it adds no value. | AGOC-REQ-027 item 2 explicitly rules out reading citation as an obligation to keep citing; cite only when GLP-001 is a genuinely useful lens (AGOC-REQ-021). |
| **Underuse** | Avoiding advisory citation even where GLP-001 §5.1 criteria clearly apply, out of unwarranted ceremony concern. | Advisory citation is zero-ceremony by design (AGOC-REQ-021); the ceremony concern applies to pilot designation, not citation. |
| **Insufficient evidence** | Proceeding past initial review on narrative assertion rather than cited, checkable evidence. | AGOC-REQ-008/AGOC-REQ-037 block any adoption-stage/pilot-status/contract-text change absent evidence meeting §5's standard; treat absence of evidence as evidence for the status quo. |
| **Role confusion** | Blurring an operational responsibility across two roles, especially the §3.4/§3.6 Independent Verifier / Future Reviewers overlap. | Treat any genuine ambiguity as admissible §6 evidence (AGOC-REQ-019), not as license to informally merge roles; the base contracts' own separation rules (e.g., GAC-REQ-035) still govern who may actually perform an assessment regardless of table wording. |
| **Recommendation bias** | An Independent Assessment or Authorization Review implicitly favoring a preferred outcome without disclosing the bias. | Disclose any of PGP-001 §11's six bias classes not affirmatively ruled out and any of PPA-001 §8's five risk categories, every time (AGOC-REQ-067). |

---

## 10. Relationship to Authoritative Contracts

| Domain | Governing contract | This handbook's role |
|---|---|---|
| Governance (candidate selection, evidence protocol) | PGP-001 v1.1 | Describes operator workflow only; PGP-001 owns every evidence-protocol requirement. |
| Lifecycle (phase sequencing within a designated initiative) | GLP-001 v1.0 | Describes when citation is useful; GLP-001 owns every sequencing/staging requirement. |
| Authority (adoption staging, designation, Stage 6 decisions) | GAC-001 v1.0 | Describes the escalation path operationally; GAC-001 owns every adoption-stage and authority requirement. |
| Operational adoption (pre-designation proposal/authorization) | PPA-001 v1.0 | Describes the proposal/review sequence operationally; PPA-001 owns every proposal/authorization requirement. |
| Operational contract (day-to-day use of all four above) | AGOC-001 v1.0 | This handbook's direct and immediate source; AGOC-001 owns every invocation/evidence/improvement/boundary/compliance/compatibility requirement this handbook describes. |

**Precedence.** Wherever this handbook's guidance differs in force from
AGOC-001, GLP-001, GAC-001, PGP-001, or PPA-001, the contract is
authoritative and controls (§0 above). A difference in force is itself a
defect in this handbook, correctable only through §11 below — never
grounds for treating the handbook as an alternative source of truth.
Phase 141C's five findings against AGOC-001 (one repaired citation defect,
four non-blocking observations — §3.2 above and its own §3.2) remain open
evidence for a **future AGOC-001 revision**; this handbook does not
resolve them and defers entirely to whatever AGOC-001 says today,
imprecision included.

---

## 11. Maintenance Guidance

### 11.1 Handbook maintenance

This handbook is maintained by whichever role is performing Governance
Maintainer duties (§3.3) at the time a maintenance need arises. It carries
no independent versioning authority beyond what AGOC-001 §9's compatibility
contract already models for the contracts it operationalizes.

### 11.2 Update process

An update to this handbook's text:

1. Is triggered by the same class of event that triggers an AGOC-001
   improvement under §6 above (AGOC-REQ-038) — a recurring
   operator-facing gap, not preference or elapsed time (AGOC-REQ-039).
2. Never precedes, and never substitutes for, a corresponding AGOC-001
   revision when the guidance gap traces to AGOC-001's own text (as
   opposed to this handbook's own presentation of that text).
3. Is itself recorded the same way any other governed documentation change
   is recorded — no new review mechanism is introduced for handbook
   maintenance specifically (mirrors AGOC-REQ-050's prohibition on a new
   compliance apparatus, applied here to this handbook's own maintenance).

### 11.3 Synchronization with future contract revisions

Any future revision to AGOC-001, GLP-001, GAC-001, PGP-001, or PPA-001
that changes an obligation this handbook describes makes the corresponding
handbook section stale. A stale handbook section is guidance debt, not a
governance defect — the contract remains authoritative and controlling
even while the handbook text has not yet caught up (§0 above). Any future
reader should treat a handbook/contract disagreement as decisive evidence
the handbook needs updating, and should follow the contract in the
meantime.

### 11.4 Retirement criteria

This handbook retires, for a given scope, only upon: (a) the corresponding
contract(s) it describes being withdrawn or superseded in that scope
(mirrors AGOC-REQ-075's own retirement conditions); or (b) a future
revision that explicitly states this handbook is withdrawn. A GAC-001 §9
"Continue advisory use" outcome is not a retirement condition for either
the framework or this handbook (AGOC-REQ-075).

### 11.5 Non-supersession statement

**Handbook revisions cannot supersede authoritative contracts.** No future
edit to this document, however extensive, can narrow, remove, or alter any
provision of AGOC-001, GLP-001, GAC-001, PGP-001, or PPA-001. Any apparent
handbook-driven change to governance obligations is invalid on its face
and must be reverted, not treated as a de facto contract amendment.

---

## Validation

Confirmed at this phase's own start and throughout drafting:

- **Independent derivation.** Every piece of guidance above was derived
  directly from re-reading `docs/contracts/
  ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md` (AGOC-001 v1.0, 808 lines)
  in full at this phase's start, cross-checked against the base four
  contracts' own text where AGOC-001 cites them, and against Phase 141C's
  independent verification findings — not copied from Phase 141A/141B/141C
  prose without re-derivation.
- **No governance authority introduced.** This handbook creates no new
  obligation, invariant, boundary, evidence category, or compliance
  mechanism; every citation above traces to an existing AGOC-001/GLP-001/
  GAC-001/PGP-001/PPA-001 requirement ID.
- **No lifecycle authority introduced.** No new phase type, lifecycle
  stage, or compliance outcome is added anywhere in this document.
- **No runtime authority introduced.** `pcae health` was reconfirmed at
  this phase's start and remains Observed / observe / unavailable; no
  file under `src/pcae/` is created, modified, or deleted by this phase.
- **No implementation requirements added.** This handbook describes
  existing operator workflow only; it assigns no new implementation
  responsibility to any role (§3.5 preserves the Implementation Owner's
  exclusive ownership unchanged).
- **Operational rather than normative.** Every section is phrased as
  guidance ("should," "the correct operational response is") rather than
  as a new SHALL/SHALL NOT obligation; every binding obligation cited is
  attributed to its actual source contract, never asserted as this
  handbook's own.
- **Illustrative examples.** §6's six scenarios are explicitly marked
  non-normative and are not citable as precedent in place of the
  underlying contract text.
- **Contract precedence explicitly preserved.** §0 and §10 both state,
  in binding terms for this document's own text, that any conflict
  between this handbook and an authoritative contract resolves in the
  contract's favor.
- `git status --short` at phase start showed only this phase's own task
  contract as a new file; no file under `docs/contracts/*.md` was
  modified by this phase.
- `pcae check` passed and `pcae health` reported the expected active-task
  state at phase start (confirmed before this document was written).
- `python -m pytest -m fast_green -n auto -q` was re-run at this phase's
  own closure step (see Compatibility below for the recorded result), per
  this repository's established practice of re-running (not assuming) the
  fast_green sentinel even for documentation-only phases.

## No-Go

Confirmed not done by this phase:

- No governance contract (AGOC-001, GLP-001, GAC-001, PGP-001, or PPA-001)
  was modified by this phase.
- No architecture was redesigned by this phase.
- No governance behavior was modified by this phase.
- No lifecycle behavior was modified by this phase.
- No runtime behavior was modified by this phase.
- No authority resolution was modified by this phase.
- No implementation was performed or modified by this phase.
- No execution capability was introduced by this phase.
- No new compliance-checking role, tool, or apparatus was introduced by
  this phase.
- `GLP-PILOT-C6` was not advanced beyond Stage 1 of 4 by this phase.
- No GAC-001 §9 Stage 6 governance decision was made or attempted by this
  phase.
- Production code (`src/pcae/**`) was not modified by this phase.

## Compatibility

- **AGOC-001/GLP-001/GAC-001/PGP-001/PPA-001:** unchanged; this phase
  modified none of their text. This handbook's guidance is subordinate to
  all five and is repairable independently of them (§11).
- **Phase 141C:** this handbook logs Findings 2–5 as still-open candidate
  §6 improvement triggers (§10 above); it does not resolve them and does
  not reopen 141C's own verdict.
- **Phase 141B/141A/140B:** not reopened; this phase treats each as
  context only, per its own governing instruction.
- **Repository governance:** this phase modified only files within its
  own task contract's allowed zones (`docs`, `tasks`, `config`); no
  `docs/contracts/*.md` file, and no `.pcae/**` policy configuration, is
  touched beyond the completion-metadata/report files this phase's own
  closure requires.

## Deliverables

- **This operations handbook** —
  `docs/PHASE_141D_ADVISORY_GOVERNANCE_OPERATIONS_HANDBOOK.md`.

## Recommended Next Phase

**141E — Advisory Governance Operational Observation Program.**

Purpose: define how operational evidence accumulates over time under this
handbook's §4.3/§7 guidance into a structured observation program —
without introducing a new compliance-checking apparatus (AGOC-REQ-050) or
performing any GAC-001 §9 Stage 6 decision. Should treat this handbook as
evidence of intended operator workflow, not as authority for any specific
program requirement, and should log Phase 141C's Findings 2–5 (§10 above)
as still-open candidate §6 improvement triggers rather than resolving them
informally.
